from math import ceil
import constants as const
import struct
from libscrc import modbus
import os


def calculate_checksum(*args):
    # Filter None and empty lists
    new_args = list(filter(lambda x : x and type(x) is not list, args))
    string = b"".join(new_args)
    return modbus(string) # 16-bit CRC 


class Packaging():
    def __init__(self, data: bytes, header_info: tuple):
        # header_info : fragment_size, data_type, file_path=None
        self.header_info = header_info
        self.fragment_data_size = self.header_info[0]
        self.data_size = self._get_data_size(data)
        self.data = data
    
    #TODO: make for a file too
    def _get_data_size(self, data):
        if self.header_info[1] == b"F":
            return os.stat(self.header_info[2]).st_size
        return len(data) if data else 0
    
    @property
    def fragments_amount(self):
        # return amount of all fragment from the file
        return ceil(self.data_size/(self.fragment_data_size))
    
    def get_wrong_data_fragment(self, index, fragment_data):
        # generate incorrect data fragment for testing the NACK responses
        header = struct.pack(const.FRAGMENT_INDEX, index)
        header += struct.pack(const.CHECKSUM, 0)
        return header + fragment_data

    def get_data_fragment(self, index, fragment_data):
        header = struct.pack(const.FRAGMENT_INDEX, index)
        header += struct.pack(const.CHECKSUM, calculate_checksum(header, fragment_data))
        return header + fragment_data

    def get_starting_header(self, checksum):
        return struct.pack(const.STARTING_HEADER,
                self.fragments_amount,
                self.header_info[0],
                checksum,
                self.header_info[1]
            )

    def get_starting_fragment(self):
        # Fragments amount + Fragment size + Checksum + Data Type
        # for easier calculation of checksum
        check = struct.pack(const.STARTING_HEADER_WO_CHECKSUM,
                        self.fragments_amount,
                        self.header_info[0],
                        self.header_info[1]
                        )
        if self.header_info[1] == b'F': # if data type is a file
            checksum = calculate_checksum(check, self.header_info[2])
            header = self.get_starting_header(checksum)
            header += self.header_info[2]            
        else:
            # message is sent, so only checksum was added
            checksum = calculate_checksum(check)
            header = self.get_starting_header(checksum)
        return header
 
    def _yield_file(self):
        file = open(self.header_info[2], 'rb')
        while True:
            data = file.read(self.fragment_data_size)
            if not data:
                break
            yield data


    def _yield_text(self):
        for offset in range(0, self.data_size, self.fragment_data_size):
            yield self.data[offset:offset+self.fragment_data_size]


    def get_fragment_generator(self):
        if self.data:
            return self._yield_text()
        else:
            return self._yield_file() 

