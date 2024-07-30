#!/usr/bin/env python3
"""
measure the time it takes to pack and parse a CAN message

reuslts (Feater M4):

---- before refactor to namedtuple ----
pack: 0.198 ms
parse: 0.174 ms

---- after refactor to namedtuple ----
nop: 0.005 ms
pack: 0.081 ms
parse: 0.097 ms
parse-direct: 0.079 ms


"""

import time
import gc
import struct
import can_protocol as protocol

opcode = protocol.get_opcode(protocol.HeartbeatMessage)
node_id = 10
iterations = 1000

byte_def = protocol.MESSAGES[opcode][1]

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
    msg = protocol.HeartbeatMessage(1, 2, 3, 4)
    data_bytes = struct.pack(byte_def, *msg)


t_end = time.monotonic_ns()
t_elapsed = (t_end - t_start) / 1e6
t_pack = t_elapsed / iterations
print(f"pack: {t_pack:.3f} ms")

# --------parse--------
gc.collect()
msg = protocol.HeartbeatMessage(1, 2, 3, 4)
msg_id = protocol.generate_message_id(node_id, opcode)

t_start = time.monotonic_ns()
for _ in range(iterations):
    msg2 = protocol.unpack(opcode, b"\x01\x02\x03\x04")

t_end = time.monotonic_ns()
t_elapsed = (t_end - t_start) / 1e6
t_parse = t_elapsed / iterations
print(f"parse: {t_parse:.3f} ms")


# --------parse direct  --------

gc.collect()

t_start = time.monotonic_ns()
for _ in range(iterations):
    msg2 = protocol.HeartbeatMessage(*struct.unpack(byte_def, b"\x01\x02\x03\x04"))

t_end = time.monotonic_ns()
t_elapsed = (t_end - t_start) / 1e6
t_parse = t_elapsed / iterations
print(f"parse-direct: {t_parse:.3f} ms")
