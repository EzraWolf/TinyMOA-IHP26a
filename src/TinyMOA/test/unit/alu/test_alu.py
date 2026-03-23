"""
ALU unit tests (tinymoa_alu, 32-bit combinational).

Full test list:
- add_basic
- add_overflow_wrap

- sub_basic
- sub_negative_result

- and_basic
- or_basic
- xor_basic
- bitwise_all_zeros
- bitwise_all_ones

- slt_positive_less_than
- slt_negative_less_than
- slt_equal
- sltu_unsigned_compare

- sll_basic
- sll_by_zero
- sll_by_thirtyone
- srl_basic
- srl_zero_fill
- sra_positive
- sra_negative_sign_extend

- mul_basic
- mul_zero
- mul_max

- czero_eqz_b_zero
- czero_eqz_b_nonzero
- czero_nez_b_zero
- czero_nez_b_nonzero
"""

import random
import cocotb
from cocotb.triggers import Timer


ADD = 0b0000
SUB = 0b0001
SLT = 0b0010
SLTU = 0b0011
XOR = 0b0100
OR = 0b0101
AND = 0b0110
SLL = 0b1000
SRL = 0b1001
SRA = 0b1010
MUL = 0b1011
CZERO_EQZ = 0b1110
CZERO_NEZ = 0b1111


async def alu(dut, opcode, a, b):
    dut.opcode.value = opcode
    dut.a_in.value = a & 0xFFFFFFFF
    dut.b_in.value = b & 0xFFFFFFFF
    await Timer(1, units="ns")
    return int(dut.result.value)


def s32(v):
    v &= 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000


# === ADD ===


@cocotb.test()
async def add_basic(dut):
    for _ in range(20):
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(0, 0xFFFFFFFF)
        r = await alu(dut, ADD, a, b)
        assert r == (a + b) & 0xFFFFFFFF, f"{hex(a)} + {hex(b)}: got {hex(r)}"


@cocotb.test()
async def add_overflow_wrap(dut):
    assert await alu(dut, ADD, 0xFFFFFFFF, 0x1) == 0


# === SUB ===


@cocotb.test()
async def sub_basic(dut):
    for _ in range(20):
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(0, 0xFFFFFFFF)
        r = await alu(dut, SUB, a, b)
        assert r == (a - b) & 0xFFFFFFFF, f"{hex(a)} - {hex(b)}: got {hex(r)}"


@cocotb.test()
async def sub_negative_result(dut):
    assert await alu(dut, SUB, 0, 1) == 0xFFFFFFFF


# === BITWISE ===


@cocotb.test()
async def and_basic(dut):
    for _ in range(20):
        a, b = random.randint(0, 0xFFFFFFFF), random.randint(0, 0xFFFFFFFF)
        r = await alu(dut, AND, a, b)
        assert r == a & b


@cocotb.test()
async def or_basic(dut):
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    r = await alu(dut, OR, a, b)
    assert r == a | b


@cocotb.test()
async def xor_basic(dut):
    a = random.randint(0, 0xFFFFFFFF)
    assert await alu(dut, XOR, a, a) == 0
    assert await alu(dut, XOR, a, 0) == a
    assert await alu(dut, XOR, a, 0xFFFFFFFF) == (~a & 0xFFFFFFFF)


# === SLT / SLTU ===


@cocotb.test()
async def slt_basic(dut):
    assert await alu(dut, SLT, 0, 1) == 1
    assert await alu(dut, SLT, 1, 0) == 0
    assert await alu(dut, SLT, 0, 0) == 0
    # negative < positive
    assert await alu(dut, SLT, 0x80000000, 0x7FFFFFFF) == 1
    # positive not < negative
    assert await alu(dut, SLT, 0x7FFFFFFF, 0x80000000) == 0


@cocotb.test()
async def sltu_basic(dut):
    assert await alu(dut, SLTU, 0, 1) == 1
    assert await alu(dut, SLTU, 1, 0) == 0
    assert await alu(dut, SLTU, 0, 0) == 0
    # 0x80000000 is large unsigned
    assert await alu(dut, SLTU, 0x7FFFFFFF, 0x80000000) == 1
    assert await alu(dut, SLTU, 0x80000000, 0x7FFFFFFF) == 0


# === SHIFTS ===


@cocotb.test()
async def sll_basic(dut):
    assert await alu(dut, SLL, 1, 0) == 1
    assert await alu(dut, SLL, 1, 1) == 2
    assert await alu(dut, SLL, 1, 31) == 0x80000000
    assert await alu(dut, SLL, 0xFFFFFFFF, 1) == 0xFFFFFFFE
    for _ in range(20):
        a = random.randint(0, 0xFFFFFFFF)
        sh = random.randint(0, 31)
        r = await alu(dut, SLL, a, sh)
        assert r == (a << sh) & 0xFFFFFFFF


@cocotb.test()
async def srl_basic(dut):
    assert await alu(dut, SRL, 0x80000000, 1) == 0x40000000
    assert await alu(dut, SRL, 0xFFFFFFFF, 31) == 1
    for _ in range(20):
        a = random.randint(0, 0xFFFFFFFF)
        sh = random.randint(0, 31)
        r = await alu(dut, SRL, a, sh)
        assert r == (a >> sh) & 0xFFFFFFFF


@cocotb.test()
async def sra_basic(dut):
    # positive: same as SRL
    assert await alu(dut, SRA, 0x40000000, 1) == 0x20000000
    # negative: sign extends
    assert await alu(dut, SRA, 0x80000000, 1) == 0xC0000000
    assert await alu(dut, SRA, 0xFFFFFFFF, 31) == 0xFFFFFFFF
    for _ in range(20):
        a = random.randint(0, 0xFFFFFFFF)
        sh = random.randint(0, 31)
        r = await alu(dut, SRA, a, sh)
        expected = (s32(a) >> sh) & 0xFFFFFFFF
        assert r == expected, (
            f"SRA {hex(a)} >> {sh}: expected {hex(expected)}, got {hex(r)}"
        )


# === MUL (16x16 unsigned -> 32) ===


@cocotb.test()
async def mul_basic(dut):
    assert await alu(dut, MUL, 3, 4) == 12
    assert await alu(dut, MUL, 0, 0xFFFF) == 0
    assert await alu(dut, MUL, 0xFFFF, 0xFFFF) == 0xFFFF * 0xFFFF
    for _ in range(20):
        a = random.randint(0, 0xFFFF)
        b = random.randint(0, 0xFFFF)
        r = await alu(dut, MUL, a, b)
        assert r == a * b, f"{a} * {b}: expected {a * b}, got {r}"


@cocotb.test()
async def mul_zero(dut):
    assert await alu(dut, MUL, 0, 0) == 0
    assert await alu(dut, MUL, 0, 0xFFFF) == 0
    assert await alu(dut, MUL, 0xFFFF, 0) == 0


@cocotb.test()
async def mul_max(dut):
    assert await alu(dut, MUL, 0xFFFF, 0xFFFF) == 0xFFFF * 0xFFFF


# === CZERO ===


@cocotb.test()
async def czero_eqz(dut):
    a = random.randint(1, 0xFFFFFFFF)
    # b == 0: result = 0
    assert await alu(dut, CZERO_EQZ, a, 0) == 0
    # b != 0: result = a
    assert await alu(dut, CZERO_EQZ, a, 1) == a
    assert await alu(dut, CZERO_EQZ, a, 0xFFFFFFFF) == a


@cocotb.test()
async def czero_nez(dut):
    a = random.randint(1, 0xFFFFFFFF)
    # b != 0: result = 0
    assert await alu(dut, CZERO_NEZ, a, 1) == 0
    assert await alu(dut, CZERO_NEZ, a, 0xFFFFFFFF) == 0
    # b == 0: result = a
    assert await alu(dut, CZERO_NEZ, a, 0) == a
