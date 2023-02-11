from enum import Enum, IntEnum
import sys
import os
import json
import time
import struct
import socket as ipc

from multijarac.src.mjconf import *

# TODO --- MAJOR ---
#
# TODO remove TODO on done items
# TODO parallel execution
# TODO distributed execution (IPC)
# TODO machine web API
# TODO encryption using CipherSaber (RC420)
# TODO hardware equivalency
# TODO object orientify (carefully!)
# TODO optimize
# TODO readability and reproducibility
# TODO portability (language wise; make it comp lang agnostic)
# TODO imperativefy - minimize ACTUAL function calls (jumps)
# TODO become one with everything


# We MUST reserve real memory for a VM
vmem = [0] * MEMORY_SIZE
# Machine state (currently a dict for 
# compatibility with JSON)
vstate = { 
    "ARM": 0, # type: int # SHORT
    "PRM": 0, # type: int # LONG
    "RN": 0, # type: int # LONG
    "XN": [0] * 15,
    "BN": 0, # type: int # SHORT
    "AK": 0 # type: int # LONG
}

def ctz(v):
    """ Count trailing zeros. 
    
    A low-level boolean function.
    
    Certain integrated chips have a
    specialized instruction for it.

    If you want to use the real one, create a
    separate mj_decode_XXX method, and
    remap mj_decode to use that one.
    """
    n = 0
    x = v

    if (x == 0): return 0x20

    if (not (x & 0x0000FFFF)):
        n += 0x10
        x >>= 0x10

    if (not (x & 0x000000FF)):
        n += 0x08
        x >>= 0x08

    if (not (x & 0x0000000F)):
        n += 0x04
        x >>= 0x04

    if (not (x & 0x00000003)):
        n += 0x02
        x >>= 0x02

    if (not (x & 0x00000001)):
        n += 0x01

    return n

def mj_dir(ireg, mask):
    return (ireg & mask) >> ctz(mask)

def mj_iprepare(memory, state):
    # TODO change these to match names in comments
    # BN = (Instruction) Counter register
    # ARM = Memory (register) address register; where to write
    # PRM = Memory (register) value register; what to write
    # RN = Instruction register
    # XN = Indexing register

    # NOTE state keys must be guaranteed at this point

    # Write count register to mema register
    state["ARM"] = state["BN"] 
    # Write MEMORY[mema] to memv register
    state["PRM"] = memory[state["ARM"]] 
    # Write memv to instr register
    state["RN"] = state["PRM"] 
    
    if (mj_dir(state["RN"], MASK_INDEXED)):                 # If Decode CODE address mode yields Indexed
        idx = mj_dir(state["RN"], MASK_INDEX)
        state["RN"] += state["XN"][idx]                                     #   Write Decode XN[Decode CODE index] to RN incremented
    elif (mj_dir(state["RN"], MASK_RELATIVE)):             # Else If Decode CODE address mode yields RelativeIndexed
        state["RN"] += state["ARM"]                                         # NOTE op-assign

    while (mj_dir(state["RN"], MASK_INDIRECT)):            # While Decode CODE address mode yields Indirect
        state["ARM"] = mj_dir(state["RN"], MASK_ADDRESS)    #   Decode CODE address, Write to ARM
        state["PRM"] = memory[state["ARM"]]                                 # NOTE will raise exception #  Write MEMORY[ARM] to PRM
        state["RN"] &= MASK_INSTR                                           # NOTE bitop-assign #  Write RN & CODE instruction to RN # (but clear address)
        state["RN"] += state["PRM"] & 0x00FFFFFF                            #   Write PRM & 0x00FFFFFF to RN incremented
    
        if (mj_dir(state["RN"], MASK_INDEXED)):             # If Decode CODE address mode yields Indexed
            idx = mj_dir(state["RN"], MASK_INDEX)
            state["RN"] += state["XN"][idx]                                 #   Write Decode XN[Decode CODE index] to RN incremented
        elif (mj_dir(state["RN"], MASK_RELATIVE)):         # Else If Decode CODE address mode yields RelativeIndexed
            state["RN"] += state["ARM"]                                     # NOTE op-assign

    # Increment BN
    state["BN"] += 1 
    
    # TODO Set clock to downtick (TODO clock)
    
    return 0


def mj_iexecute(mem, state):
    # NOTE state keys must be guaranteed at this point
    instr = mj_dir(state["RN"], MASK_INSTR)
    addr = mj_dir(state["RN"], MASK_ADDRESS)

    # Switch on I # PERF python doesn't have switch    
    if (instr == opcode.HLT):
        return 0
    elif (instr == opcode.ADD): # arithmetic -----------------------
        state["AK"] += mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.SUB):
        state["AK"] -= mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.MUL):
        state["AK"] *= mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.DIV):
        state["AK"] /= mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.ADF): # TODO floating point arithmetic ---
        state["AK"] += mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.SUF):
        state["AK"] -= mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.MVA): # Read from memory -----------------
        state["AK"] = mem[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.MVM): # Write to memory ------------------
        mem[addr] = state["AK"]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.CLR): # Clear acc register ---------------
        state["AK"] = 0x0
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.NEG): # Invert acc register --------------
        state["AK"] = -state["AK"] # FIXME Syntax, style
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.JNE): # Conditional jump (acc < 0) -------
        if (state["AK"] < 0x0):
            state["BN"] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.JZE): # Conditional jump (acc == 0) ------
        if (state["AK"] == 0x0):
            state["BN"] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.JMP): # Unconditional jump ---------------
        state["BN"] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.IDX): # Indexed memory address -----------
        idx = mj_dir(state["RN"], MASK_INDEX)
        state["XN"][idx] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == opcode.TRS): # Subroutine (Jump + Decode) -------
        state["RN"] = state["RN"] & (0xFFFF0000 + state["BN"])
        state["BN"] = 0x1 + addr
        return 1 # NOTE in place of switch BREAK!
    else: # illegal instruction ------------------------------------        
        return -1

    # TODO Set clock to uptick (TODO clock)
    
    return 1

def mj_dump(memory, blocksize):
    # TODO use the logger
    instr = None
    segment = max(4096, blocksize)
    sout = ""

    # For A in range DATA offset, blocksize
    for i in range(OFFSET_DATA, OFFSET_DATA + segment):
        #   Write A, MEMORY[A] to output
        sout += (
            ' %(addr)04X:   %(val)08X\n' %
            { "addr": i, "val": memory[i] }
        )

    # For A in range 0, blocksize
    for i in range(0, segment):
        #   Decode instruction and paramater address
        instr = mj_dir(memory[i], MASK_INSTR)
        caddr = mj_dir(memory[i], MASK_ADDRESS)
        
        #   Write A+CODE offset, instruction mnemonic, instruction address 
        sout += (
            ' %(addr)04X: %(instr)3.3s 0x%(caddr)04X\n' %
            { 
                "addr": OFFSET_CODE + i,
                "instr": mnemonics[instr],
                "caddr": caddr
            }
        )
        
    return sout


def mj_load(mem, fd):
    # TODO This should be a native program
    # TODO Read from IPC socket?
    cbytes = 0
    dbytes = 0

    # The role of the program loader is to
    # work around a catch-22 where the program
    # itself should not be able to load other
    # programs; this might seem drastic, but
    # we are not implementing a file system yet
    # so there is no instruction for storage
    # manipulation - the environment must do this!
    # That said, the instruction set is made
    # purposely extensible; as we refine the
    # VM we can tweak the depth of control
    # the machine has over programs, i.e.
    # make binaries more self-sufficient
    
    codebytebuf = fd.read(4)

    # While (Read instruction yields)
    while (codebytebuf != b''): 
        # Normalize instruction endianness
        codebytebuf = int.from_bytes(codebytebuf, 'little')

        # If (Decode instruction yields DATA)
        if (mj_dir(codebytebuf, MASK_INSTR) == 0):            
            #           Commit DATA to memory starting at DATA offset
            mem[OFFSET_DATA + dbytes] = codebytebuf
            #           Increment DATA unit counter
            dbytes += 1
            #           Else (yields CODE)
        else:
            #           Commit CODE to memory starting at CODE offset
            mem[0 + cbytes] = codebytebuf
            #           Increment CODE unit counter
            cbytes += 1
            
        codebytebuf = fd.read(4)

    # Return sum of DATA and CODE counters
    return cbytes + dbytes

def mj_exec(mem, state):
    # Prepare next instruction
    mj_iprepare(mem, state)

    # While (Execute instruction success)
    while(mj_iexecute(mem, state) > 0): # NOTE > 0 signals we are using a RANGE of return codes
        # Prepare next instruction
        mj_iprepare(mem, state)

    return 0;

def mj_bios(mem, state, romfd): # NOTE should also be a native routine
    """ A BIOS-like routine.
    
    Currently just executes a piece of code directly.
    """
    # NOTE "BYTE" IS USED GENERICALLY
    # IT MAY OR MAY NOT REPRESENT AN OCTET OF BITS

    n_bytes = mj_load(mem, romfd)
    mj_dump(mem, n_bytes)
    mj_exec(mem, state)

if __name__ == "__main__":
    try:
        BOOT_INIT_PROGRAM = sys.argv[1]
    except Exception as exc:
        raise Exception(exc)

    with open(BOOT_INIT_PROGRAM, "r+b") as vrom:
        mj_bios(vmem, vstate, vrom)
        sys.stderr.write(str(vstate))
