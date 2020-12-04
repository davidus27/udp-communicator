from math import ceil
import constants
import struct
from libscrc import modbus


def calculate_checksum(*args):
    # Filter None and empty lists
    new_args = list(filter(lambda x : x and type(x) is not list, args))
    string = b"".join(new_args)
    return modbus(string) # 16-bit CRC 


class Packaging():
    def __init__(self, data: bytes, header_info: tuple):
        # header_info : fragment_size, data_type.upper(), (file_path)
        self.header_info = header_info
        self.fragment_data_size = self.header_info[0]
        self.data_size = len(data) if data else 0
        self.data = data

    @property
    def fragments_amount(self):
        # return amount of all segment from the file
        if self.data:
            return ceil(self.data_size/(self.fragment_data_size))
        return 0
    
    def get_data_segment(self, index, fragment_data):
        header = struct.pack(constants.FRAGMENT_INDEX, index)
        header += struct.pack(constants.CHECKSUM, calculate_checksum(header, fragment_data))
        return header + fragment_data

    def get_starting_header(self, checksum):
        return struct.pack(constants.STARTING_HEADER,
                self.fragments_amount,
                self.header_info[0],
                checksum,
                self.header_info[1]
            )

    def get_starting_segment(self):
        # Fragments amount + Fragment size + Checksum + Data Type
        # for easier calculation of checksum
        check = struct.pack(constants.STARTING_HEADER_WO_CHECKSUM,
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
 
    def yield_segments(self):
        for offset in range(0, self.data_size, self.fragment_data_size):
            yield self.data[offset:offset+self.fragment_data_size]