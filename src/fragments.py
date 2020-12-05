from packing import calculate_checksum # TODO : remove this stupidity
import constants as const
import struct

class StartingFragment:
    def __init__(self, starting_header):
        self._starting_header= starting_header
        self._header = self._process_starting_header(starting_header)
        self.fragments_amount = self._header[0]
        self.fragment_size = self._header[1]
        self.checksum = self._header[2]
        self.data_type = self._header[3]
        self.file_path = self._header[4]

    def _process_starting_header(self, starting_fragment) -> tuple:
        #TODO: check alternative constant
        header = struct.unpack(const.STARTING_HEADER, starting_fragment[:const.STARTING_HEADER_SIZE])
        file_path = starting_fragment[const.STARTING_HEADER_SIZE:]
        if not file_path:
            file_path = None
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        return list(header) + [file_path]

    def has_valid_checksum(self) -> bool:
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        header_without_checksum = struct.pack(const.STARTING_HEADER_WO_CHECKSUM, 
                        self.fragments_amount,
                        self.fragment_size,
                        self.data_type
                )
        #header[2] -> checksum
        return self.checksum == calculate_checksum(header_without_checksum, self.file_path)

    def __call__(self):
        return self._starting_header


class DataFragment:
    def __init__(self, data_fragment):
        self._data_fragment = data_fragment
        self._header = self._process_data_fragment(data_fragment)
        self.index = self._header[0]
        self.checksum = self._header[1]
        self.data = self._header[2]

    def _process_data_fragment(self, fragment) -> tuple:
        """ Separate information in the received fragment"""
        header = struct.unpack(const.DATA_HEADER, fragment[0:const.DATA_HEADER_SIZE])
        data = fragment[const.DATA_HEADER_SIZE:] 
        return list(header) + [data] # Index, Checksum, Data

    def has_valid_checksum(self) -> bool:
        fragment_index = struct.pack(const.FRAGMENT_INDEX, self.index)
        calculated_checksum = calculate_checksum(fragment_index, self.data)
        return self.checksum == calculated_checksum

    def create_reply(self, data_type : bytes):
        reply = struct.pack(const.FRAGMENT_INDEX, self.index)
        reply += struct.pack(const.CHECKSUM, calculate_checksum(reply, data_type))
        reply += data_type
        return reply

    def __call__(self):
        return self._data_fragment


class ReplyFragment:
    def __init__(self, reply):
        self._reply = reply
        self._header = self._process_reply(reply)
        self.index = self._header[0]
        self.checksum = self._header[1]
        self.data_type = self._header[2]

    def _process_reply(self, reply) -> tuple:
        """ Separate information in the received fragment"""
        # Index, Checksum, Data type
        return struct.unpack(const.REPLY_HEADER, reply)

    def has_valid_checksum(self) -> bool:
        fragment_index = struct.pack(const.FRAGMENT_INDEX, self.index)
        calculated_checksum = calculate_checksum(fragment_index, self.data_type)
        return self.checksum == calculated_checksum

    def __call__(self):
        return self._reply