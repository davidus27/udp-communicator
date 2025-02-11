from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from packing import calculate_checksum
import socket
import time
import math
import sys
import ntpath
import time
import constants as const
from keep_alive import KeepAlive
from fragments import *

def get_file_name(path):
    if path:
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)
    return None


class ServerSide(KeepAlive):
    def __init__(self, port):
        KeepAlive.__init__(self, port)
        self.data = []
        self.address = None
        # starting header: fragment amount, fragment size, checksum, data type
        self.starting_header = None 
    
    def _clear_data(self):
        self.data = []
        self.starting_header = None

    def process_data(self) -> None:
        """ Function to either print message, or save the recieved file """
        self.data.sort(key=lambda x : x[0])
        self.data = list(map(lambda x : x[1], self.data))
        if self.starting_header.data_type == b"M":
            print()
            print(b"".join(self.data).decode(const.CODING_FORMAT))
        else:
            # slice absolute file path and save only name
            file_path = get_file_name(self.starting_header.file_path)
            with open(file_path, "wb+") as f:
                for d in self.data:
                    f.write(d)
        self._clear_data()

    def set_socket(self) -> None:
        """ Sets the socket binding with the posibility of resusing the same port """
        try:
            super()._set_socket()
            self.node.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # fix of 'port already used'
            return self.node
        except PermissionError as e:
            print(e)
        except (ValueError, TypeError):
            print("Unknown port.")
        except OSError:
            return self.node # already binded

    def recieved_everything(self) -> bool:
        """ Checking if all fragments were sent """
        return len(set(self.data)) == self.starting_header.fragments_amount

    def print_progress(self, index) -> None:
        """ Printing progress bar for estetics """
        if self.starting_header.data_type == b"F":
            progress = math.ceil(100 * len(self.data) / self.starting_header.fragments_amount)
            sys.stdout.write(f"Downloading file : {progress}%. Received {index}. packet.   \r")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"Currently received {index}. packet.   \r")
            sys.stdout.flush() 

    def send_NACK(self, process_fragment) -> None:
        self.node.sendto(process_fragment.create_reply(const.NACK), self.address)
        print(f"Wrong checksum of fragment {process_fragment.index}. Sending NACK.")

    def send_ACK(self, process_fragment) -> None:
        self.node.sendto(process_fragment.create_reply(const.ACK), self.address)

    def process_fragment(self, fragment : DataFragment) -> None:
        """ Check if fragment is correct, save it or drop it and reply to the client """
        processed_fragment = DataFragment(fragment)
        if processed_fragment.has_valid_checksum():
            # save fragment
            self.data.append((processed_fragment.index, processed_fragment.data)) 
            self.send_ACK(processed_fragment)
        else:
            self.send_NACK(processed_fragment)
        self.print_progress(processed_fragment.index)

    def listen(self):
        """ Listen on port for fragment, if recieved create new thread so it can be processed """
        while not self.recieved_everything():
            fragment, _ = self.node.recvfrom(self.starting_header.fragment_size + const.DATA_HEADER_SIZE)
            if fragment == const.END:
                self.node.sendto(const.ACK, self.address)
                print("Recieved END fragment. Ending session...")
                return
            with ThreadPoolExecutor(max_workers=const.MAXIMUM_THREADS) as executor: 
                thread = executor.submit(self.process_fragment, fragment)
                thread.result()
        self.node.recvfrom(len(const.END))

    def keep_alive_communication(self):
        super().keep_alive_communication()

    def create_connection(self) -> None:
        """ Wait for start of connection """
        while True:
            initial_fragment, self.address = self.node.recvfrom(const.MAX_STARTING_HEADER_SIZE)
            if len(initial_fragment) < const.STARTING_HEADER_SIZE:
                continue
            starting_header = StartingFragment(initial_fragment)
            if starting_header.has_valid_checksum():
                self.starting_header = starting_header
                self.node.sendto(const.ACK, self.address)
                return
            else:
                self.node.sendto(const.NACK, self.address)
    
    def print_info(self):
        file_path = self.starting_header.file_path
        if file_path:
            print(f"File {file_path.decode(const.CODING_FORMAT)} will be saved locally.")
        print("Size of framgents:", self.starting_header.fragment_size)
        print("Amount of fragments:", self.starting_header.fragments_amount)


    def handle_communication(self) -> None:
        """ 
        Main function of class. 
        Listens on the port, creates connection and handles it.
        """
        if self.set_socket():
            print(f"[LISTENING] port: {self.port}")
            self.create_connection()
            self.print_info()
            self.listen()
            self.process_data()