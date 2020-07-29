import constants

class FragmentPacking():
    def __init__(self, data, data_type: str, fragment_size: int, file_name=None):
        self.data = data
        self.data_size = len(data)
        self.data_type = data_type
        self.file_name = file_name
        self.fragment_size = fragment_size

    def _split_package_data(self, sub_array, segment_size, offset):
        """ Splits package to the even sized segments"""
        return [sub_array[i: i+segment_size] for i in range(0,len(sub_array), segment_size)]

    def split_data(self):
        """
        Splits the data into packages
        """
        package_size = self.fragment_size * constants.SEGMENTS_AMOUNT
        for offset in range(0, self.data_size, package_size):
            package_data = self.data[offset: offset + package_size]
            yield self._split_package_data(package_data, self.fragment_size, offset)

    def calculate_fragments_amount(self):
        return len(self.data)/self.fragment_size