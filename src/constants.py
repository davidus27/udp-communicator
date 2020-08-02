import struct

CODING_FORMAT = "utf-8"
ACK = b"OK"
NACK = b"ERROR"
KEEP_ALIVE = b"KA"
ENDING = b"END."
STARTING_HEADER = "ihc" # Fragments amount + Fragment size + Data Type
DATA_HEADER = "iB"
SEGMENTS_AMOUNT = 10 # how many segments will be sent at once
STARTING_HEADER_SIZE = struct.calcsize(STARTING_HEADER) # bytes
DATA_HEADER_SIZE = struct.calcsize(DATA_HEADER)
MAX_FILE_NAME_SIZE = 255
MAXIMUM_THREADS = 5

MIN_FRAGMENT_SIZE = 50
MAX_FRAGMENT_SIZE = 1466