"""
measure the time it takes to pack and parse a CAN message

reuslts (Feater M4):
pack: 0.198 ms
parse: 0.174 ms


"""

import time
import gc
from collections import namedtuple
import struct
import can_protocol as protocol

node_id = 10
iterations = 1000


# --------nop---------
gc.collect()
t_start = time.monotonic_ns()
for _ in range(iterations):
    pass
t_elapsed = (time.monotonic_ns() - t_start) / 1e6
t_nop = t_elapsed / iterations
print(f"nop: {t_nop:.3f} ms")

# --------pack--------
gc.collect()
t_start = time.monotonic_ns()
for _ in range(iterations):
    msg = protocol.HeartbeatMessage(node_id, 1, 2, 3, 7)
    message_id, data_bytes = msg.pack()

t_end = time.monotonic_ns()
t_elapsed = (t_end - t_start) / 1e6
t_pack = t_elapsed / iterations
print(f"pack: {t_pack:.3f} ms")

# --------parse--------
gc.collect()
msg = protocol.HeartbeatMessage(node_id, 1, 2, 3, 7)
msg_id = protocol.generate_message_id(msg.opcode, node_id)

t_start = time.monotonic_ns()
for _ in range(iterations):
    msg2 = protocol.parse(msg_id, b"\x01\x02\x00\x03\x00\x00\x00\x07")

t_end = time.monotonic_ns()
t_elapsed = (t_end - t_start) / 1e6
t_parse = t_elapsed / iterations
print(f"parse: {t_parse:.3f} ms")


# -------- proto simple protocol --------

# parsing without creating separate message classes

Heartbeat = namedtuple("Heartbeat", "error_code error_count uptime version")
byte_def = "<BHIB"
opcode = 1
msg_id = protocol.generate_message_id(msg.opcode, node_id)

t_start = time.monotonic_ns()
for _ in range(iterations):
    opcode, node_id = protocol.split_message_id(msg_id)
    msg = struct.unpack(byte_def, b"\x01\x02\x00\x03\x00\x00\x00\x07")
t_end = time.monotonic_ns()
t_elapsed = (t_end - t_start) / 1e6
t_proto = t_elapsed / iterations
print(f"proto: {t_proto:.3f} ms")
