import struct
import enum

# NOTE must be shared with the assembler/linker
INTERR = lambda: 0xFFFFFFFF # integer value representing a virtual error

MEMORY_SIZE = 16384 # type: int # LONG (minimum CODE length 32 bits!)

OFFSET_RESERVED = 0x0
OFFSET_CODE = 0xA  
OFFSET_DATA = 0x60 
# TODO JSON config?
MASK_INDEXED =  0x00010000
MASK_RELATIVE = 0x00020000
MASK_INDIRECT = 0x00040000
MASK_INDEX =    0x00F00000
MASK_INSTR =    0xFF000000
MASK_ADDRESS =  0x0000FFFF

mnemonics = 'NOP ADD SUB MUL DIV ADF SUF MVA MVM CLR NEG JNE JZE JMP IDX TRS HLT'.split()
opcode = enum.IntEnum(
    'opcode', 
    'ADD SUB MUL DIV ADF SUF MVA MVM CLR NEG JNE JZE JMP IDX TRS HLT'
)
