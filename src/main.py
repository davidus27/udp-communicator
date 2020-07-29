from server import ServerSide
from client import ClientSide
from packing import FragmentPacking
from socket import gethostbyname, gethostname

class SettingStrategy():
    def __init__(self):
        self._strategy = None
        self.arguments = []

    def add_receiver_args(self):
        ip = input("Input ip address: ")
        if ip == "localhost":
            ip = gethostbyname(gethostname()) #local ip
        port = int(input("Input port number: "))
        self.arguments.append((ip, port))
        return ip, port

    def _ask_data_info(self):
        file_type = input("Do you want to send file or message? [M/f] ")
        if file_type.upper() == "F":
            file_path = input("Input file path: ")
            with open(file_path) as f:
                data = f.read()
        elif file_type.upper() == "M":
            data = input("Input the message: ")
        else:
            print("Wrong input")
            return
        fragment_size = int(input("Input fragment size 50 - 1466: "))
        if fragment_size < 50 or fragment_size > 1466:
            print("Wrong input")
            return
        try:
            x = (data, file_type, fragment_size, file_path)
        except Exception:
            x = (data, file_type, fragment_size)
        finally:
            return x

    def add_data_info(self):
        args = False
        while not args:
            args = self._ask_data_info()
        self.arguments.append(FragmentPacking(*args))


    def get_strategy(self):
        if self._strategy is ServerSide:
            self.arguments.append(input("Input port: "))
        elif self._strategy is ClientSide:
            self.add_receiver_args()
            self.add_data_info()
        else:
            print("Error.")
        return self._strategy(*self.arguments)

    def execute_side(self):
        """
        Execute sides needed parts
        """
        while True:
            side = input("Do you want to run as server or a client? [S/c]: ")
            if side.upper() == "C":
                self._strategy = ClientSide
                self.get_strategy().send_data()
            elif side.upper() == "S" or side == "":
                self._strategy = ServerSide
                self.get_strategy().start_listening()
            else:
                print("Wrong input. Try again.")


if __name__ == "__main__":
    context = SettingStrategy()
    context.execute_side()