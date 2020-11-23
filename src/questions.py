import constants as const
from socket import gethostbyname, gethostname

MIN_FRAGMENT_SIZE = 50
MAX_FRAGMENT_SIZE = 1466

# Getting input from the files

def ask_again(function):
    def decorate(*args):
        result = None
        while not result:
            result = function(*args)
            if not result:
                print("Wrong input. Try again.")
        return result
    return decorate     

@ask_again
def ask_for_file():
    data = None
    file_path = input("Input file path: ").encode(const.CODING_FORMAT)
    with open(file_path, "rb") as f:
        data = f.read()
    return data, file_path

@ask_again
def ask_for_data(data_type):
    if data_type.upper() == "F":
        return ask_for_file() # data, file_path
    elif data_type.upper() == "M":
        message = input("Input the message: ").encode(const.CODING_FORMAT)
        return message, None
    return None

@ask_again
def ask_for_fragment_size():
    fragment_size = int(input(f"Input fragment size {MIN_FRAGMENT_SIZE} - {MAX_FRAGMENT_SIZE}: "))
    if fragment_size < MIN_FRAGMENT_SIZE or fragment_size > MAX_FRAGMENT_SIZE:
        print("Wrong input")
        return None
    return fragment_size

@ask_again
def ask_for_header_info():
    data_type = input("Do you want to send file or message? [M/f]: ")
    if data_type == "":
        data_type = "M"
    data, file_path = ask_for_data(data_type)
    fragment_size = ask_for_fragment_size()

    data_type = data_type.upper().encode(const.CODING_FORMAT)

    if file_path:
        return data, fragment_size, data_type, file_path 
    else:
        return data, fragment_size, data_type


@ask_again
def ask_for_recipient():
    ip = input("Input ip address: ")
    if ip == "localhost":
        ip = gethostbyname(gethostname()) #local ip
    
    try:
        port = int(input("Input port number: "))
    except:
        return None
    return ip, port
