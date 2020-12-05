import socket
from concurrent.futures import ThreadPoolExecutor
import constants as const
import packing
from random import seed, random
from segments import *

seed()
"""
TODO : Set more consistent terminology 

Fragment = something hehe
Segment = one part of whole data
Package = Group of segments that are sent together
"""

class ClientSide(object):
    def __init__(self, reciever: tuple, port: int, content: packing.Packaging, send_false_packets=False):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.reciever = reciever
        self.port = port
        self.content = content
        self.data = content.yield_segments()
        self.window = []
        self.send_false_packets = send_false_packets

    def _send_starting_message(self):
        self.node.bind(('', self.port))
        self.node.sendto(self.content.get_starting_segment(), self.reciever)
        if self.content.header_info[1] == b'F':
            print("Sending file", self.content.header_info[2].decode(const.CODING_FORMAT))

    def _send_segment(self, index, segment):
        # randomly generate wrong response if setup
        if self.send_false_packets and random() < const.WRONG_PACKET_RATIO:
            self.node.sendto(self.content.get_wrong_data_segment(index, segment), self.reciever)    
        else:
            # send good response
            self.node.sendto(self.content.get_data_segment(index, segment), self.reciever)

    def process_response(self, response, index) -> bool:
        processed_reply = ReplySegment(response)
        if processed_reply.has_valid_checksum() and processed_reply.data_type == const.ACK :
            self.window = list(filter(lambda x: x[0] != processed_reply.index, self.window))
            try: 
                next_segment = next(self.data)
            except StopIteration:
                return True
            else:
                self.window.append((index, next_segment))
                self._send_segment(index, next_segment)
     
        elif processed_reply.has_valid_checksum() and processed_reply.data_type == const.NACK:
            print("Caught NACK. Sending packet again.")
            corrected_data = list(filter(lambda x: x[0] == processed_reply.index, self.window))[0][1]
            self.node.sendto(self.content.get_data_segment(processed_reply.index, corrected_data), self.reciever)
        else:
            print("Error, unknown packet found.")
        
        return False

    def send_data(self):
        index = 0
        while True:
            self._send_starting_message()
            response, _ = self.node.recvfrom(const.STARTING_HEADER_SIZE)
            if response == const.ACK:
                break
        # Fill empty window
        for _ in range(const.SEGMENTS_AMOUNT):
            try:
                self.window.append((index, next(self.data)))
                index += 1
            except StopIteration:
                break

        # TODO: Change this. It should be better... 
        # send all segments from the window
        for segment in self.window:
            self.node.sendto(self.content.get_data_segment(segment[0], segment[1]), self.reciever)
        
        while self.window:
            response, _ = self.node.recvfrom(const.REPLY_HEADER_SIZE)
            with ThreadPoolExecutor(max_workers=const.MAXIMUM_THREADS) as executor:
                index += 1
                thread = executor.submit(self.process_response, response, index)
                thread.result()
                #if thread.result():
                #    break

        self.node.sendto(const.END, self.reciever)

