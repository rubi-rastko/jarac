import sys
import unittest


from src.komputor import (
    ctz, 
    mj_idecode as idecode,
    mj_exec, 
    mj_load, 
    mj_dump,
    mj_bios
)

from src.askomputor import (
    mj_compile,
    mj_assemble,
    mj_linker
)

from src.komputor_conf import OPMNEM, OPENUM, MASK_INDIRECT, MASK_INDEX, MASK_RELATIVE, MASK_INDEXED, MASK_INSTR, MASK_ADDRESS, OFFSET_DATA, OFFSET_CODE, OFFSET_RESERVED, INTERR, MEMORY_SIZE

class Test_MultiJarac(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.SOURCE_CODE = "komputor_tests/srctest"
        cls.BOOT_DISK_PATH = "komputor_tests/srctest.out"
        cls.testmem = []
        cls.teststate = dict()
        super().setUpClass()

    def setUp(self):
        self.testmem = [0] * 256
        self.teststate = dict(RN=0, ARM=0, PRM=0, XN=[0]*15, BN=0, AK=0)

    def tearDown(self):
        self.testmem = [0] * 256
        self.teststate = dict(RN=0, ARM=0, PRM=0, XN=[0]*15, BN=0, AK=0)

    def test_ctz(self):
        """Check generic CTZ routine works.
        """
        # There are 12 trailing zeros in 0x3000
        self.assertEqual(
            ctz(0x10003000), 12
        )   

    def test_instr_enum(self):
        """Sanity check on instruction set enum.
        """
        self.assertEqual(OPENUM.ADD, 1)
        self.assertEqual(OPMNEM[OPENUM.ADD], "ADD")

    def test_hlt_instr(self):
        """Check execution halts on HALT instruction.
        """
        # NOTE bytes() from int needs an ITERABLE of ints (bytes([int[int...]]))
        # bytes(int) only initializes a byte object of size int (aka b'\x00')!
        self.testmem[0 + OFFSET_CODE] = int.from_bytes(
            b'\x01\x00\x00' + bytes([OPENUM.ADD]), 'little')
        self.testmem[1 + OFFSET_CODE] = int.from_bytes(
            b'\x01\x00\x00' + bytes([OPENUM.HLT]), 'little')
        mj_dump(self.testmem, 2)

        # Assert mj_exec returns SUCCESS (0)
        # TODO if HLT doesn't stop execution
        # this test won't be valid
        self.assertEqual(mj_exec(self.testmem, self.teststate), 0) 

    def test_instr_exec(self):
        """Check VM handles complete instruction set.
        """
        all_opcodes = range(1, len(OPMNEM))        
        addrcounter = 0

        for o in all_opcodes:
            if (o not in [OPENUM.JMP, OPENUM.JNE, OPENUM.JZE, OPENUM.TRS]):
                self.testmem[addrcounter] = int.from_bytes(
                    b'\x01\x00\x00' + bytes([o]), 'little'
                )
                addrcounter += 1
        
        self.assertEqual(mj_exec(self.testmem, self.teststate), 0)
            

    def test_instr_mnem(self):
        """Check mnemonics array correspond to opcode enum.
        """

        self.assertEqual(OPMNEM[OPENUM.MUL], "MUL")

    def test_instr_dec(self):
        """Check instruction decoder masking.
        """
        n = 0x10203040
        addr = idecode(n, MASK_ADDRESS)

        # Decoded instruction address must be 0x10203040 & 0x0000FFFF
        self.assertEqual(addr, 0x3040)

    def test_instr_mask(self):
        """Check instruction decoder instruction masking.
        """
        n = 0x08000001
        instr = idecode(n, MASK_INSTR)

        # Decoded instruction must be non-zero for valid instruction
        self.assertNotEqual(instr, 0)

    def test_data_mask(self):
        """Check instruction decoder with static data.
        """
        n = 0x00000001
        instr = idecode(n, MASK_INSTR)

        # Decoded instruction must be 0 for static data
        self.assertEqual(instr, 0)

    def test_mov_instr(self):
        """Check data after moving between registers and mem.
        """
        n = int.from_bytes(b'\x01\x00\xFF\xFF', 'little') # NOTE equiv to 0xFFFF0001
        addr = idecode(n, MASK_ADDRESS) + OFFSET_DATA
        self.testmem[addr] = 24
        self.teststate["AK"] = self.testmem[addr]

        self.assertEqual(self.teststate["AK"], 24)

        # TODO test ALL instructions separately
        # FIXME this test should call the actual MOV instr

    def test_code_ingest(self):
        """Check if program loader maps memory correctly.
        """
        testmem = [0] * 256
        
        #mj_compile(f'{self.SOURCE_CODE}')
        #mj_assemble(self.SOURCE_CODE)
        #mj_linker(self.SOURCE_CODE)
        
        with open("komputor_tests/srctest.out", "r+b") as xf:
            mj_load(testmem, xf)

        # Code byte at OFFSET_CODE must be a valid instruction
        self.assertNotEqual(testmem[OFFSET_CODE], 0)       

    def test_compiler(self):
        """Test compilation routine.
        """
        mj_compile(f'{self.SOURCE_CODE}')

    def test_assembler(self):
        """Test assembler routine.
        """
        mj_assemble(self.SOURCE_CODE)

    def test_linker(self):
        """Test linker routine.
        """
        mj_linker(self.SOURCE_CODE)
        # assert files exist

    def test_pipeline(self):
        """Test execution pipeline using test binary executable.
        """        
        # test execution
        with open(self.BOOT_DISK_PATH, "r+b") as vrom:
            mj_load(self.testmem, vrom)
            mj_exec(self.testmem, self.teststate)
        
        # assert acc register has value which srctest.vmt 
        # program should yield, after execution
        self.assertEqual(self.teststate["AK"], 794)
