from math import ceil
import constants
import ntpath
import struct


def calculate_checksum(*args):
    string = b"".join(args)
    return sum(string) % 255

def get_file_name(path):
    if path:
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)


class StartingFragment():
    def __init__(self, data: bytes, header_info: tuple):
        # header_info : fragment_size, data_type.upper(), (file_path)
        self.header_info = header_info
        self.data = data

    @property
    def fragment_data_size(self):
        """ How many bytes of data are in one fragment """
        return self.header_info[0] - constants.DATA_HEADER_SIZE

    @property
    def data_size(self):
        return len(self.data) if self.data else 0 
    
    @property
    def fragments_amount(self):
        # return amount of all segment from the file
        if self.data:
            return ceil(self.data_size/(self.fragment_data_size))
        return 0
    
    def get_segment(self, fragment_data, index):
        header = struct.pack("i", index)
        header += struct.pack("B", calculate_checksum(header, fragment_data))
        return header + fragment_data

    def get_starting_segment(self):
        header = struct.pack(constants.STARTING_HEADER, 
                                self.fragments_amount,
                                self.header_info[0],
                                self.header_info[1])                               
        try:
            file_path = get_file_name(self.header_info[2]) # add sliced file_path
        except:
            # no file path was found, so only header was added
            header += struct.pack('B', calculate_checksum(header))
        else:
            header += struct.pack('B', calculate_checksum(header, file_path))
            header += file_path
        finally:
            return header

    def _split_package_data(self, sub_array, segment_size, offset):
        """ Splits package to the even sized segments"""
        return [sub_array[i: i+segment_size] for i in range(0,len(sub_array), segment_size)]

    def split_data(self):
        """
        Splits the data into packages
        """
        package_data_size =  self.fragment_data_size * constants.SEGMENTS_AMOUNT
        for offset in range(0, self.data_size, package_data_size):
            package_data = self.data[offset: offset + package_data_size]
            yield self._split_package_data(package_data, self.fragment_data_size, offset)