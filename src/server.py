from concurrent.futures import ThreadPoolExecutor
from packing import calculate_checksum
import struct
import socket
import time
import os
import math
import sys
import constants
import operator

class ProcessRecievedData(object):
    def __init__(self):
        pass

    @staticmethod
    def separate_data_segment(segment) -> tuple:
        """ Separate information in the received segment"""
        header = struct.unpack(constants.DATA_HEADER, segment[0:constants.DATA_HEADER_SIZE])
        data = segment[constants.DATA_HEADER_SIZE:]
        return header[0], header[1], data  # Index, Checksum, Data

    @staticmethod
    def separate_starting_header(starting_segment) -> tuple:
        #TODO: check alternative constant
        header = struct.unpack(constants.STARTING_HEADER, starting_segment[:constants.STARTING_HEADER_SIZE])
        file_path = starting_segment[constants.STARTING_HEADER_SIZE:]
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        return header[0], header[1], header[2], header[3], file_path # if message recieved file_path == b''

    @staticmethod
    def has_valid_checksum(header, file_path = 0) -> bool:
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        header_without_checksum = struct.pack(constants.STARTING_HEADER_WO_CHECKSUM, 
                        header[0],
                        header[1],
                        header[3]
                )
        #header[2] - checksum
        return header[2] == calculate_checksum(header_without_checksum, file_path)

class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []
        self.file_path = None
        # starting header: segment amount, segment size, data type, checksum
        self.starting_header = None
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def save_package(self, package):
        for fragment in package:
            self.data.append(fragment)

    def _receive_package(self, address) -> bool:
        while True:
            package = []
            error_segment_indexes = []
            for _ in range(constants.SEGMENTS_AMOUNT):
                segment, _ = self.node.recvfrom(self.starting_header[1])
                if segment == constants.ENDING:
                    print("Recieved END segment. Ending session.")
                    break
                index, checksum, data = ProcessRecievedData.separate_data_segment(segment)
                if checksum == calculate_checksum(struct.pack(constants.FRAGMENT_INDEX, index), data):
                    package.append((index, data))
                else:
                    error_segment_indexes.append(index)
                    print("Incorrect checksum.")

            # ask for the correct ones if some errors were issued
            if error_segment_indexes:
                print("Send me:", error_segment_indexes)
                response = constants.NACK
            # if all are correct save whole package to the self.data
            else:
                #self.node.sendto(constants.ACK, address)

                progress = math.ceil(100 * len(self.data) / self.starting_header[0])
                sys.stdout.write("Downloading file : %d%%   \r" % (progress) )
                sys.stdout.flush()
                self.save_package(package)
                response = constants.ACK

            self.node.sendto(response, address)

            if len(set(self.data)) == self.starting_header[0]:
                print("Got all packages, ending this session.")
                return True
            return False

    def get_raw_data(self):
        for item in self.data:
            yield item[1].decode(constants.CODING_FORMAT)

    def _process_data(self):
        self.data.sort(key=operator.itemgetter(0))
        if self.starting_header[3] == b"M":
            print("".join(self.get_raw_data()))
            return
            
        with open(self.file_path, "wb+") as f:
            for d in self.data:
                f.write(d[1])

    def set_socket(self):
        try:
            self.node.bind(("", self.port))
            return self.node
        except PermissionError as e:
            print(e)
        except (ValueError, TypeError):
            print("Unknown port.")


    def _handle_communication(self, address):
        while True:
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._receive_package, address)
                if thread.result():
                    self._process_data()
                    return


    def initialize_connection(self):
        while True:
            initial_segment, address = self.node.recvfrom(constants.MAX_STARTING_HEADER_SIZE)
            
            *header, file_path = ProcessRecievedData.separate_starting_header(initial_segment)

            if ProcessRecievedData.has_valid_checksum(header, file_path):
                self.starting_header = header
                self.file_path = file_path
                self.node.sendto(constants.ACK, address)
                return address
            else:
                self.node.sendto(constants.NACK, address)
                print("SOMETHING IS WRONG") # TODO : DELETE
    
    def start_listening(self):
        if self.set_socket():
            print(f"[LISTENING] port: {self.port}")
            address = self.initialize_connection()
            self._handle_communication(address)