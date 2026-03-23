"""
Test suite for the ALU (tinymoa_alu)
- add_basic
- add_carry_propagation
- add_overflow_wrap
- sub_basic
- sub_borrow_propagation
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
- czero_eqz
- czero_nez
- carry_chain_across_nibbles
- cmp_out_accumulation_across_nibbles
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    dut.opcode.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.c_in.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def compute_alu_loop(dut, opcode, iterations=100):
    """Loop multiple ALU operations with randomised inputs to stress-test carry/compare chains."""
    dut.opcode.value = opcode
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    c = random.randint(0, 1)
    dut.a_in.value = a
    dut.b_in.value = b
    dut.c_in.value = c
    await ClockCycles(dut.clk, 1)

    results = []
    for _ in range(iterations):
        await ClockCycles(dut.clk, 7)
        next_a = random.randint(0, 0xFFFFFFFF)
        next_b = random.randint(0, 0xFFFFFFFF)
        next_c = random.randint(0, 1)

        dut.a_in.value = next_a
        dut.b_in.value = next_b
        dut.c_in.value = next_c
        await ClockCycles(dut.clk, 1)
        results.append((int(dut.result.value), int(a), int(b), int(c)))
        a, b, c = next_a, next_b, next_c
    return results


async def compute_alu(dut, opcode, a, b, c=0):
    """Run a single ALU instruction"""
    dut.opcode.value = opcode
    dut.a_in.value = a & 0xFFFFFFFF
    dut.b_in.value = b & 0xFFFFFFFF
    dut.c_in.value = c & 0x1
    await ClockCycles(dut.clk, 1 + 8)  # 1 load, 8 compute

    return (int(dut.result.value), int(dut.c_out.value), int(dut.cmp_out.value))


# === ADD ===


@cocotb.test()
async def add_basic(dut):
    await setup(dut)
    for result, a, b, c in await compute_alu_loop(dut, 0b0000):
        expected = (a + b + c) & 0xFFFFFFFF
        assert result == expected, (
            f"{hex(a)} + {hex(b)} + {hex(c)}: expected {hex(expected)}, got {hex(result)}"
        )


@cocotb.test()
async def add_carry_propagation(dut):
    """0xFFFFFFFF + 1 = 0 with c_out=1"""
    await setup(dut)
    result, c_out, _ = await compute_alu(dut, 0b0000, 0xFFFFFFFF, 0x1)
    assert result == 0, f"expected 0, got {hex(result)}"
    assert c_out == 1


@cocotb.test()
async def add_overflow_wrap(dut):
    """0x7FFFFFFF + 1 = 0x80000000: signed overflow, no carry"""
    await setup(dut)
    result, c_out, _ = await compute_alu(dut, 0b0000, 0x7FFFFFFF, 0x1)
    assert result == 0x80000000, f"expected 0x80000000, got {hex(result)}"
    assert c_out == 0


# === SUB ===


@cocotb.test()
async def sub_basic(dut):
    await setup(dut)
    for result, a, b, c in await compute_alu_loop(dut, 0b1000):
        expected = (a - b + c - 1) & 0xFFFFFFFF
        assert result == expected, (
            f"{hex(a)} - {hex(b)} + {hex(c)} - 1: expected {hex(expected)}, got {hex(result)}"
        )


@cocotb.test()
async def sub_borrow_propagation(dut):
    """0 - 1 = 0xFFFFFFFF: borrow ripples across all 8 nibbles"""
    await setup(dut)
    result, _, _ = await compute_alu(dut, 0b1000, 0x0, 0x1, c=0x1)
    assert result == 0xFFFFFFFF, f"expected 0xFFFFFFFF, got {hex(result)}"


@cocotb.test()
async def sub_negative_result(dut):
    """a - b where a < b: result is correct signed negative"""
    await setup(dut)
    a = random.randint(0, 0x7FFFFFFE)
    b = random.randint(a + 1, 0x7FFFFFFF)
    result, _, _ = await compute_alu(dut, 0b1000, a, b, c=0x1)
    expected = (a - b) & 0xFFFFFFFF
    assert result == expected, (
        f"{hex(a)} - {hex(b)}: expected {hex(expected)}, got {hex(result)}"
    )


# === AND / OR / XOR ===


@cocotb.test()
async def and_basic(dut):
    await setup(dut)
    for result, a, b, c in await compute_alu_loop(dut, 0b0111):
        assert result == a & b, (
            f"{hex(a)} & {hex(b)}: expected {hex(a & b)}, got {hex(result)}"
        )


@cocotb.test()
async def or_basic(dut):
    await setup(dut)
    for result, a, b, c in await compute_alu_loop(dut, 0b0110):
        assert result == a | b, (
            f"{hex(a)} | {hex(b)}: expected {hex(a | b)}, got {hex(result)}"
        )


@cocotb.test()
async def xor_basic(dut):
    await setup(dut)
    for result, a, b, c in await compute_alu_loop(dut, 0b0100):
        assert result == a ^ b, (
            f"{hex(a)} ^ {hex(b)}: expected {hex(a ^ b)}, got {hex(result)}"
        )


@cocotb.test()
async def bitwise_all_zeros(dut):
    """AND / OR / XOR against zero boundary operand"""
    await setup(dut)
    a = random.randint(1, 0xFFFFFFFF)
    r, _, _ = await compute_alu(dut, 0b0111, a, 0x0)
    assert r == 0, f"AND with 0: {hex(r)}"
    r, _, _ = await compute_alu(dut, 0b0110, 0x0, 0x0)
    assert r == 0, f"OR 0|0: {hex(r)}"
    r, _, _ = await compute_alu(dut, 0b0100, a, a)
    assert r == 0, f"XOR a^a: {hex(r)}"


@cocotb.test()
async def bitwise_all_ones(dut):
    """AND / OR / XOR against 0xFFFFFFFF boundary operand"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    r, _, _ = await compute_alu(dut, 0b0111, a, 0xFFFFFFFF)
    assert r == a, f"AND all-ones identity: {hex(r)}"
    r, _, _ = await compute_alu(dut, 0b0110, 0x0, 0xFFFFFFFF)
    assert r == 0xFFFFFFFF, f"OR with all-ones: {hex(r)}"
    r, _, _ = await compute_alu(dut, 0b0100, 0xFFFFFFFF, 0xFFFFFFFF)
    assert r == 0, f"XOR all-ones^all-ones: {hex(r)}"


# === SLT / SLTU ===


@cocotb.test()
async def slt_positive_less_than(dut):
    """SLT: positive a < positive b gives cmp_out=1"""
    await setup(dut)
    a = random.randint(0, 0x3FFFFFFE)
    b = random.randint(a + 1, 0x3FFFFFFF)
    _, _, cmp_out = await compute_alu(dut, 0b0010, a, b, c=0x1)
    assert cmp_out == 1, f"SLT {hex(a)} < {hex(b)}: expected 1, got {cmp_out}"


@cocotb.test()
async def slt_negative_less_than(dut):
    """SLT: negative a < positive b gives cmp_out=1"""
    await setup(dut)
    a = random.randint(0x80000000, 0xFFFFFFFF)
    b = random.randint(0, 0x7FFFFFFF)
    _, _, cmp_out = await compute_alu(dut, 0b0010, a, b, c=0x1)
    assert cmp_out == 1, f"SLT {hex(a)} < {hex(b)}: expected 1, got {cmp_out}"


@cocotb.test()
async def slt_equal(dut):
    """SLT: a == b gives cmp_out=0"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    _, _, cmp_out = await compute_alu(dut, 0b0010, a, a, c=0x1)
    assert cmp_out == 0, f"SLT {hex(a)} == {hex(a)}: expected 0, got {cmp_out}"


@cocotb.test()
async def sltu_unsigned_compare(dut):
    """SLTU: random unsigned comparison verified against Python reference"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    _, _, cmp_out = await compute_alu(dut, 0b0011, a, b, c=0x1)
    expected = 1 if a < b else 0
    assert cmp_out == expected, (
        f"SLTU {hex(a)} < {hex(b)}: expected {expected}, got {cmp_out}"
    )


# === CZERO ===


@cocotb.test()
async def czero_eqz(dut):
    """CZERO.EQZ: result is pass-through of a_in"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    result, _, _ = await compute_alu(dut, 0b1110, a, b)
    assert result == a, f"CZERO.EQZ: expected {hex(a)}, got {hex(result)}"


@cocotb.test()
async def czero_nez(dut):
    """CZERO.NEZ: result is pass-through of a_in"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    b = random.randint(0, 0xFFFFFFFF)
    result, _, _ = await compute_alu(dut, 0b1111, a, b)
    assert result == a, f"CZERO.NEZ: expected {hex(a)}, got {hex(result)}"


# === Carry / compare chain ===


@cocotb.test()
async def carry_chain_across_nibbles(dut):
    """Carry propagates across all 8 nibbles: 0xFFFFFFF0 + 0x10 = 0 with c_out=1"""
    await setup(dut)
    result, c_out, _ = await compute_alu(dut, 0b0000, 0xFFFFFFF0, 0x00000010)
    assert result == 0, f"expected 0, got {hex(result)}"
    assert c_out == 1, f"carry-out expected 1, got {c_out}"


@cocotb.test()
async def cmp_out_accumulation_across_nibbles(dut):
    """EQ via XOR: cmp_out=1 iff all nibbles equal, single-bit diff detected"""
    await setup(dut)
    a = random.randint(0, 0xFFFFFFFF)
    _, _, cmp_out = await compute_alu(dut, 0b0100, a, a)
    assert cmp_out == 1, f"a==a: expected 1, got {cmp_out}"
    await ClockCycles(dut.clk, 7)  # re-align nibble_ct to 0 before next operation
    b = a ^ (1 << random.randint(0, 31))
    _, _, cmp_out = await compute_alu(dut, 0b0100, a, b)
    assert cmp_out == 0, f"a!=b (1-bit diff): expected 0, got {cmp_out}"
