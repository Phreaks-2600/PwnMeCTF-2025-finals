"""
Custom MAC Algorithm
"""

from typing import List
from aes import Block
from os import getenv
from random import randbytes

STATE_SIZE = 4
MEMORY_SIZE = 3
ADDITIONAL_ROUNDS = 10

key_env = getenv("KEY")
if key_env is None:
    key = randbytes(16 * (STATE_SIZE + MEMORY_SIZE))
else:
    key = key_env.encode()
assert len(key) == 16 * (STATE_SIZE + MEMORY_SIZE), "key have wrong size"

def state_permute(state: List[Block]):
    """
    Linear permutation of the state (in place)
    """
    assert len(state) == STATE_SIZE

    new_state = [
        state[0] ^ state[3],
        state[0],
        state[1],
        state[2],
    ]

    # move result in place
    for i in range(STATE_SIZE):
        state[i] = new_state[i]

def state_confuse(state: List[Block]):
    """
    Add confusion to the state using one AES round (in place)
    """
    assert len(state) == STATE_SIZE

    state[0].aes_round()

def memory_mix(message: Block, memory: List[Block]):
    """
    Perform a linear permutation of the memory registers with the input
    message block (in place).

    Returns an other linear permutation of the memory registers and
    the message block to be added to the state.
    """
    assert len(memory) == MEMORY_SIZE

    mix = [
        message,
        memory[1],
        memory[2],
        memory[0] ^ message,
    ]

    new_memory = [
        memory[1],
        memory[2],
        memory[0] ^ message,
    ]

    for i in range(MEMORY_SIZE):
        memory[i] = new_memory[i]

    return mix


def state_add(state: List[Block], round_add: List[Block]):
    """
    Add the linear permutation of the memory registers to the state
    (in place)
    """
    assert len(state) == STATE_SIZE
    assert len(round_add) == STATE_SIZE

    for i in range(STATE_SIZE):
        state[i] = state[i] ^ round_add[i]

def perform_round(state: List[Block], memory: List[Block], message: Block):
    """
    Perform a full round of the MAC
    """
    assert len(state) == STATE_SIZE
    assert len(memory) == MEMORY_SIZE

    state_permute(state)
    state_confuse(state)
    round_add = memory_mix(message, memory)
    state_add(state, round_add)

def tag(message: bytes):
    """
    Generates a MAC tag for the message, using the key as initial state.
    """
    # 1-0 padding
    message += b'\x01'
    while len(message) % 16 != 0:
        message += b'\x00'

    # block-ify message
    message_blocks = [
        Block(message[i:i+16])
        for i in range(0, len(message), 16)
    ]

    # convert key into initial state and memory
    state = [ Block(key[i:i+16]) for i in range(0, 16 * STATE_SIZE, 16) ]
    memory = [ Block(key[i:i+16]) for i in range(16 * STATE_SIZE, 16 * (STATE_SIZE + MEMORY_SIZE), 16) ]

    # perform the MAC
    for i in range(len(message_blocks)):
        perform_round(state, memory, message_blocks[i])

    # additional rounds to ensure proper diffusion
    for _ in range(ADDITIONAL_ROUNDS):
        perform_round(state, memory, Block(b'\x00' * 16))

    # the final state will serve as the authentication tag
    tag = b''.join([block.values for block in state])
    return tag
