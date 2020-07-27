from concurrent.futures import ThreadPoolExecutor
import struct
import socket
import time
import os

import packing

MAXIMUM_THREADS = 5


class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []

    def receive_message(self, received_data, address):
        self.data.append(received_data)
        self.node.sendto(packing.ACK, address)

        #Only testing
        if len(self.data) > 57:
        #if self.node.recvfrom(6)[0] == b"KONIEC":
            print(b"".join(self.data).decode(packing.CODING_FORMAT))
            self.data = []
        

    def set_socket(self):
        try:
            self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.node.bind(("", self.port))
        except PermissionError as e:
            print("Well known port used.")
            print(e)
        except (ValueError, TypeError):
            print("Unknown port.")

    def start_listening(self):
        print(f"[LISTENING] port: {self.port}")
        self.set_socket()
        while True:
            data, address = self.node.recvfrom(1024)
            
            with ThreadPoolExecutor(max_workers=MAXIMUM_THREADS) as executor:
                thread = executor.submit(self.receive_message, data, address)
                thread.result()

ServerSide(5555).start_listening()
