import socket
import struct
from concurrent.futures import ThreadPoolExecutor
import packing

IP_ADDRESS = socket.gethostbyname(socket.gethostname())

"""
Segment = one part of whole data
Package = Group of segments that are sent together
"""

class ClientSide(object):
    def __init__(self, reciever: tuple, content: packing.FragmentPacking):
        self.reciever = reciever
        self.content = content
        self.fragment_amount = content.calculate_fragments_amount()

    def send_fragment(self):
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        for package in self.content.split_data():
            for segment in package:
                self.node.sendto(segment, self.reciever)
            
            respond, _ = self.node.recvfrom(2)
            if respond == packing.ACK:
                pass
            else:
                print("Something went wrong.")
            """
            while True:
                for segment in package:
                    self.node.sendto(segment, self.reciever)
                respond, _ = self.node.recvfrom(2)
                if respond == packing.ACK:
                    break
                elif respond == packing.NACK:
                    while True:
                        index, _ = self.node.recvfrom(1024)
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            thread = executor.submit(lambda index, package: package[index],package, int(index))
                            thread.result()
            """

        self.node.sendto(packing.ENDING, self.reciever)


lorem = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
f = packing.FragmentPacking(lorem, "t", 20)
ClientSide((IP_ADDRESS, 5555), f).send_fragment()