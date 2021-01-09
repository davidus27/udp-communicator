from server import ServerSide
from client import ClientSide
from packing import Packaging
from questions import *

class SettingStrategy():
    def __init__(self):
        self._strategy = None
        self.arguments = []
        self.keep_alive_disabled = None

    def get_strategy(self):
        """
        Adds outputs from questions to the list of arguments for
        specific strategy
        """ 
        if self._strategy is ServerSide:
            self.arguments = [ask_for_port()]

        elif self._strategy is ClientSide:
            self.arguments = [ask_for_recipient(), 
                            ask_for_listening_port(),
                            self._get_header(),
                            ask_for_test()]
        return self._strategy(*self.arguments)

    def _get_header(self):
        header = ask_for_header_info()
        return Packaging(header[0], header[1:])
    
    def set_strategy(self):
        side = ask_for_strategy()
        options = {"C": ClientSide, "S":ServerSide, "Q": False}
        self._strategy = options[side]
        return True
    
    def ask_questions(self):
        self.set_strategy()
        if self._strategy:
            strategy = self.get_strategy()
            self.keep_alive_disabled = ask_for_keep_alive()
            return strategy

    def execute_side(self):
        """
        Execute sides needed parts
        """
        strategy = self.ask_questions()
        while strategy:
            strategy.handle_communication()
            if self.keep_alive_disabled:
                if user_want_to_stop():
                    return
                strategy = self.ask_questions()
            else:
                strategy.keep_alive()
                if not strategy.communication_can_continue():
                    # keep alive is indicating to stop
                    return
                if self._strategy is ClientSide:
                    # this is terrible, but should work
                    self.arguments = [self._get_header(),
                                    ask_for_test()]
                    strategy.change_args(*self.arguments)
            
if __name__ == "__main__":
    SettingStrategy().execute_side()