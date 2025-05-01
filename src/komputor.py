from enum import Enum, IntEnum
import sys
import os
import json
import time
import struct
import socket as ipc

from src.komputor_conf import *

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

def ctz(v):
    """Count trailing zeros. 
    
    A low-level boolean function.

    Generic version as a replacement for
    a hardware instruction (most chips have
    a hardware implementation)   
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

def mj_idecode(ireg, mask):
    """Decode instruction.
    """
    return (ireg & mask) >> ctz(mask)

def mj_iprep(memory, regs):
    """Instruction execution preparation.

    Pulse-clock alternating phase 1 - prepare instruction.
    """
    # NOTE state keys must be guaranteed at this point    
    regs["ARM"] = regs["BN"] # Write count register to mema register    
    regs["PRM"] = memory[regs["ARM"]] # Write MEMORY[mema] to memv register
    regs["RN" ] = regs["PRM"] # Write memv to instr register
    
    if (mj_idecode(regs["RN"], MASK_INDEXED)):                 # If Decode CODE address mode yields Indexed
        idx = mj_idecode(regs["RN"], MASK_INDEX)
        regs["RN" ] += regs["XN"][idx]                                     #   Write Decode XN[Decode CODE index] to RN incremented
    elif (mj_idecode(regs["RN"], MASK_RELATIVE)):             # Else If Decode CODE address mode yields RelativeIndexed
        regs["RN" ] += regs["ARM"]                                         # NOTE op-assign

    while (mj_idecode(regs["RN"], MASK_INDIRECT)):            # While Decode CODE address mode yields Indirect
        regs["ARM"] = mj_idecode(regs["RN"], MASK_ADDRESS)    #   Decode CODE address, Write to ARM
        regs["PRM"] = memory[regs["ARM"]]                                 # NOTE will raise exception #  Write MEMORY[ARM] to PRM
        regs["RN" ] &= MASK_INSTR                                           # NOTE bitop-assign #  Write RN & CODE instruction to RN # (but clear address)
        regs["RN" ] += regs["PRM"] & 0x00FFFFFF                            #   Write PRM & 0x00FFFFFF to RN incremented
    
        if (mj_idecode(regs["RN"], MASK_INDEXED)):             # If Decode CODE address mode yields Indexed
            idx = mj_idecode(regs["RN"], MASK_INDEX)
            regs["RN"] += regs["XN"][idx]                                 #   Write Decode XN[Decode CODE index] to RN incremented
        elif (mj_idecode(regs["RN"], MASK_RELATIVE)):         # Else If Decode CODE address mode yields RelativeIndexed
            regs["RN"] += regs["ARM"]                                     # NOTE op-assign

    # Increment BN
    regs["BN"] += 1 
    
    # TODO Set clock to downtick (TODO clock)
    
    return 0


def mj_iexec(memory, regs):
    """Instruction execution execution.

    Pulse-clock alternating phase 2 - execute instruction.
    """
    # NOTE state keys must be guaranteed at this point
    instr = mj_idecode(regs["RN"], MASK_INSTR)
    addr = mj_idecode(regs["RN"], MASK_ADDRESS)

    # Switch on I # PERF python doesn't have switch    
    if (instr == OPENUM.HLT):
        return 0
    elif (instr == OPENUM.ADD): # arithmetic -----------------------
        regs["AK"] += memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.SUB):
        regs["AK"] -= memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.MUL):
        regs["AK"] *= memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.DIV):
        regs["AK"] /= memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.ADF): # TODO floating point arithmetic ---
        regs["AK"] += memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.SUF):
        regs["AK"] -= memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.MVA): # Read from memory -----------------
        regs["AK"] = memory[addr]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.MVM): # Write to memory ------------------
        memory[addr] = regs["AK"]
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.CLR): # Clear acc register ---------------
        regs["AK"] = 0x0
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.NEG): # Invert acc register --------------
        regs["AK"] = -regs["AK"] # FIXME Syntax, style
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.JNE): # Conditional jump (acc < 0) -------
        if (regs["AK"] < 0x0):
            regs["BN"] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.JZE): # Conditional jump (acc == 0) ------
        if (regs["AK"] == 0x0):
            regs["BN"] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.JMP): # Unconditional jump ---------------
        regs["BN"] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.IDX): # Indexed memory address -----------
        idx = mj_idecode(regs["RN"], MASK_INDEX)
        regs["XN"][idx] = addr
        return 1 # NOTE in place of switch BREAK!
    elif (instr == OPENUM.TRS): # Subroutine (Jump + Decode) -------
        regs["RN"] = regs["RN"] & (0xFFFF0000 + regs["BN"])
        regs["BN"] = 0x1 + addr
        return 1 # NOTE in place of switch BREAK!
    else: # illegal instruction ------------------------------------        
        return -1

    # TODO Set clock to uptick (TODO clock)
    
    return 1 # 1 = success (so far only code)

def mj_dump(memory, nbytes):
    # TODO use the logger
    instr = None
    segment = min(4096, nbytes)
    output_buffer = ""

    for i in range(OFFSET_DATA, OFFSET_DATA + segment): # For A in range DATA offset, blocksize
        output_buffer += ( # Write A, MEMORY[A] to output
            ' %(addr)04X:   %(val)08X\n' %
            { "addr": i, "val": memory[i] }
        )

    for i in range(0, segment): # For A in range 0, blocksize
        instr = mj_idecode(memory[i], MASK_INSTR) #   Decode instruction and paramater address
        caddr = mj_idecode(memory[i], MASK_ADDRESS)
        
        output_buffer += ( # Write A+CODE offset, instruction mnemonic, instruction address 
            ' %(addr)04X: %(instr)3.3s 0x%(caddr)04X\n' %
            { 
                "addr": OFFSET_CODE + i,
                "instr": OPMNEM[instr],
                "caddr": caddr
            }
        )
        
    return output_buffer


def mj_load(memory, fd):
    # TODO This should be a native program
    # TODO Read from IPC socket?
    code_bytes = 0
    data_bytes = 0

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
    
    code_byte = fd.read(4)
    
    while (code_byte != b''): # While (Read instruction yields)
        code_byte = int.from_bytes(code_byte, 'little') # Normalize instruction endianness

        if (mj_idecode(code_byte, MASK_INSTR) == 0): # If (Decode instruction yields DATA)
            memory[OFFSET_DATA + data_bytes] = code_byte # Commit DATA to memory starting at DATA offset            
            data_bytes += 1 # Increment DATA unit counter
        else: # else (yields CODE)
            memory[0 + code_bytes] = code_byte # Commit CODE to memory starting at CODE offset            
            code_bytes += 1 # Increment CODE unit counter
            
        code_byte = fd.read(4)
    
    return code_bytes + data_bytes # Return sum of DATA and CODE counters

def mj_exec(memory, regs):
    mj_iprep(memory, regs) # Prepare next instruction

    while(mj_iexec(memory, regs) > 0): # While (Execute instruction returns success code)
        mj_iprep(memory, regs) # Prepare next instruction

    return 0;

def mj_bios(memory, regs, fd): # NOTE should also be a native routine
    """ A BIOS-like routine.
    
    Currently just executes a piece of code directly.
    """
    # NOTE "BYTE" IS USED GENERICALLY
    # IT MAY OR MAY NOT REPRESENT AN OCTET OF BITS

    nbytes = mj_load(memory, fd)
    mj_dump(memory, nbytes)
    mj_exec(memory, regs)


    
if __name__ == "__main__":    
    machine_memory = [0] * MEMORY_SIZE # We MUST reserve real memory for a VM    
    machine_regs = dict( # Machine state (currently a dict for compatibility with JSON)
        RN=0, # type: int # LONG  # instruction register
        BN=0, # type: int # SHORT # instruction counter register 
        AK=0, # type: int # LONG  # accumulation register 
        ARM=0, # type: int # SHORT # read-from-memory register
        PRM=0, # type: int # LONG  # write-to-memory register
        XN=[0] * 15 # indexed-addressing registers
    )
    
    try:
        BOOT_INIT_PROGRAM = sys.argv[1]
    except Exception as exc:
        raise Exception(exc)

    with open(BOOT_INIT_PROGRAM, "r+b") as vrom:
        mj_bios(machine_memory, machine_regs, vrom)
        sys.stderr.write(str(machine_regs))
