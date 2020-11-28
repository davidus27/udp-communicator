from concurrent.futures import ThreadPoolExecutor
from packing import calculate_checksum
import struct
import socket
import time
import os
import math
import sys
import constants
from segments import *


class ProcessRecievedData(object):
    @staticmethod
    def separate_data_segment(segment) -> DataSegment:
        """ Separate information in the received segment"""
        header = struct.unpack(constants.DATA_HEADER, segment[0:constants.DATA_HEADER_SIZE])
        data = segment[constants.DATA_HEADER_SIZE:] 
        return DataSegment(*header, data) # Index, Checksum, Data

    @staticmethod
    def separate_starting_header(starting_segment) -> StartingSegment:
        #TODO: check alternative constant
        header = struct.unpack(constants.STARTING_HEADER, starting_segment[:constants.STARTING_HEADER_SIZE])
        file_path = starting_segment[constants.STARTING_HEADER_SIZE:]
        # Fragments amount + Fragment size + Checksum + Data Type + file_path
        return StartingSegment(*header, file_path)


class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []
        self.address = None
        self.starting_header = None # starting header: segment amount, segment size, checksum, data type
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def save_package(self, package) -> None:
        for fragment in package:
            self.data.append(fragment)

    def get_raw_data(self) -> str:
        for item in self.data:
            yield item[1].decode(constants.CODING_FORMAT)

    def _process_data(self) -> None:
        """ Function to either print message, or save the recieved file """
        self.data.sort(key=lambda x : x[0])
        if self.starting_header[3] == b"M":
            # print("".join(self.get_raw_data()))
            print(b"".join(self.data).decode(constants.CODING_FORMAT)) # TODO: CHECK IF CORRECT 
        with open(self.file_path, "wb+") as f:
            for d in self.data:
                f.write(d[1])

    def set_socket(self) -> None:
        """ Sets the socket binding with the posibility of resusing the same port """
        try:
            self.node.bind(("", self.port))
            self.node.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # fix of 'port already used'
            return self.node
        except PermissionError as e:
            print(e)
        except (ValueError, TypeError):
            print("Unknown port.")

    def recieved_everything(self) -> bool:
        """ Checking if all fragments were sent """
        return len(set(self.data)) == self.starting_header.fragments_amount

    def print_progress(self) -> None:
        """ Printing progress bar for estetics """
        progress = math.ceil(100 * len(self.data) / self.starting_header.fragments_amount)
        sys.stdout.write("Downloading file : %d%%   \r" % (progress) )
        sys.stdout.flush()

    def _receive_package(self, address) -> bool:
        while True:
            package = []
            error_segment_indexes = []
            for _ in range(constants.SEGMENTS_AMOUNT):
                segment, _ = self.node.recvfrom(self.starting_header[1])
                if segment == constants.END:
                    print("Recieved END segment. END session.")
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
                self.save_package(package)
                response = constants.ACK
            self.node.sendto(response, address)



    def send_NACK(self, index : int) -> None:
        response = struct.pack(constants.FRAGMENT_INDEX, index) + constants.NACK
        response += calculate_checksum(response)
        self.node.sendto(response, self.address)

    def send_ACK(self, index : int) -> None:
        response = struct.pack(constants.FRAGMENT_INDEX, index) + constants.ACK
        response += calculate_checksum(response)
        self.node.sendto(response, self.address)

    def process_segment(self, segment : DataSegment) -> None:
        """ Check if segment is correct, save it or drop it and reply to the client """
        processed_segment = ProcessRecievedData.separate_data_segment(segment)
        if processed_segment.has_valid_checksum():
            # save segment
            self.data.append(processed_segment.index, processed_segment.data) 
            self.send_ACK()
        else:
            self.send_NACK()
        self.print_progress()

    def handle_communication(self):
        """ Listen on port for segment, if recieved create new thread so it can be processed """
        while not self.recieved_everything():
            segment, _ = self.node.recvfrom(self.starting_header.fragment_size)
            if segment == constants.END:
                # should contain waiting for END ACK
                print("Recieved END segment. END session.")
                return
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor: 
                thread = executor.submit(self.process_segment, segment)
                thread.result()

    def create_connection(self) -> None:
        """ Wait for start of connection """
        while True:
            initial_segment, self.address = self.node.recvfrom(constants.MAX_STARTING_HEADER_SIZE)
            starting_header = ProcessRecievedData.separate_starting_header(initial_segment)

            if starting_header.has_valid_checksum():
                self.starting_header = starting_header
                self.node.sendto(constants.ACK, self.address)
            else:
                self.node.sendto(constants.NACK, self.address)
                print("SOMETHING IS WRONG") # TODO : DELETE
    
    def start_listening(self) -> None:
        """ 
        Main function of class. 
        Listens on the port, creates connection and handles it.
        """
        if self.set_socket():
            print(f"[LISTENING] port: {self.port}")
            self.create_connection()
            self.handle_communication()