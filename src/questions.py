import constants as const
from socket import gethostbyname, gethostname

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
    with open(file_path, "rb") as f:
        data = f.read()
    return data, file_path

@ask_again
def ask_for_data(data_type):
    data_type = data_type.upper()
    if data_type == "F":
        return ask_for_file() # data, file_path
    elif data_type == "M":
        message = input("Input the message: ").encode(const.CODING_FORMAT)
        return message, None
    return None

@ask_again
def ask_for_fragment_size():
    fragment_size = int(input(f"Input fragment size {const.MIN_FRAGMENT_SIZE} - {const.MAX_FRAGMENT_SIZE}: "))
    if fragment_size < const.MIN_FRAGMENT_SIZE or fragment_size > const.MAX_FRAGMENT_SIZE:
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