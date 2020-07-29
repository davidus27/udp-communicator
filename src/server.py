from concurrent.futures import ThreadPoolExecutor
import struct
import socket
import time
import os
import constants


def calculate_checksum(fragment):
    return sum(fragment) % 255

class ServerSide(object):
    def __init__(self, port):
        self.port = port
        self.data = []

    def receive_message(self, received_data, address):
        if received_data == constants.ENDING:
            #print(b"".join(self.data).decode(constants.CODING_FORMAT))
            self.data = []
        else:
            header_size = struct.calcsize(constants.DATA_HEADER) 
            header = struct.unpack(constants.DATA_HEADER, received_data[0:header_size])
            message = received_data[header_size:]
            self.data.append((header, message))
            print((header, message))
        self.node.sendto(constants.ACK, address) # sending for each segment, should be after each package
        

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

            with ThreadPoolExecutor(max_workers=constants.MAXIMUM_THREADS) as executor:
                thread = executor.submit(self.receive_message, data, address)
                thread.result()

ServerSide(5555).start_listening()
