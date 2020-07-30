from math import ceil
import constants

def calculate_checksum(fragment):
    return sum(fragment) % 255

class StartingInfo:
    def __init__(self, fragment_amount: int, fragment_size: int, data_type: str, file_path=None):
        self.fragments_amount = fragment_amount
        self.fragment_size = fragment_size
        self.data_type = data_type
        self.file_path = file_path


class FragmentPacking():
    def __init__(self, header: StartingInfo, data: list):
        self.header = header
        self.data = data

    @property
    def data_size(self):
        return len(self.data) if self.data else 0 
    
    @property
    def fragment_amount(self):
        # return amount of all segment from the file
        if self.data:
            return ceil(self.header.fragment_size/self.data_size) 
        return 0
    
    def get_starting_header(self):
        #TODO: datatype, datapath checksum of datapath
        # Fragments amount + Fragment size + Checksum + Data Type
        return (self.fragment_amount, 
                    self.header.fragment_size, 
                    calculate_checksum(b'TODO'),
                    self.header.data_type.encode(constants.CODING_FORMAT))

    def _split_package_data(self, sub_array, segment_size, offset):
        """ Splits package to the even sized segments"""
        return [sub_array[i: i+segment_size] for i in range(0,len(sub_array), segment_size)]

    def split_data(self):
        """
        Splits the data into packages
        """
        package_size = self.header.fragment_size * constants.SEGMENTS_AMOUNT
        for offset in range(0, self.data_size, package_size):
            package_data = self.data[offset: offset + package_size]
            yield self._split_package_data(package_data, self.header.fragment_size, offset)

    def calculate_fragments_amount(self):
        return len(self.data)/self.header.fragment_size