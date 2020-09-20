from concurrent.futures import ThreadPoolExecutor
import struct
import socket
import time
import os
import math
import sys
import constants
import operator
from packing import calculate_checksum

class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []
        self.file_path = None
        # starting header: segment amount, segment size, data type, checksum
        self.starting_header = None
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def separate_segment(self, segment):
        header_size = struct.calcsize(constants.DATA_HEADER)
        header = struct.unpack(constants.DATA_HEADER, segment[0:header_size])
        data = segment[header_size:]
        return header, data
    
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
                header, data = self.separate_segment(segment)
                if header[1] == calculate_checksum(struct.pack("i", header[0]), data):
                    package.append((header[0], data))
                else:
                    error_segment_indexes.append(header[0])
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
        if self.starting_header[2] == b"M":
            print("".join(self.get_raw_data()))
        else:
            try:
                with open(self.file_path, "wb+") as f:
                    for d in self.data:
                        f.write(d[1])
            except:
                print("No option available")

    def set_socket(self):
        try:
            self.node.bind(("", self.port))
            return self.node
        except PermissionError as e:
            print(e)
        except (ValueError, TypeError):
            print("Unknown port.")

    def _split_starting_header(self, starting_segment) -> tuple:
        #TODO: check alternative constant
        header_size = constants.STARTING_HEADER_SIZE
        header = struct.unpack(constants.STARTING_HEADER, starting_segment[0:header_size])
        checksum = starting_segment[header_size]
        file_path = starting_segment[header_size+1:]
        return header, checksum, file_path


    def _handle_communication(self, address):
        while True:
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._receive_package, address)
                if thread.result():
                    self._process_data()
                    return

    def _correct_header_caught(self, initial_segment, address) -> bool:
        header, checksum, file_path = self._split_starting_header(initial_segment)
        
        h = initial_segment[:constants.STARTING_HEADER_SIZE]
        if checksum == calculate_checksum(h, file_path): #TODO: not correct
            self.starting_header = header
            self.file_path = file_path
            self.node.sendto(constants.ACK, address)
            return True
        else:
            print("Checksum mismatch.")
            self.node.sendto(constants.NACK, address)
            return False

    def initialize_connection(self):
        initialized = False
        while not initialized:
            initial_segment, address = self.node.recvfrom(constants.STARTING_HEADER_SIZE
                                                            +constants.MAX_FILE_NAME_SIZE)
            initialized = self._correct_header_caught(initial_segment, address)
        return address
    
    def start_listening(self):
        if self.set_socket():
            print(f"[LISTENING] port: {self.port}")
            address = self.initialize_connection()
            self._handle_communication(address)