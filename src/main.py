from server import ServerSide
from client import ClientSide
from packing import Packaging
import questions

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
            self.arguments.append(questions.ask_for_port())
            #self.arguments.append(questions.ask_for_implementation())

        elif self._strategy is ClientSide:
            self.arguments.append(questions.ask_for_recipient())
            self.arguments.append(questions.ask_for_listening_port())
            
            header = questions.ask_for_header_info()
            self.arguments.append(Packaging(header[0], header[1:]))
            
            # extra arguments:
            self.arguments.append(questions.ask_for_test())
            # based on what will be in implementation
            #self.arguments.append(questions.ask_for_implementation())
        else:
            print("Error.")
        return self._strategy(*self.arguments)

    def clear_options(self):
        self.arguments = []
        self._strategy = None
        
    def execute_side(self):
        """
        Execute sides needed parts
        """
        while True:
            side = input("Do you want to run as server or a client? [S/c]: ").upper()
            if side == "C":
                self._strategy = ClientSide
                self.get_strategy().send_data()
            elif side == "S" or side == "":
                self._strategy = ServerSide
                self.get_strategy().start_listening()
            elif side == "Q":
                break
            if input("Press q for ending session, or any key to continue.") == "q":
                break
            self.clear_options()


if __name__ == "__main__":
    SettingStrategy().execute_side()