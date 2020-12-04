import socket
from concurrent.futures import ThreadPoolExecutor
import constants
import packing
from segments import *

"""
TODO : Set more consistent terminology 

Fragment = something hehe
Segment = one part of whole data
Package = Group of segments that are sent together
"""

class ClientSide(object):
    def __init__(self, reciever: tuple, content: packing.Packaging, send_false_packets=False):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.reciever = reciever
        self.content = content
        self.data = content.yield_segments()
        self.window = []
        self.send_false_packets = send_false_packets

    def _send_starting_message(self):
        self.node.sendto(self.content.get_starting_segment(), self.reciever)

    def process_response(self, response, index) -> bool:
        processed_reply = ReplySegment(response)
        if processed_reply.data_type == constants.ACK:
            self.window = list(filter(lambda x: x[0] != processed_reply.index, self.window))
            try: 
                next_segment = next(self.data)
            except StopIteration:
                return True
            else:
                self.window.append((index, next_segment))
                self.node.sendto(self.content.get_data_segment(index, next_segment), self.reciever)
        elif processed_reply.data_type == constants.NACK:
            print("Caught NACK. Sending packet again.")
            self.node.sendto(self.content.get_data_segment(processed_reply.index, processed_reply.data_type), self.reciever)
        
        elif processed_reply.data_type == constants.KEEP_ALIVE:
            self.node.sendto(constants.KEEP_ALIVE, self.reciever)
        
        return False

    def send_data(self):
        index = 0
        while True:
            self._send_starting_message()
            response, _ = self.node.recvfrom(constants.STARTING_HEADER_SIZE)
            if response == constants.ACK:
                break
        # Fill empty window
        for _ in range(constants.SEGMENTS_AMOUNT):
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
            response, _ = self.node.recvfrom(constants.REPLY_HEADER_SIZE)
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                index += 1
                thread = executor.submit(self.process_response, response, index)
                if thread.result():
                    break

        self.node.sendto(constants.END, self.reciever)

