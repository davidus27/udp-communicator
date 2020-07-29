from concurrent.futures import ThreadPoolExecutor
import struct
import socket
import time
import os
import constants

#checkit
from packing import FragmentPacking

def calculate_checksum(fragment):
    return sum(fragment) % 255

class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []
        self.node = None
        
    def _receive_package(self, address, message) -> bool:
        header_size = struct.calcsize(constants.DATA_HEADER)
        while True:
            package = []
            for _ in range(constants.SEGMENTS_AMOUNT):
                segment, _ = self.node.recvfrom(message[2])
                if segment == constants.ENDING:
                    print("Recieved END segment. Ending session.")
                    return True
                header = struct.unpack(constants.DATA_HEADER, segment[0:header_size])
                data = segment[header_size:]
                package.append((header, data))
                print(f"Segment {header[0]} of size: {message[1]}")
            if len(set(package)) == constants.SEGMENTS_AMOUNT:
                self.node.sendto(constants.ACK, address)
                return False
            else:
                print("send again.")
                self.node.sendto(constants.NACK, address)

    def _process_data(self):
        pass

    def _set_socket(self):
        if not self.node:
            try:
                self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.node.bind(("", self.port))
            except PermissionError as e:
                print("Well known port used.")
                print(e)
            except (ValueError, TypeError):
                print("Unknown port.")

    def _handle_communication(self, communication_start, address):
        message = struct.unpack(constants.STARTING_HEADER, communication_start)
        self.node.sendto(constants.ACK, address)
        while True:
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._receive_package, address, message)
                if thread.result():
                    self._process_data()
                    return


    def start_listening(self):
        self._set_socket()
        while True:
            print(f"[LISTENING] port: {self.port}")
            initial_segment, address = self.node.recvfrom(constants.STARTING_HEADER_SIZE)
            self._handle_communication(initial_segment, address)
            if input("Press q for ending session, or any key to continue.") == "q":
                break