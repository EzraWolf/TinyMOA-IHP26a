"""
Test suite for tinymoa_multiplier (pipelined signed 16x16->32 multiplier).
TB wraps nibble_ct internally; exposes 32-bit product after 9 clock cycles.
- positive_times_positive
- negative_times_positive
- positive_times_negative
- negative_times_negative
- zero_times_n
- n_times_zero
- max_times_max
- min_times_min
- min_times_max
- one_identity
- minus_one_negate
- random_stress
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


def to_signed32(v):
    """Interpret a raw 32-bit unsigned DUT output as signed."""
    v = v & 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.product.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def multiply(dut, a, b):
    """Drive a and b (Python ints, signed 16-bit range), wait 9 cycles, return signed 32-bit product."""
    dut.a_in.value = a & 0xFFFF
    dut.b_in.value = b & 0xFFFF
    await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 9)
    return to_signed32(int(dut.product.value))


# === Boundary cases ===


@cocotb.test()
async def positive_times_positive(dut):
    """Two positive operands produce a positive product"""
    await setup(dut)
    a = random.randint(1, 0x7FFF)
    b = random.randint(1, 0x7FFF)
    result = await multiply(dut, a, b)
    expected = a * b
    assert result == expected, f"{a} * {b}: expected {expected}, got {result}"


@cocotb.test()
async def negative_times_positive(dut):
    """Negative * positive = negative product"""
    await setup(dut)
    a = random.randint(-32768, -1)
    b = random.randint(1, 0x7FFF)
    result = await multiply(dut, a, b)
    expected = a * b
    assert result == expected, f"{a} * {b}: expected {expected}, got {result}"


@cocotb.test()
async def positive_times_negative(dut):
    """Positive * negative = negative product"""
    await setup(dut)
    a = random.randint(1, 0x7FFF)
    b = random.randint(-32768, -1)
    result = await multiply(dut, a, b)
    expected = a * b
    assert result == expected, f"{a} * {b}: expected {expected}, got {result}"


@cocotb.test()
async def negative_times_negative(dut):
    """Negative * negative = positive product"""
    await setup(dut)
    a = random.randint(-32768, -1)
    b = random.randint(-32768, -1)
    result = await multiply(dut, a, b)
    expected = a * b
    assert result > 0, f"{a} * {b}: expected positive, got {result}"
    assert result == expected, f"{a} * {b}: expected {expected}, got {result}"


@cocotb.test()
async def zero_times_n(dut):
    """0 * n = 0 for any n"""
    await setup(dut)
    b = random.randint(-32768, 32767)
    result = await multiply(dut, 0, b)
    assert result == 0, f"0 * {b}: expected 0, got {result}"


@cocotb.test()
async def n_times_zero(dut):
    """n * 0 = 0 for any n"""
    await setup(dut)
    a = random.randint(-32768, 32767)
    result = await multiply(dut, a, 0)
    assert result == 0, f"{a} * 0: expected 0, got {result}"


@cocotb.test()
async def max_times_max(dut):
    """0x7FFF * 0x7FFF = 1,073,676,289"""
    await setup(dut)
    result = await multiply(dut, 0x7FFF, 0x7FFF)
    expected = 32767 * 32767
    assert result == expected, f"max*max: expected {expected}, got {result}"


@cocotb.test()
async def min_times_min(dut):
    """-32768 * -32768 = +1,073,741,824 (0x40000000, fits in signed 32-bit)"""
    await setup(dut)
    result = await multiply(dut, -32768, -32768)
    expected = (-32768) * (-32768)
    assert result == expected, f"min*min: expected {expected}, got {result}"


@cocotb.test()
async def min_times_max(dut):
    """-32768 * 32767 = most negative product (-1,073,709,056)"""
    await setup(dut)
    result = await multiply(dut, -32768, 0x7FFF)
    expected = (-32768) * 32767
    assert result == expected, f"min*max: expected {expected}, got {result}"


@cocotb.test()
async def one_identity(dut):
    """n * 1 = n (multiplicative identity)"""
    await setup(dut)
    a = random.randint(-32768, 32767)
    result = await multiply(dut, a, 1)
    assert result == a, f"{a} * 1: expected {a}, got {result}"


@cocotb.test()
async def minus_one_negate(dut):
    """n * -1 = -n"""
    await setup(dut)
    a = random.randint(-32768, 32767)
    result = await multiply(dut, a, -1)
    expected = -a
    assert result == expected, f"{a} * -1: expected {expected}, got {result}"


# === Random stress ===


@cocotb.test()
async def random_stress(dut):
    """200 random signed 16-bit pairs verified against Python reference"""
    await setup(dut)
    for _ in range(200):
        a = random.randint(-32768, 32767)
        b = random.randint(-32768, 32767)
        result = await multiply(dut, a, b)
        expected = a * b
        assert result == expected, f"{a} * {b}: expected {expected}, got {result}"
