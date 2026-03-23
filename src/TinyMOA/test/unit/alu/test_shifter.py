"""
Test suite for tinymoa_shifter (combinational barrel shifter).
- sll_by_zero
- sll_by_one
- sll_by_sixteen
- sll_by_thirtyone
- srl_by_one
- srl_by_sixteen
- srl_by_thirtyone
- sra_positive_by_one
- sra_negative_by_one
- sra_negative_by_thirtyone
- nibble_extraction_all_positions
- sll_random
- srl_random
- sra_random
"""

import random
import cocotb
from cocotb.triggers import Timer

SLL = 0b0001
SRL = 0b0101
SRA = 0b1101


async def read_shift(dut, opcode, data, amount):
    """Drive the combinational shifter and return the full 32-bit result
    by reading all 8 nibbles."""
    dut.opcode.value = opcode
    dut.data_in.value = data & 0xFFFFFFFF
    dut.shift_amnt.value = amount & 0x1F
    result = 0
    for n in range(8):
        dut.nibble_ct.value = n
        await Timer(1, units="ns")
        result |= (int(dut.result.value) & 0xF) << (n * 4)
    return result


def sll_ref(data, amount):
    return (data << amount) & 0xFFFFFFFF


def srl_ref(data, amount):
    return (data & 0xFFFFFFFF) >> amount


def sra_ref(data, amount):
    signed = data if data < 0x80000000 else data - 0x100000000
    return signed >> amount & 0xFFFFFFFF


# === SLL ===


@cocotb.test()
async def sll_by_zero(dut):
    """SLL x << 0 = x"""
    data = random.randint(0, 0xFFFFFFFF)
    result = await read_shift(dut, SLL, data, 0)
    assert result == data, (
        f"SLL {hex(data)} << 0: expected {hex(data)}, got {hex(result)}"
    )


@cocotb.test()
async def sll_by_one(dut):
    """SLL x << 1 shifts left one bit"""
    data = random.randint(0, 0xFFFFFFFF)
    result = await read_shift(dut, SLL, data, 1)
    expected = sll_ref(data, 1)
    assert result == expected, (
        f"SLL {hex(data)} << 1: expected {hex(expected)}, got {hex(result)}"
    )


@cocotb.test()
async def sll_by_sixteen(dut):
    """SLL x << 16 moves low halfword to high halfword"""
    data = random.randint(0, 0xFFFF)
    result = await read_shift(dut, SLL, data, 16)
    expected = sll_ref(data, 16)
    assert result == expected, (
        f"SLL {hex(data)} << 16: expected {hex(expected)}, got {hex(result)}"
    )


@cocotb.test()
async def sll_by_thirtyone(dut):
    """SLL x << 31: only bit 0 of x survives, in bit 31"""
    data = random.randint(0, 0xFFFFFFFF)
    result = await read_shift(dut, SLL, data, 31)
    expected = sll_ref(data, 31)
    assert result == expected, (
        f"SLL {hex(data)} << 31: expected {hex(expected)}, got {hex(result)}"
    )


# === SRL ===


@cocotb.test()
async def srl_by_one(dut):
    """SRL x >> 1 zero-extends from MSB"""
    data = random.randint(0x80000000, 0xFFFFFFFF)  # MSB set to confirm zero-fill
    result = await read_shift(dut, SRL, data, 1)
    expected = srl_ref(data, 1)
    assert result == expected, (
        f"SRL {hex(data)} >> 1: expected {hex(expected)}, got {hex(result)}"
    )


@cocotb.test()
async def srl_by_sixteen(dut):
    """SRL x >> 16 moves high halfword to low halfword with zero fill"""
    data = random.randint(0, 0xFFFFFFFF)
    result = await read_shift(dut, SRL, data, 16)
    expected = srl_ref(data, 16)
    assert result == expected, (
        f"SRL {hex(data)} >> 16: expected {hex(expected)}, got {hex(result)}"
    )


@cocotb.test()
async def srl_by_thirtyone(dut):
    """SRL x >> 31: result is 0 or 1 depending on bit 31"""
    data = random.randint(0, 0xFFFFFFFF)
    result = await read_shift(dut, SRL, data, 31)
    expected = srl_ref(data, 31)
    assert result == expected, (
        f"SRL {hex(data)} >> 31: expected {hex(expected)}, got {hex(result)}"
    )


# === SRA ===


@cocotb.test()
async def sra_positive_by_one(dut):
    """SRA on positive value (MSB=0) behaves like SRL"""
    data = random.randint(0, 0x7FFFFFFF)
    result = await read_shift(dut, SRA, data, 1)
    expected = sra_ref(data, 1)
    assert result == expected, (
        f"SRA {hex(data)} >> 1: expected {hex(expected)}, got {hex(result)}"
    )


@cocotb.test()
async def sra_negative_by_one(dut):
    """SRA on negative value (MSB=1) sign-extends from MSB"""
    data = random.randint(0x80000000, 0xFFFFFFFF)
    result = await read_shift(dut, SRA, data, 1)
    expected = sra_ref(data, 1)
    assert result == expected, (
        f"SRA {hex(data)} >> 1: expected {hex(expected)}, got {hex(result)}"
    )


@cocotb.test()
async def sra_negative_by_thirtyone(dut):
    """SRA negative >> 31: all bits become sign bit (0xFFFFFFFF)"""
    data = random.randint(0x80000000, 0xFFFFFFFF)
    result = await read_shift(dut, SRA, data, 31)
    assert result == 0xFFFFFFFF, (
        f"SRA {hex(data)} >> 31: expected 0xFFFFFFFF, got {hex(result)}"
    )


# === Nibble extraction ===


@cocotb.test()
async def nibble_extraction_all_positions(dut):
    """nibble_ct correctly selects each 4-bit slice of the shifted result"""
    data = 0x89ABCDEF
    amount = 4  # SRL by 4: expected = 0x089ABCDE
    expected = srl_ref(data, amount)
    dut.opcode.value = SRL
    dut.data_in.value = data
    dut.shift_amnt.value = amount
    for n in range(8):
        dut.nibble_ct.value = n
        await Timer(1, units="ns")
        exp_nibble = (expected >> (n * 4)) & 0xF
        got = int(dut.result.value)
        assert got == exp_nibble, f"nibble {n}: expected {exp_nibble:x}, got {got:x}"


# === Random stress ===


@cocotb.test()
async def sll_random(dut):
    """SLL: 100 random (data, amount) pairs"""
    for _ in range(100):
        data = random.randint(0, 0xFFFFFFFF)
        amount = random.randint(0, 31)
        result = await read_shift(dut, SLL, data, amount)
        expected = sll_ref(data, amount)
        assert result == expected, (
            f"SLL {hex(data)} << {amount}: expected {hex(expected)}, got {hex(result)}"
        )


@cocotb.test()
async def srl_random(dut):
    """SRL: 100 random (data, amount) pairs"""
    for _ in range(100):
        data = random.randint(0, 0xFFFFFFFF)
        amount = random.randint(0, 31)
        result = await read_shift(dut, SRL, data, amount)
        expected = srl_ref(data, amount)
        assert result == expected, (
            f"SRL {hex(data)} >> {amount}: expected {hex(expected)}, got {hex(result)}"
        )


@cocotb.test()
async def sra_random(dut):
    """SRA: 100 random (data, amount) pairs"""
    for _ in range(100):
        data = random.randint(0, 0xFFFFFFFF)
        amount = random.randint(0, 31)
        result = await read_shift(dut, SRA, data, amount)
        expected = sra_ref(data, amount)
        assert result == expected, (
            f"SRA {hex(data)} >> {amount}: expected {hex(expected)}, got {hex(result)}"
        )
