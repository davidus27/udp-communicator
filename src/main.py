from server import ServerSide
from client import ClientSide
from packing import Packaging
from questions import *

class SettingStrategy():
    def __init__(self):
        self._strategy = None
        self.arguments = []

    def get_strategy(self):
        """
        Adds outputs from questions to the list of arguments for
        specific strategy
        """ 
        if self._strategy is ServerSide:
            self.arguments = [ask_for_port()]
            #self.arguments.append(ask_for_implementation())

        elif self._strategy is ClientSide:
            self.arguments = [ask_for_recipient(), 
                            ask_for_listening_port(),
                            self._get_header(),
                            ask_for_test()]
            # based on what will be in implementation
            #self.arguments.append(ask_for_implementation())
        return self._strategy(*self.arguments)

    def _get_header(self):
        header = ask_for_header_info()
        return Packaging(header[0], header[1:])
    def clear_options(self):
        self.arguments = []
        self._strategy = None
        
    def ask_for_strategy(self):
        side = input("Do you want to run as server or a client? [S/c]: ").upper()
        if side == "C":
            self._strategy = ClientSide
        elif side == "S" or side == "":
            self._strategy = ServerSide
        elif side == "Q":
            return False
        return True
    
    def execute_side(self):
        """
        Execute sides needed parts
        """
        while True:
            if self.ask_for_strategy():
                self.get_strategy().handle_communication()
            else:
                break
            if input("Press q for ending session, or any key to continue.") == "q":
                break
            self.clear_options()


if __name__ == "__main__":
    SettingStrategy().execute_side()