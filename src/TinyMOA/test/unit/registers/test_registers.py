"""
Test suite for tinymoa_registers -- 32-bit single-cycle 2R1W register file.

Control lines verified per test:
  rs1_data, rs2_data: combinational read output
  rd_wen, rd_sel, rd_data: synchronous write port

Tests:
- x0_reads_zero
- x0_write_ignored
- gp_reads_0x000400
- tp_reads_0x400000
- write_then_read
- write_all_storage_registers
- simultaneous_rs1_rs2_different_regs
- simultaneous_rs1_rs2_same_reg
- no_cross_contamination_between_regs
- reset_clears_all_registers
- rd_wen_low_does_not_corrupt
- write_zero_to_register
- write_max_to_register
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


STORAGE_REGS = [r for r in range(16) if r not in (0, 3, 4)]


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    dut.rs1_sel.value = 0
    dut.rs2_sel.value = 0
    dut.rd_sel.value = 0
    dut.rd_data.value = 0
    dut.rd_wen.value = 0
    await ClockCycles(dut.clk, 2)
    dut.nrst.value = 1
    await ClockCycles(dut.clk, 1)


async def write_reg(dut, reg, value):
    """Write a 32-bit value in one clock cycle."""
    dut.rd_sel.value = reg
    dut.rd_data.value = int(value) & 0xFFFFFFFF
    dut.rd_wen.value = 1
    await ClockCycles(dut.clk, 1)
    dut.rd_wen.value = 0


async def read_regs(dut, rs1, rs2):
    """Set read selects, settle combinational outputs, return (rs1_data, rs2_data)."""
    dut.rs1_sel.value = rs1
    dut.rs2_sel.value = rs2
    await Timer(1, unit="ns")
    return int(dut.rs1_data.value), int(dut.rs2_data.value)


@cocotb.test()
async def x0_reads_zero(dut):
    """x0 always reads zero on both ports."""
    await setup(dut)
    v1, v2 = await read_regs(dut, 0, 0)
    assert v1 == 0, f"x0 rs1: expected 0, got {hex(v1)}"
    assert v2 == 0, f"x0 rs2: expected 0, got {hex(v2)}"


@cocotb.test()
async def x0_write_ignored(dut):
    """Writing to x0 has no effect and reads back 0."""
    await setup(dut)
    await write_reg(dut, 0, 0xDEADBEEF)
    v1, _ = await read_regs(dut, 0, 0)
    assert v1 == 0, f"x0 after write: expected 0, got {hex(v1)}"


@cocotb.test()
async def gp_reads_0x000400(dut):
    """x3 (gp) reads 0x000400 on both ports."""
    await setup(dut)
    v1, v2 = await read_regs(dut, 3, 3)
    assert v1 == 0x000400, f"gp rs1: expected 0x000400, got {hex(v1)}"
    assert v2 == 0x000400, f"gp rs2: expected 0x000400, got {hex(v2)}"


@cocotb.test()
async def tp_reads_0x400000(dut):
    """x4 (tp) reads 0x400000 on both ports."""
    await setup(dut)
    v1, v2 = await read_regs(dut, 4, 4)
    assert v1 == 0x400000, f"tp rs1: expected 0x400000, got {hex(v1)}"
    assert v2 == 0x400000, f"tp rs2: expected 0x400000, got {hex(v2)}"


@cocotb.test()
async def write_then_read(dut):
    """Write random values to all storage registers and read them back."""
    await setup(dut)
    values = {r: random.randint(1, 0xFFFFFFFF) for r in STORAGE_REGS}

    for reg in STORAGE_REGS:
        await write_reg(dut, reg, values[reg])

    for reg in STORAGE_REGS:
        v1, v2 = await read_regs(dut, reg, reg)
        assert v1 == values[reg], (
            f"x{reg} rs1: expected {hex(values[reg])}, got {hex(v1)}"
        )
        assert v2 == values[reg], (
            f"x{reg} rs2: expected {hex(values[reg])}, got {hex(v2)}"
        )


@cocotb.test()
async def write_all_storage_registers(dut):
    """Unique deterministic value written to every storage register reads back correctly."""
    await setup(dut)
    values = {r: r * 0x11111111 for r in STORAGE_REGS}

    for reg in STORAGE_REGS:
        await write_reg(dut, reg, values[reg])

    for reg in STORAGE_REGS:
        v1, _ = await read_regs(dut, reg, reg)
        assert v1 == values[reg], f"x{reg}: expected {hex(values[reg])}, got {hex(v1)}"


@cocotb.test()
async def simultaneous_rs1_rs2_different_regs(dut):
    """Both read ports return correct values when reading different registers."""
    await setup(dut)
    await write_reg(dut, 1, 0xAAAAAAAA)
    await write_reg(dut, 2, 0x55555555)
    v1, v2 = await read_regs(dut, 1, 2)
    assert v1 == 0xAAAAAAAA, f"x1: expected 0xAAAAAAAA, got {hex(v1)}"
    assert v2 == 0x55555555, f"x2: expected 0x55555555, got {hex(v2)}"


@cocotb.test()
async def simultaneous_rs1_rs2_same_reg(dut):
    """Both ports return the same value when reading the same register."""
    await setup(dut)
    await write_reg(dut, 5, 0xDEADBEEF)
    v1, v2 = await read_regs(dut, 5, 5)
    assert v1 == 0xDEADBEEF, f"x5 rs1: expected 0xDEADBEEF, got {hex(v1)}"
    assert v2 == 0xDEADBEEF, f"x5 rs2: expected 0xDEADBEEF, got {hex(v2)}"
    assert v1 == v2, f"port mismatch: rs1={hex(v1)}, rs2={hex(v2)}"


@cocotb.test()
async def no_cross_contamination_between_regs(dut):
    """Writing to one register does not affect any other register."""
    await setup(dut)
    values = {r: (0xF0F0F0F0 ^ (r << 4)) & 0xFFFFFFFF for r in STORAGE_REGS}
    for reg in STORAGE_REGS:
        await write_reg(dut, reg, values[reg])
    for reg in STORAGE_REGS:
        v1, _ = await read_regs(dut, reg, reg)
        assert v1 == values[reg], (
            f"x{reg}: contaminated, expected {hex(values[reg])}, got {hex(v1)}"
        )


@cocotb.test()
async def reset_clears_all_registers(dut):
    """After reset, all storage registers read 0."""
    await setup(dut)
    for reg in STORAGE_REGS:
        await write_reg(dut, reg, 0xFFFFFFFF)
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 2)
    dut.nrst.value = 1
    await ClockCycles(dut.clk, 1)
    for reg in STORAGE_REGS:
        v1, _ = await read_regs(dut, reg, reg)
        assert v1 == 0, f"x{reg}: expected 0 after reset, got {hex(v1)}"


@cocotb.test()
async def rd_wen_low_does_not_corrupt(dut):
    """With rd_wen=0, clocking many cycles does not corrupt register contents."""
    await setup(dut)
    await write_reg(dut, 6, 0x12345678)
    dut.rd_wen.value = 0
    await ClockCycles(dut.clk, 32)
    v1, _ = await read_regs(dut, 6, 6)
    assert v1 == 0x12345678, f"x6: expected 0x12345678 after idle, got {hex(v1)}"


@cocotb.test()
async def write_zero_to_register(dut):
    """Writing 0 over a non-zero value reads back 0."""
    await setup(dut)
    await write_reg(dut, 7, 0xFFFFFFFF)
    await write_reg(dut, 7, 0x00000000)
    v1, _ = await read_regs(dut, 7, 7)
    assert v1 == 0, f"x7: expected 0 after writing zero, got {hex(v1)}"


@cocotb.test()
async def write_max_to_register(dut):
    """Writing 0xFFFFFFFF reads back 0xFFFFFFFF."""
    await setup(dut)
    await write_reg(dut, 8, 0xFFFFFFFF)
    v1, _ = await read_regs(dut, 8, 8)
    assert v1 == 0xFFFFFFFF, f"x8: expected 0xFFFFFFFF, got {hex(v1)}"
