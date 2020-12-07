import constants as const
import socket
import time
import concurrent.futures

class KeepAlive(object):
    def __init__(self, port):
        self._is_blocked = False # can't continue with keep alive
        self._can_continue = True # can't continue with communication
        self.port = port
        self.node = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _set_socket(self):
        self.node.bind(('', self.port))

    def communication_can_continue(self):
        return self._can_continue

    def _stop_keep_alive(self):
        self._is_blocked = True
        self._can_continue = False

    def _send_keep_alive(self):
        self.node.settimeout(const.KEEP_ALIVE_TIMEOUT)
        self.node.sendto(const.KEEP_ALIVE, self.address)
        
    def ask_user(self):
        if input("Press q for ending session, or any key to continue.").upper() == "Q":
            self.node.sendto(const.END_BY_USER, self.address)
            self._can_continue = False
        else:
            self.node.sendto(const.START_COMMUNICATION, self.address)
            self._can_continue = True
        self._is_blocked = True

    def keep_alive_communication(self):
        while not self._is_blocked:
            try:
                response, _ = self.node.recvfrom(const.ENDING_MESSAGE_LEN)
            except socket.timeout:
                self.node.sendto(const.END_BY_TIMEOUT, self.address)
                print("Ending with timeout")
                self._stop_keep_alive()
            if response == const.KEEP_ALIVE:
                time.sleep(const.KEEP_ALIVE_SLEEP)
                self._send_keep_alive()
            elif response == const.START_COMMUNICATION:
                print("Starting new communication.")
                self._is_blocked = True
                self._can_continue = True
            elif response == const.END_BY_TIMEOUT:
                print("End by user")
                self._stop_keep_alive()
            elif response == const.END_BY_TIMEOUT:
                print("End by timeout.")
                self._stop_keep_alive()


    def keep_alive(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            threads = [executor.submit(self.keep_alive_communication), executor.submit(self.ask_user)]
            # return first answer that came out
            for t in concurrent.futures.as_completed(threads):
                return t.result()