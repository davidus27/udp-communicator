from concurrent.futures import ThreadPoolExecutor
import struct
import socket
import time
import os
import constants
import operator
#checkit
from packing import StartingInfo, calculate_checksum

class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []
        self.header = None
        self.node = None  

    def save_data(self, segment):
        header_size = struct.calcsize(constants.DATA_HEADER)
        header = struct.unpack(constants.DATA_HEADER, segment[0:header_size])
        data = segment[header_size:]
        self.data.append((header[0],data))


    def _receive_package(self, address, header) -> bool:
        while True:
            package = []
            for _ in range(constants.SEGMENTS_AMOUNT):
                segment, _ = self.node.recvfrom(header[2])
                if segment == constants.ENDING:
                    print("Recieved END segment. Ending session.")
                    return True
                self.save_data(segment)
            if len(set(self.data)) == self.header.fragments_amount:
                return True
            if len(set(package)) == constants.SEGMENTS_AMOUNT:
                self.node.sendto(constants.ACK, address)
                return False
            else:
                print("send again.")
                self.node.sendto(constants.NACK, address)

    def get_raw_data(self):
        for item in self.data:
            yield item[1].decode(constants.CODING_FORMAT)

    def _process_data(self):
        self.data.sort(key=operator.itemgetter(0), reverse=True)
        if self.header.data_type.decode(constants.CODING_FORMAT).upper() == "M":
            print("".join(self.get_raw_data()))
        else:
            try:
                with open(self.header.file_path, "w") as f:
                    for d in self.data:
                        f.write(d)
            except:
                print("No option available")

    def _set_socket(self):
        if not self.node:
            try:
                self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.node.bind(("", self.port))
                return self.node
            except PermissionError as e:
                print(e)
            except (ValueError, TypeError):
                print("Unknown port.")

    def _pull_starting_info(self, starting_segment):
        header_size = struct.calcsize(constants.STARTING_HEADER)
        header = struct.unpack(constants.STARTING_HEADER, starting_segment[0:header_size])
        file_path = starting_segment[header_size:]
        if header[2] == calculate_checksum(b'TODO'): # TODO: add checksum!!!
            self.header = StartingInfo(header[0], header[1], header[3], file_path=file_path)
            return header
        else:
            print("Checksum mismatch.")
            return None

    def _handle_communication(self, communication_start, address):
        header = self._pull_starting_info(communication_start)
        if header:
            self.node.sendto(constants.ACK, address)
        else:
            self.node.sendto(constants.NACK, address)
        while header:
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._receive_package, address, header)
                if thread.result():
                    self._process_data()
                    return

    def start_listening(self):
        if self._set_socket():
            print(f"[LISTENING] port: {self.port}")
            initial_segment, address = self.node.recvfrom(constants.STARTING_HEADER_SIZE)
            self._handle_communication(initial_segment, address)