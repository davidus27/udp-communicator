from packing import calculate_checksum # TODO : remove this stupidity
import constants
import struct

class StartingSegment:
    def __init__(self, fragments_amount, fragment_size, checksum, data_type, file_path = None):
        self.data_type = data_type
        self.fragment_size = fragment_size
        self.fragments_amount = fragments_amount
        self.file_path = file_path
        self.checksum = checksum

    def has_valid_checksum(self) -> bool:
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        header_without_checksum = struct.pack(constants.STARTING_HEADER_WO_CHECKSUM, 
                        self.fragments_amount,
                        self.fragment_size,
                        self.data_type
                )
        #header[2] -> checksum
        return self.checksum == calculate_checksum(header_without_checksum, self.file_path)

class DataSegment:
    def __init__(self, index, checksum, data):
        self.index = index
        self.checksum = checksum
        self.data = data

    def has_valid_checksum(self) -> bool:
        return self.checksum == calculate_checksum(struct.pack(constants.FRAGMENT_INDEX, self.index), self.data)

class ReplySegment(DataSegment):
    def has_valid_checksum(self) -> bool:
        return self.checksum == calculate_checksum(struct.pack(constants.FRAGMENT_INDEX, self.index), 
                                                self.data.encode(constants.ENCODING))