"""
Test suite for the register file (tinymoa_registers)

- x0_reads_zero
- x0_write_ignored
- gp_reads_0x000400
- tp_reads_0x400000
- write_then_read_nibble_serial
- write_all_storage_registers
- simultaneous_rs1_rs2_different_regs
- simultaneous_rs1_rs2_same_reg
- no_cross_contamination_between_regs
- reset_clears_all_registers
- rd_wr_en_low_does_not_corrupt
- nibble_position_alignment_after_partial_cycle
- write_zero_to_register
- write_max_to_register
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the register file"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.nrst.value = 0
    dut.rs1_sel.value = 0
    dut.rs2_sel.value = 0
    dut.rd_sel.value = 0
    dut.rd_data.value = 0
    dut.rd_wen.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def write_reg(dut, reg, value):
    """Write a 32-bit value to a register over 8 nibble cycles."""
    dut.rd_sel.value = reg
    dut.rd_data.value = int(value)
    dut.rd_wen.value = 1
    await ClockCycles(dut.clk, 8)
    dut.rd_wen.value = 0


async def read_regs(dut, rs1, rs2):
    """Read two registers over 8 nibble cycles. Returns (rs1_val, rs2_val)."""
    dut.rs1_sel.value = rs1
    dut.rs2_sel.value = rs2
    dut.rd_wen.value = 0
    await ClockCycles(dut.clk, 8)
    dut.rd_sel.value = 0
    dut.rd_data.value = 0
    dut.rd_wen.value = 1
    await ClockCycles(dut.clk, 1)  # Resolve to read
    return int(dut.rs1_data.value), int(dut.rs2_data.value)


@cocotb.test()
async def x0_reads_zero(dut):
    """x0 always reads zero"""
    await setup(dut)
    rs1, _ = await read_regs(dut, 0, 0)
    assert rs1 == 0, f"x0: expected 0, got {hex(rs1)}"


@cocotb.test()
async def x0_write_ignored(dut):
    """Writing to x0 has no effect"""
    await setup(dut)
    await write_reg(dut, 0, 0xDEADBEEF)
    rs1, _ = await read_regs(dut, 0, 0)
    assert rs1 == 0, f"x0 after write: expected 0, got {hex(rs1)}"


@cocotb.test()
async def gp_reads_0x000400(dut):
    """x3 (gp) reads 0x000400"""
    await setup(dut)
    rs1, _ = await read_regs(dut, 3, 3)
    assert rs1 == 0x000400, f"gp: expected 0x000400, got {hex(rs1)}"


@cocotb.test()
async def tp_reads_0x400000(dut):
    """x4 (tp) reads 0x400000"""
    await setup(dut)
    rs1, _ = await read_regs(dut, 4, 4)
    assert rs1 == 0x400000, f"tp: expected 0x400000, got {hex(rs1)}"


@cocotb.test()
async def write_then_read_nibble_serial(dut):
    """Write random values to storage registers and read them back."""
    await setup(dut)
    # Skip x0 (hardwired), x3 (gp), x4 (tp)
    storage_regs = [r for r in range(16) if r not in (0, 3, 4)]
    values = {r: random.randint(0, 0xFFFFFFFF) for r in storage_regs}

    for reg in storage_regs:
        await write_reg(dut, reg, values[reg])

    for reg in storage_regs:
        rs1, rs2 = await read_regs(dut, reg, reg)
        assert rs1 == values[reg], (
            f"x{reg}: expected {hex(values[reg])}, got {hex(rs1)}"
        )
        assert rs1 == rs2, f"x{reg} port mismatch: rs1={hex(rs1)}, rs2={hex(rs2)}"


@cocotb.test()
async def write_all_storage_registers(dut):
    """Write a unique value to every storage register and read each back."""
    await setup(dut)
    storage_regs = [r for r in range(16) if r not in (0, 3, 4)]
    # Unique deterministic value per register: reg_index * 0x11111111
    values = {r: r * 0x11111111 for r in storage_regs}

    for reg in storage_regs:
        await write_reg(dut, reg, values[reg])

    for reg in storage_regs:
        rs1, _ = await read_regs(dut, reg, reg)
        assert rs1 == values[reg], (
            f"x{reg}: expected {hex(values[reg])}, got {hex(rs1)}"
        )


@cocotb.test()
async def simultaneous_rs1_rs2_different_regs(dut):
    """Both read ports return correct values when reading different registers simultaneously."""
    await setup(dut)
    await write_reg(dut, 1, 0xAAAAAAAA)
    await write_reg(dut, 2, 0x55555555)
    rs1, rs2 = await read_regs(dut, 1, 2)
    assert rs1 == 0xAAAAAAAA, f"x1: expected 0xAAAAAAAA, got {hex(rs1)}"
    assert rs2 == 0x55555555, f"x2: expected 0x55555555, got {hex(rs2)}"


@cocotb.test()
async def simultaneous_rs1_rs2_same_reg(dut):
    """Both read ports return the same value when reading the same register."""
    await setup(dut)
    await write_reg(dut, 5, 0xDEADBEEF)
    rs1, rs2 = await read_regs(dut, 5, 5)
    assert rs1 == 0xDEADBEEF, f"x5 rs1: expected 0xDEADBEEF, got {hex(rs1)}"
    assert rs2 == 0xDEADBEEF, f"x5 rs2: expected 0xDEADBEEF, got {hex(rs2)}"
    assert rs1 == rs2, f"port mismatch: rs1={hex(rs1)}, rs2={hex(rs2)}"


@cocotb.test()
async def no_cross_contamination_between_regs(dut):
    """Writing to one register does not affect any other register."""
    await setup(dut)
    storage_regs = [r for r in range(16) if r not in (0, 3, 4)]
    values = {r: (0xF0F0F0F0 ^ (r << 4)) & 0xFFFFFFFF for r in storage_regs}
    for reg in storage_regs:
        await write_reg(dut, reg, values[reg])
    for reg in storage_regs:
        rs1, _ = await read_regs(dut, reg, reg)
        assert rs1 == values[reg], (
            f"x{reg}: contaminated — expected {hex(values[reg])}, got {hex(rs1)}"
        )


@cocotb.test()
async def reset_clears_all_registers(dut):
    """After reset, all storage registers read 0."""
    await setup(dut)
    storage_regs = [r for r in range(16) if r not in (0, 3, 4)]
    for reg in storage_regs:
        await write_reg(dut, reg, 0xFFFFFFFF)
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 2)
    dut.nrst.value = 1
    for reg in storage_regs:
        rs1, _ = await read_regs(dut, reg, reg)
        assert rs1 == 0, f"x{reg}: expected 0 after reset, got {hex(rs1)}"


@cocotb.test()
async def rd_wr_en_low_does_not_corrupt(dut):
    """With wen=0, clocking does not corrupt register contents."""
    await setup(dut)
    await write_reg(dut, 6, 0x12345678)
    dut.rd_wen.value = 0
    await ClockCycles(dut.clk, 32)
    rs1, _ = await read_regs(dut, 6, 6)
    assert rs1 == 0x12345678, f"x6: expected 0x12345678 after idle, got {hex(rs1)}"


@cocotb.test(skip=True)
async def nibble_position_alignment_after_partial_cycle(dut):
    """
    After a partial read cycle (< 8 cycles), nibble_ct and register rotation
    fall out of sync with no recovery mechanism in the TB.
    Skipped: requires TB-level nibble_ct reset support to test properly.
    """


@cocotb.test()
async def write_zero_to_register(dut):
    """Writing 0 to a storage register reads back 0."""
    await setup(dut)
    await write_reg(dut, 7, 0xFFFFFFFF)
    await write_reg(dut, 7, 0x00000000)
    rs1, _ = await read_regs(dut, 7, 7)
    assert rs1 == 0, f"x7: expected 0 after writing zero, got {hex(rs1)}"


@cocotb.test()
async def write_max_to_register(dut):
    """Writing 0xFFFFFFFF to a storage register reads back 0xFFFFFFFF."""
    await setup(dut)
    await write_reg(dut, 8, 0xFFFFFFFF)
    rs1, _ = await read_regs(dut, 8, 8)
    assert rs1 == 0xFFFFFFFF, f"x8: expected 0xFFFFFFFF, got {hex(rs1)}"
