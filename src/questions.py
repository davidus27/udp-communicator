import constants as const
from socket import gethostbyname, gethostname

import pathlib
import os

# Getting input from the files

def ask_again(function):
    def decorate(*args):
        result = None
        while result is None:
            result = function(*args)
            if result is None:
                print("Wrong input. Try again.")
        return result
    return decorate     

@ask_again
def ask_for_file():
    data = None
    file_path = input("Input file path: ").encode(const.CODING_FORMAT)
    p = pathlib.Path(file_path.decode(const.CODING_FORMAT))
    if p.is_file():
        return None, os.path.abspath(file_path) # get absolute path
    else:
        print("File path not found.")
        return None

@ask_again
def ask_for_data(data_type):
    data_type = data_type.upper()
    if data_type == "F":
        return ask_for_file() # None, file path
    elif data_type == "M":
        message = input("Input the message: ").encode(const.CODING_FORMAT)
        if message == b"":
            print("Write something.")
            return None
        return message, None
    return None

@ask_again
def ask_for_fragment_size():
    try:
        fragment_size = int(input(f"Input fragment size {const.MIN_FRAGMENT_SIZE} - {const.MAX_FRAGMENT_SIZE}: "))
    except:
        return None
    if fragment_size < const.MIN_FRAGMENT_SIZE or fragment_size > const.MAX_FRAGMENT_SIZE:
        print("Wrong input")
        return None
    return fragment_size

@ask_again
def ask_for_header_info():
    data_type = input("Do you want to send file or message? [M/f]: ").upper()
    if data_type == "":
        data_type = "M"
    data, file_path = ask_for_data(data_type)
    fragment_size = ask_for_fragment_size()
    data_type = data_type.encode(const.CODING_FORMAT)
    return data, fragment_size, data_type, file_path

@ask_again
def ask_for_port():
    port = input("Input server port[5555]: ")
    if port != "":
        try:
            return int(port)
        except:
            return None
    return 5555

@ask_again
def ask_for_listening_port():
    port = input("Input your port[7777]: ")
    if port != "":
        try:
            return int(port)
        except:
            return None
    return 7777

@ask_again
def ask_for_recipient():
    ip = input("Input ip address[localhost]: ")
    if ip == "localhost" or ip == "":
        ip = gethostbyname(gethostname()) #local ip
    return ip, ask_for_port()

@ask_again
def ask_for_test():
    """ Returns boolean value based on input, None if wrong value """
    answer = input("Do you want to start a test?[y/N]: ").upper()
    if answer == "Y":
        return True
    elif answer == "N" or answer == "":
        return False
    else:
        return None


@ask_again
def ask_for_implementation():
    """ Returns boolean value based on input, None if wrong value """
    answer = input("Do you want to test implementation?[y/N]: ").upper()
    if answer == "Y":
        return True
    elif answer == "N" or answer == "":
        return False
    else:
        return None