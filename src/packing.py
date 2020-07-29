import struct

CODING_FORMAT = "utf-8"
SEGMENTS_AMOUNT = 10 # how many segments will be sent at once
ACK = b"OK"
NACK = b"ERROR"
KEEP_ALIVE = b"KA"
ENDING = b"END."

class FragmentPacking():
    # TODO: write down all these packing formats
    STARTING_HEADER = "bIhh" # Data Type + Fragments amount + Fragment size + Checksum
    TEXT_MESSAGE_HEADER = "xh" # Checksum
    DATA_HEADER = "ih"


    def __init__(self, data, data_type: str, fragment_size: int, file_name=None):
        self.data = data
        self.data_size = len(data)
        self.data_type = data_type
        self.file_name = file_name
        self.fragment_size = fragment_size

    def _get_chunk(self, sub_array, segment_size, offset):
        """ Splits package to the even sized segments"""
        return [sub_array[i: i+segment_size].encode(CODING_FORMAT) for i in range(0,len(sub_array), segment_size)]


    def split_data(self):
        """
        Splits the data into packages
        """
        segment_size = self.fragment_size - 6
        package_size = segment_size * SEGMENTS_AMOUNT

        #yield [struct.pack(self.TEXT_MESSAGE_HEADER, self.calculate_checksum())]
        
        for offset in range(0, self.data_size, package_size):
            sub_array = self.data[offset: offset + package_size]
            #yield self._get_chunk(sub_array, segment_size, offset) 
            yield self._get_chunk(sub_array, segment_size, offset)



    def calculate_checksum(self):
        return 10

    def calculate_fragments_amount(self):
        return len(self.data)/self.fragment_size