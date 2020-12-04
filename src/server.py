from concurrent.futures import ThreadPoolExecutor
from packing import calculate_checksum
import socket
import time
import math
import sys
import constants
from segments import *

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

    def process_data(self) -> None:
        """ Function to either print message, or save the recieved file """
        self.data.sort(key=lambda x : x[0])
        self.data = list(map(lambda x : x[1], self.data))
        if self.starting_header.data_type == b"M":
            print(b"".join(self.data).decode(constants.CODING_FORMAT)) # TODO: CHECK IF CORRECT 
        else:
            with open(self.starting_header.file_path, "wb+") as f:
                for d in self.data:
                    f.write(d)

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
        if self.starting_header.data_type == b"F":
            progress = math.ceil(100 * len(self.data) / self.starting_header.fragments_amount)
            sys.stdout.write("Downloading file : %d%%   \r" % (progress) )
            sys.stdout.flush()

    def send_NACK(self, process_segment) -> None:
        self.node.sendto(process_segment.create_reply(constants.NACK), self.address)
        print("Wrong checksum. Sending NACK.")

    def send_ACK(self, process_segment) -> None:
        self.node.sendto(process_segment.create_reply(constants.ACK), self.address)

    def process_segment(self, segment : DataSegment) -> None:
        """ Check if segment is correct, save it or drop it and reply to the client """
        processed_segment = DataSegment(segment)
        if processed_segment.has_valid_checksum():
            # save segment
            self.data.append((processed_segment.index, processed_segment.data)) 
            self.send_ACK(processed_segment)
        else:
            self.send_NACK(processed_segment)
        self.print_progress()

    def handle_communication(self):
        """ Listen on port for segment, if recieved create new thread so it can be processed """
        while not self.recieved_everything():
            segment, _ = self.node.recvfrom(self.starting_header.fragment_size + constants.DATA_HEADER_SIZE)
            if segment == constants.END:
                #self.node.sendto(constants.ACK, self.address)
                print("Recieved END segment. Ending session...")
                return
            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor: 
                thread = executor.submit(self.process_segment, segment)
                thread.result()

    def create_connection(self) -> None:
        """ Wait for start of connection """
        while True:
            initial_segment, self.address = self.node.recvfrom(constants.MAX_STARTING_HEADER_SIZE)
            starting_header = StartingSegment(initial_segment)
            if starting_header.has_valid_checksum():
                self.starting_header = starting_header
                self.node.sendto(constants.ACK, self.address)
                return
            else:
                self.node.sendto(constants.NACK, self.address)
    
    def start_listening(self) -> None:
        """ 
        Main function of class. 
        Listens on the port, creates connection and handles it.
        """
        if self.set_socket():
            print(f"[LISTENING] port: {self.port}")
            self.create_connection()
            self.handle_communication()
            self.process_data()