from server import ServerSide
from client import ClientSide
from packing import StartingFragment
import questions

class SettingStrategy():
    def __init__(self):
        self._strategy = None
        self.arguments = []

    def add_data_info(self):
        args = None
        while not args:
            args = self._ask_for_header_info()
        self.arguments.append(StartingFragment(args[0], args[1:]))

    def get_strategy(self):
        if self._strategy is ServerSide:
            self.arguments.append(int(input("Input port: ")))
        elif self._strategy is ClientSide:
            self.arguments.append(questions.ask_for_recipient())

            header = questions.ask_for_header_info()
            self.arguments.append(StartingFragment(header[0], header[1:]))
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
            side = input("Do you want to run as server or a client? [S/c]: ")
            if side.upper() == "C":
                self._strategy = ClientSide
                self.get_strategy().send_data()
            elif side.upper() == "S" or side == "":
                self._strategy = ServerSide
                self.get_strategy().start_listening()
            elif side.upper() == "Q":
                break
            if input("Press q for ending session, or any key to continue.") == "q":
                break
            self.clear_options()


if __name__ == "__main__":
    context = SettingStrategy()
    context.execute_side()