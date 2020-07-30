import socket
import struct
from concurrent.futures import ThreadPoolExecutor
import constants

"""
Segment = one part of whole data
Package = Group of segments that are sent together
"""


def calculate_checksum(fragment):
    return sum(fragment) % 255


class ClientSide(object):
    def __init__(self, reciever: tuple, content):
        self.reciever = reciever
        self.content = content
        self.fragments_amount = content.calculate_fragments_amount()

    def _send_package(self, package, segment_counter):
        package_sent_correctly = False
        while not package_sent_correctly:
            for fragment in package:
                fragment = fragment.encode(constants.CODING_FORMAT)

                header = struct.pack(constants.DATA_HEADER, 
                                        segment_counter, 
                                        calculate_checksum(fragment))

                self.node.sendto(header + fragment, self.reciever)
                segment_counter += 1
                
            respond, _ = self.node.recvfrom(2)
            if respond == constants.ACK:
                package_sent_correctly = True
            elif respond == constants.NACK:
                print("Something went wrong.")

    def send_data(self):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        segment_counter = 0
        starting_message = struct.pack(constants.STARTING_HEADER, 
                                            *self.content.get_starting_header())
        self.node.sendto(starting_message, self.reciever)
        for package in self.content.split_data():
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._send_package, package, segment_counter)
                segment_counter += 10
                thread.result()

        self.node.sendto(constants.ENDING, self.reciever)