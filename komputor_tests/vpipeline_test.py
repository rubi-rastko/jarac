import sys
import unittest

from multijarac.src.mj import (
    ctz, 
    mj_dir,
    mj_exec, 
    mj_load, 
    mj_dump,
    mj_bios
)
from multijarac.src.mjas import (
    mj_compile,
    mj_assemble,
    mj_linker
)

from multijarac.src.mjconf import *

class Test_MultiJarac(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.SOURCE_CODE = "multijarac/multijarac_tests/srctest.vmt"
        cls.BOOT_DISK_PATH = "multijarac/multijarac_tests/srctest.vmt.cc.o.mjx"
        cls.testmem = []
        cls.teststate = dict()
        super().setUpClass()

    def setUp(self):
        self.testmem = [0] * 256
        self.teststate = dict(RN=0, ARM=0, PRM=0, XN=[0]*15, BN=0, AK=0)

    def tearDown(self):
        self.testmem = [0] * 256
        self.teststate = dict(RN=0, ARM=0, PRM=0, XN=[0]*15, BN=0, AK=0)

    def test_mj_ctz(self):
        """Check generic CTZ routine works.
        """
        # There are 12 trailing zeros in 0x3000
        self.assertEqual(ctz(0x10003000), 12)   

    def test_mj_instruction_enum(self):
        """Sanity check on instruction set enum.
        """
        self.assertEqual(opcode.ADD, 1)
        self.assertEqual(mnemonics[opcode.ADD], "ADD")

    def test_mj_halt_instruction(self):
        """Check execution halts on HALT instruction.
        """
        # NOTE bytes() from int needs an ITERABLE of ints (bytes([int[int...]]))
        # bytes(int) only initializes a byte object of size int (aka b'\x00')!
        self.testmem[0 + OFFSET_CODE] = int.from_bytes(
            b'\x01\x00\x00' + bytes([opcode.ADD]), 'little')
        self.testmem[1 + OFFSET_CODE] = int.from_bytes(
            b'\x01\x00\x00' + bytes([opcode.HLT]), 'little')
        mj_dump(self.testmem, 2)

        # Assert mj_exec returns SUCCESS (0)
        # TODO if HLT doesn't stop execution
        # this test won't be valid
        self.assertEqual(mj_exec(self.testmem, self.teststate), 0) 

    def test_mj_execution(self):
        """Check VM handles complete instruction set.
        """
        all_opcodes = range(1, len(mnemonics))        
        addrcounter = 0

        for o in all_opcodes:
            if (o not in [opcode.JMP, opcode.JNE, opcode.JZE, opcode.TRS]):
                self.testmem[addrcounter] = int.from_bytes(
                    b'\x01\x00\x00' + bytes([o]), 'little'
                )
                addrcounter += 1
        
        self.assertEqual(mj_exec(self.testmem, self.teststate), 0)
            

    def test_mj_mnemonics(self):
        """Check mnemonics array correspond to opcode enum.
        """

        self.assertEqual(mnemonics[opcode.MUL], "MUL")

    def test_mj_instruction_decoder(self):
        """Check instruction decoder masking.
        """
        n = 0x10203040
        addr = mj_dir(n, MASK_ADDRESS)

        # Decoded instruction address must be 0x10203040 & 0x0000FFFF
        self.assertEqual(addr, 0x3040)

    def test_mj_decode_is_instr(self):
        """Check instruction decoder instruction masking.
        """
        n = 0x08000001
        instr = mj_dir(n, MASK_INSTR)

        # Decoded instruction must be non-zero for valid instruction
        self.assertNotEqual(instr, 0)

    def test_mj_decode_is_data(self):
        """Check instruction decoder with static data.
        """
        n = 0x00000001
        instr = mj_dir(n, MASK_INSTR)

        # Decoded instruction must be 0 for static data
        self.assertEqual(instr, 0)

    def test_mj_instr_mov(self):
        """Check data after moving between registers and mem.
        """
        n = int.from_bytes(b'\x01\x00\xFF\xFF', 'little') # NOTE equiv to 0xFFFF0001
        addr = mj_dir(n, MASK_ADDRESS) + OFFSET_DATA
        self.testmem[addr] = 24
        self.teststate["AK"] = self.testmem[addr]

        self.assertEqual(self.teststate["AK"], 24)

        # TODO test ALL instructions separately
        # FIXME this test should call the actual MOV instr

    def test_mj_load(self):
        """Check if program loader maps memory correctly.
        """
        testmem = [0] * 256
        
        with open("multijarac/multijarac_tests/srctest.vmt.cc.o.mjx", "r+b") as xf:
            mj_load(testmem, xf)

        # Code byte at OFFSET_CODE must be a valid instruction
        self.assertNotEqual(testmem[OFFSET_CODE], 0)       

    def test_mj_compile(self):
        mj_compile(self.SOURCE_CODE)
        pass

    def test_mj_assemble(self):
        mj_assemble(self.SOURCE_CODE + ".cc")
        pass

    def test_mj_link(self):
        mj_linker(self.SOURCE_CODE + ".cc.o")
        # assert files exist
        pass

    def test_multijarac_pipeline_and_exec(self):
        """Test execution pipeline using test binary executable.
        """        
        # test execution
        with open(self.BOOT_DISK_PATH, "r+b") as vrom:
            mj_load(self.testmem, vrom)
            mj_exec(self.testmem, self.teststate)
        
        # assert acc register has value which srctest.vmt 
        # program should yield, after execution
        self.assertEqual(self.teststate["AK"], 794)
