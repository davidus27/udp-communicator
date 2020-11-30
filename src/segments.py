from packing import calculate_checksum # TODO : remove this stupidity
import constants
import struct

class StartingSegment:
    def __init__(self, starting_header):
        self._starting_header= starting_header
        self._header = self._process_starting_header(starting_header)
        self.fragments_amount = self._header[0]
        self.fragment_size = self._header[1]
        self.checksum = self._header[2]
        self.data_type = self._header[3]
        self.file_path = self._header[4]

    def _process_starting_header(self, starting_segment) -> tuple:
        #TODO: check alternative constant
        header = struct.unpack(constants.STARTING_HEADER, starting_segment[:constants.STARTING_HEADER_SIZE])
        file_path = starting_segment[constants.STARTING_HEADER_SIZE:]
        if not file_path:
            file_path = None
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        return list(header) + [file_path]

    def has_valid_checksum(self) -> bool:
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        header_without_checksum = struct.pack(constants.STARTING_HEADER_WO_CHECKSUM, 
                        self.fragments_amount,
                        self.fragment_size,
                        self.data_type
                )
        #header[2] -> checksum
        return self.checksum == calculate_checksum(header_without_checksum, self.file_path)

    def __call__(self):
        return self._starting_header


class DataSegment:
    def __init__(self, data_segment):
        self._data_segment = data_segment
        self._header = self._process_data_segment(data_segment)
        self.index = self._header[0]
        self.checksum = self._header[1]
        self.data = self._header[2]

    def _process_data_segment(self, segment) -> tuple:
        """ Separate information in the received segment"""
        header = struct.unpack(constants.DATA_HEADER, segment[0:constants.DATA_HEADER_SIZE])
        data = segment[constants.DATA_HEADER_SIZE:] 
        return list(header) + [data] # Index, Checksum, Data

    def has_valid_checksum(self) -> bool:
        fragment_index = struct.pack(constants.FRAGMENT_INDEX, self.index)
        calculated_checksum = calculate_checksum(fragment_index, self.data)
        return self.checksum == calculated_checksum

    def create_reply(self, data_type : bytes):
        reply = struct.pack(constants.FRAGMENT_INDEX, self.index)
        reply += struct.pack(constants.CHECKSUM, calculate_checksum(reply, data_type))
        reply += data_type
        return reply

    def __call__(self):
        return self._data_segment


class ReplySegment:
    def __init__(self, reply):
        self._reply = reply
        self._header = self._process_reply(reply)
        self.index = self._header[0]
        self.checksum = self._header[1]
        self.data_type = self._header[2]

    def _process_reply(self, reply) -> tuple:
        """ Separate information in the received segment"""
        # Index, Checksum, Data type
        return struct.unpack(constants.REPLY_HEADER, reply)

    def has_valid_checksum(self) -> bool:
        fragment_index = struct.pack(constants.FRAGMENT_INDEX, self.index)
        calculated_checksum = calculate_checksum(fragment_index, self.data_type)
        return self.checksum == calculated_checksum

    def __call__(self):
        return self._reply