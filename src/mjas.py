import os
import socket
import struct
import sys

from multijarac.src.mjconf import *

def get_opcode(mnemonic, itable):
    return itable.index(mnemonic) * 0x1000000

def precedence(
    op, 
    oplist # type: list
):
    for op_set in oplist:
        for o in op_set:
            if (o == op):
                return oplist.index(op_set)

    return 0

def shuntingyard(   # type: int
    xi, # type: str # FIXME NAME
    ol  # FIXME NAME
):
    so = [" "] # FIXME NAME
    xo = "" # FIXME NAME
    last_op = ""

    for a in xi:
        if (a.isalnum()):
            xo += " " + a
        elif (a in ["*", "/", "+", "-"]):
            if (so):
                last_op = so[-1]

            while (
                (
                    precedence(a, ol) == precedence(last_op, ol) or
                    precedence(a, ol) > precedence(last_op, ol)
                ) and last_op != "("
            ):
                xo += " " + last_op

                if (so):
                    so.pop()

                    if (so):
                        last_op = so[-1]
            
            so.append(a)
        elif (a in ["("]):
            so.append(a)
        elif (a in [")"]):
            if (so):
                last_op = so[-1]           

            while (last_op != "("):
                xo += " " + last_op                

                if (so):
                    so.pop()
                    if (so):
                        last_op = so[-1]

            if (so):
                so.pop()
    if (so):
        last_op = so[-1]

    while (len(so)):
        xo += " " + last_op
        so.pop()

        if (so):
            last_op = so[-1]

    return xo

def reversepolish(temp, malist, rpnexpr):
    asmops = []
    vrstack = []
    lplh = ""
    rplh = ""

    for tok in rpnexpr:
        if (tok in ["*", "/", "+", "-"]):
            rplh = malist.index(vrstack[-1])
            vrstack.pop()
            lplh = malist.index(vrstack[-1])
            vrstack.pop()

            asmops.append(mnemonics[opcode.MVA] + " " + str(lplh))

            asmops.append(
                [
                    mnemonics[opcode.MUL], 
                    mnemonics[opcode.DIV], 
                    mnemonics[opcode.ADD], 
                    mnemonics[opcode.SUB]
                ][
                    ["*", "/", "+", "-"].index(tok)
                ] + " " + str(rplh)
            )
            asmops.append(mnemonics[opcode.MVM] + " " + str(malist.index(temp)))
            vrstack.append(temp)
        elif (str(tok).isalpha()):
            vrstack.append(tok)
        elif (str(tok).isnumeric()):
            asmops.append(tok)
            vrstack.append(tok)

    return asmops


def tokenize(statement, malist, oplist, fd):
    ma = malist

    t = ""
    texpr = ""
    lefthand = ""
    righthand = ""

    t = statement
    texpr = str(t).split("=")
    lefthand = ''.join([c for c in texpr[0] if c.isalpha()])
    righthand = texpr[1]

    try:
        ma.index(lefthand)
    except ValueError as exc:     
        ma.append(lefthand)

    for oto in reversepolish(lefthand, ma, shuntingyard(righthand, oplist)):
        fd.write(oto + "\n")


def mj_compile(sourcepath):
    # --- COMPILER ---
    # https://open.spotify.com/track/5oD2Z1OOx1Tmcu2mc9sLY2?si=561abda035bc4c6a
    memory_map = []

    # operator precedence
    op_list = [
        ["*", "/"],
        ["+", "-"],
        [" "]
    ]

    with open(sourcepath, "r") as cin, open(f'{sourcepath}.cc', "w") as cout:
        # ident -> address (offset)

        statement = cin.readline()
        
        while (statement):
            tokenize(statement, memory_map, op_list, cout)
            statement = cin.readline()

        cout.write("HLT 0\n")


def mj_assemble(sourcepath):
    # --- ASSEMBLER ---
    # OPCODE := INTEGER
    # ADDRESS := INTEGER
    # CONSTANT := INTEGER
    # INSTRUCTION := OPCODE ADDRESS
    # if line starts with alpha, it's an instruction
    # else if line starts with numeric, it's a constant (data)

    asmascii = ""

    with open(sourcepath, "r") as cin, open(f'{sourcepath}.o', "w+b") as bout:
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
                            get_opcode(mnemonic, mnemonics) +
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
    absolute_xset = 0 # type: int
    bufsize = 4

    with (
        open(objectpath, "r+b") as buf_in, 
        open(f'{objectpath}.mjx', "w+b") as bout
    ):
        instr = buf_in.read(4)

        while(instr):
            instr = int.from_bytes(instr, 'little') 
            
            bout.write(
                struct.pack( # NOTE must use pack to handle multibyte values
                    "I", # must be 32-bits
                    instr + absolute_xset
                )
            )
            
            if (instr == data_separator):
                absolute_xset = OFFSET_DATA

            instr = buf_in.read(bufsize)

if __name__ == "__main__":
    # TODO cleanup intermediary files
    
    try:
        source_code = sys.argv[1]

        mj_compile(source_code)
        mj_assemble(source_code + ".cc")
        mj_linker(source_code + ".cc.o")
    except Exception as exc:
        print(f"\tERROR ----\n{exc}")
        
