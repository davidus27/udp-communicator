import socket
from concurrent.futures import ThreadPoolExecutor
import constants as const
import packing
from random import seed, random
from fragments import *

seed()
"""
TODO : Set more consistent terminology 

Fragment = something hehe
fragment = one part of whole data
Package = Group of fragments that are sent together
"""

class ClientSide(object):
    def __init__(self, reciever: tuple, port: int, content: packing.Packaging, send_false_packets=False):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.reciever = reciever
        self.port = port
        self.content = content
        self.data = content.get_fragment_generator()
        self.window = []
        self.send_false_packets = send_false_packets

    def _send_starting_message(self):
        self.node.bind(('', self.port))
        self.node.settimeout(const.TIMEOUT)
        self.node.sendto(self.content.get_starting_fragment(), self.reciever)
        if self.content.header_info[1] == b'F':
            print("Sending file", self.content.header_info[2].decode(const.CODING_FORMAT))

    def _send_fragment(self, index, fragment):
        # randomly generate wrong response if setup
        if self.send_false_packets and random() < const.WRONG_PACKET_RATIO:
            self.node.sendto(self.content.get_wrong_data_fragment(index, fragment), self.reciever)    
        else:
            # send correct response
            self.node.sendto(self.content.get_data_fragment(index, fragment), self.reciever)

    def process_response(self, response, index) -> bool:
        processed_reply = ReplyFragment(response)
        if processed_reply.has_valid_checksum() and processed_reply.data_type == const.ACK:
            self.window = list(filter(lambda x: x[0] != processed_reply.index, self.window))
            try: 
                next_fragment = next(self.data)
            except StopIteration:
                return True
            else:
                self.window.append((index, next_fragment))
                self._send_fragment(index, next_fragment)
     
        elif processed_reply.has_valid_checksum() and processed_reply.data_type == const.NACK:
            print("Caught NACK. Sending packet again.")
            corrected_data = list(filter(lambda x: x[0] == processed_reply.index, self.window))[0][1]
            self.node.sendto(self.content.get_data_fragment(processed_reply.index, corrected_data), self.reciever)
        else:
            print("Error, unknown packet found.")
        return False

    def create_connection(self):
        while True:
            self._send_starting_message()
            response, _ = self.node.recvfrom(const.STARTING_HEADER_SIZE)
            if response == const.ACK:
                break
    
    def keep_alive(self):
        pass

    def send_whole_window(self):
        # send all fragments from the window
        for fragment in self.window:
            self.node.sendto(self.content.get_data_fragment(fragment[0], fragment[1]), self.reciever)
        
    def send_data(self):
        # Fill empty window
        index = 0
        for _ in range(const.FRAGMENTS_AMOUNT):
            try:
                self.window.append((index, next(self.data)))
                index += 1
            except StopIteration:
                break

        self.send_whole_window()

        while self.window:
            try:
                response, _ = self.node.recvfrom(const.REPLY_HEADER_SIZE)
                with ThreadPoolExecutor(max_workers=const.MAXIMUM_THREADS) as executor:
                    index += 1
                    thread = executor.submit(self.process_response, response, index)
                    thread.result()
            except socket.timeout:
                self.send_whole_window()
        self.node.sendto(const.END, self.reciever)

    def handle_communication(self):
        while True:
            self.create_connection()
            self.send_data()
            if not self.keep_alive():
                break

