import struct

CODING_FORMAT = "utf-8"

# REWRITE
ACK = b"A"
NACK = b"N"
END = b"E"
KEEP_ALIVE = b"KA"
END_BY_USER = b"EU"
END_BY_TIMEOUT = b"ET"
START_COMMUNICATION = b"S"
ENDING_MESSAGE_LEN = len(KEEP_ALIVE)

REPLY_HEADER = "IHc" # Fragment index + Checksum + Reply Type

STARTING_HEADER_WO_CHECKSUM = "IHc" # Fragments amount + Fragment size + Data Type
STARTING_HEADER = "IHHc" # Fragments amount + Fragment size + Checksum + Data Type

FRAGMENT_INDEX = "I"
CHECKSUM = "H"
DATA_HEADER = FRAGMENT_INDEX + CHECKSUM
REPLY_HEADER_SIZE = struct.calcsize(REPLY_HEADER)
STARTING_HEADER_SIZE = struct.calcsize(STARTING_HEADER) # bytes
DATA_HEADER_SIZE = struct.calcsize(DATA_HEADER)
MAX_STARTING_HEADER_SIZE = 255 + STARTING_HEADER_SIZE


MIN_FRAGMENT_SIZE = 1
MAX_FRAGMENT_SIZE = 1466

# what ratio of packets should be randomly sent with wrong checkum
WRONG_PACKET_RATIO = 0.05

MAXIMUM_THREADS = 5
# TODO : delete
FRAGMENTS_AMOUNT = 10
TIMEOUT = 1.5 # 1.5 seconds
KEEP_ALIVE_TIMEOUT = 10
