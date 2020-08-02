import socket
from concurrent.futures import ThreadPoolExecutor
import constants
import packing

"""
Segment = one part of whole data
Package = Group of segments that are sent together
"""

class ClientSide(object):
    def __init__(self, reciever: tuple, content: packing.StartingFragment):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.reciever = reciever
        self.content = content

    def _send_package(self, package, segment_counter):
        package_sent_correctly = False
        while not package_sent_correctly:
            for fragment_data in package:
                fragment = self.content.get_segment(fragment_data, segment_counter)
                self.node.sendto(fragment, self.reciever)
                segment_counter += 1
                
            respond, _ = self.node.recvfrom(5) # OK or ERROR
            if respond == constants.ACK:
                package_sent_correctly = True
            elif respond == constants.NACK:
                print("Something went wrong.")

    def send_data(self):
        segment_counter = 0
        self.node.sendto(self.content.get_starting_segment(), self.reciever)
        for package in self.content.split_data():
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._send_package, package, segment_counter)
                segment_counter += 10
                thread.result()
        self.node.sendto(constants.ENDING, self.reciever)