import socket
from concurrent.futures import ThreadPoolExecutor
import constants
import packing
import sys


"""
TODO : Set more consistent terminology 

Fragment = something hehe
Segment = one part of whole data
Package = Group of segments that are sent together
"""

class ClientSide(object):
    def __init__(self, reciever: tuple, content: packing.StartingFragment):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.reciever = reciever
        self.content = content
        self.window = []
        self.is_locked = False

    def _send_starting_message(self):
        self.node.sendto(self.content.get_starting_segment(), self.reciever)

    def _send_package(self, package, segment_counter):
        package_sent_correctly = False
        temp = segment_counter
        while not package_sent_correctly:
            for fragment_data in package:
                fragment = self.content.get_data_segment(fragment_data, segment_counter)
                self.node.sendto(fragment, self.reciever)
                segment_counter += 1
                
            respond, _ = self.node.recvfrom(5) # OK or ERROR
            if respond == constants.ACK:
                package_sent_correctly = True
                sys.stdout.write(f"Package {temp} - {segment_counter} sent correctly \r")
                sys.stdout.flush()

            elif respond == constants.NACK:
                print("Something went wrong.")

    def send_data(self):
        segment_counter = 0
        self._send_starting_message()
        for package in self.content.split_data():
            # TODO : CHANGE ALL THIS TO WINDOWING ALGO
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self._send_package, package, segment_counter)
                segment_counter += 10
                thread.result()
            
        self.node.sendto(constants.END, self.reciever)

    def process_response(self, response):
        pass

    def send_data(self):
        self._send_starting_message()
        segments = self.content.yield_segments()
        
        # Fill empty window
        for _ in range(constants.SEGMENTS_AMOUNT):
            self.window.append(next(segments))

        # send all segments from the window 
        for segment in self.window:
            self.node.sendto(segment, self.reciever)

        response, _ = self.node.recvfrom(constants.REPLY_HEADER_SIZE)

        with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor: 
                thread = executor.submit(self.process_response, response)
                thread.result()

        
        self.node.sendto(constants.END, self.reciever)

"""
TODO: 
    - finish send_data
    - implement process_response
    - redo packing for segments.py compability
    - set better terminology (segment vs fragment)
    - remove extra methods
    - comment everything
    - finish all other TODO's
    - test everything
"""
