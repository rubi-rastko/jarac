import os
import socket
import struct
import sys
import logging 
from src.komputor_conf import *

def opcode( mnemonic, itable ):
    return itable.index(mnemonic) * 0x1000000

def prec( op, opconfig ):
    """Get level of operator in operator sets configuration.
    """
    for oplevel in opconfig:        
        if (op in oplevel):
            return opconfig.index(oplevel)

    return 0

def postfix( infix, opconfig ):
    stack = [" "]
    expression = ""
    last = ""

    for symbol in infix:
        if (symbol.isalnum()):
            expression += " " + symbol
        elif (symbol in ["*", "/", "+", "-"]):
            if (stack):
                last = stack[-1]
                #last = stack.pop()

            while (
                (
                    prec(symbol, opconfig) == prec(last, opconfig) or
                    prec(symbol, opconfig) > prec(last, opconfig)
                ) and last != "("
            ):
                expression += " " + last

                if (stack):
                    stack.pop()
                    #last = stack.pop()

                    if (stack):
                        last = stack[-1]
            
            stack.append(symbol)
        elif (symbol in ["("]):
            stack.append(symbol)
        elif (symbol in [")"]):
            if (stack):
                last = stack[-1]
                #last = stack.pop()

            while (last != "("):
                expression += " " + last                

                if (stack):
                    stack.pop()
                    #last = stack.pop()
                    
                    if (stack):
                        last = stack[-1]

            if (stack):
                stack.pop()

    if (stack):
        last = stack[-1]
        #last = stack.pop()

    while (len(stack)):
        expression += " " + last
        stack.pop()

        if (stack):
            last = stack[-1]

    return expression

def asm(temp, memmap, expression):
    asm = []
    stack = []
    lplh = ""
    rplh = ""

    for t in expression:
        if (t in ["*", "/", "+", "-"]):
            rplh = memmap.index(stack[-1])
            stack.pop()
            lplh = memmap.index(stack[-1])
            stack.pop()
            asm.append(OPMNEM[OPENUM.MVA] + " " + str(lplh))
            asm.append(
                [
                    OPMNEM[OPENUM.MUL], 
                    OPMNEM[OPENUM.DIV], 
                    OPMNEM[OPENUM.ADD], 
                    OPMNEM[OPENUM.SUB]
                ][
                    ["*", "/", "+", "-"].index(t)
                ] + " " + str(rplh)
            )
            asm.append(OPMNEM[OPENUM.MVM] + " " + str(memmap.index(temp)))
            stack.append(temp)
        elif (str(t).isalpha()):
            stack.append(t)
        elif (str(t).isnumeric()):
            asm.append(t)
            stack.append(t)

    return asm


def tokenize(statement, memmap, opconfig):
    """Tokenize is the HLL syntax processor, and also its
    definition/reference implementation.
    """
    mmap = memmap
    expression = ""
    lhand = ""
    rhand = ""
    output = ""

    
    expression = str(statement).split("=")
    lhand = ''.join([c for c in expression[0] if c.isalpha()])
    rhand = expression[1]

    try:
        mmap.index(lhand)        
    except ValueError as exc:     
        mmap.append(lhand)

    for symbol in asm(lhand, mmap, postfix(rhand, opconfig)):
        output += symbol + "\n"
        
    return output


def mj_compile(sourcepath):
    # --- COMPILER ---
    # https://open.spotify.com/track/5oD2Z1OOx1Tmcu2mc9sLY2?si=561abda035bc4c6a

    memmap = [] # we call this in a loop, so each iteration depends on the accumulation of values!
    expressions = []
    output = ""

    with open(f'{sourcepath}.vmt', "r") as cin:
        # ident -> address (offset)

        statement = cin.readline()
        
        while (statement):
            output += tokenize(statement, memmap, OPERATOR_PRECEDENCE)
            statement = cin.readline()    

    with open(f'{sourcepath}.asm', "w") as cout:
        cout.write( output )
        cout.write("HLT 0\n")


def mj_assemble(sourcepath):
    """Assembler compiles assembly code into machine code.
    """
    # --- ASSEMBLER ---
    # OPCODE := INTEGER
    # ADDRESS := INTEGER
    # CONSTANT := INTEGER
    # INSTRUCTION := OPCODE ADDRESS
    # if line starts with alpha, it's an instruction
    # else if line starts with numeric, it's a constant (data)

    asmascii = ""

    with open(f'{sourcepath}.asm', "r") as cin, open(f'{sourcepath}.o', "w+b") as bout:
        asmascii = cin.readline()

        while (asmascii):
            if (asmascii[0].isalpha()):
                instruction = asmascii.split(" ") # MNEMONIC, ADDRESS
                mnemonic = instruction[0]
                address = instruction[1]

                bout.write(
                    bytes(
                        struct.pack(
                            "I", # TODO byte order
                            opcode(mnemonic, OPMNEM) +
                            int(address)))
                )

            elif (asmascii[0].isnumeric()):
                bout.write(
                    bytes(
                        struct.pack(
                            "I", # TODO byte order
                            int(asmascii)
                        )
                    )               
                )

            asmascii = cin.readline()

def mj_linker(objectpath): 
    # FIXME should go to assembler? 

    # links several objects together!
    # links new programs to existing binary libraries in object form
    # (STATIC) or in executable form (DYNAMIC, DLL)
    # FIXME the below code does not seem to be related
    # to the linking process


    # --- LINKER ---
    data_separator = 0x00000000 # type: int
    absolute_offset = 0 # type: int
    bufsize = 4

    with (
        open(f'{objectpath}.o', "r+b") as buf_in, 
        open(f'{objectpath}.out', "w+b") as bout
    ):
        instr = buf_in.read(4)

        while(instr):
            instr = int.from_bytes(instr, 'little') 
            
            bout.write(
                struct.pack( # NOTE must use pack to handle multibyte values
                    "I", # must be 32-bits
                    instr + absolute_offset
                )
            )
            
            if (instr == data_separator):
                absolute_offset = OFFSET_DATA

            instr = buf_in.read(bufsize)

if __name__ == "__main__":
    # TODO cleanup intermediary files
    
    try:
        source_code = sys.argv[1]

        mj_compile(source_code)
        mj_assemble(source_code)
        mj_linker(source_code)
    except Exception as exc:
        print(f"\tERROR ----\n{exc}")
        
