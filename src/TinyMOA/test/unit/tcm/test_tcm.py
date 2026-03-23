"""
Test suite for TCM (sram_wrapper, behavioral model)

- port_a_write_read_latency_one_cycle
- port_b_write_read_latency_one_cycle
- port_a_and_port_b_different_addresses
- port_a_and_port_b_same_address_concurrent
- write_all_zeros
- write_all_ones
- write_alternating_pattern
- address_boundary_zero
- address_boundary_max
- multiple_sequential_writes_then_reads
- port_a_read_only
- port_b_read_only
- back_to_back_reads_port_a
- back_to_back_reads_port_b
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer


async def setup(dut):
    """Initialize the TCM block (no nrst on DUT)."""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # All ports idle
    dut.a_en.value = 0
    dut.a_wen.value = 0
    dut.a_addr.value = 0
    dut.a_din.value = 0
    dut.b_en.value = 0
    dut.b_wen.value = 0
    dut.b_addr.value = 0
    dut.b_din.value = 0

    await ClockCycles(dut.clk, 2)


async def write_port_a(dut, addr, data):
    """Write one word via port A (one clock cycle)."""
    await RisingEdge(dut.clk)
    dut.a_addr.value = addr
    dut.a_din.value = data
    dut.a_en.value = 1
    dut.a_wen.value = 1
    await RisingEdge(dut.clk)
    dut.a_en.value = 0
    dut.a_wen.value = 0


async def read_port_a(dut, addr):
    """Read one word via port A and return the data (1-cycle latency)."""
    await RisingEdge(dut.clk)
    dut.a_addr.value = addr
    dut.a_en.value = 1
    dut.a_wen.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    val = int(dut.a_dout.value)
    dut.a_en.value = 0
    return val


async def write_port_b(dut, addr, data):
    """Write one word via port B."""
    await RisingEdge(dut.clk)
    dut.b_addr.value = addr
    dut.b_din.value = data
    dut.b_en.value = 1
    dut.b_wen.value = 1
    await RisingEdge(dut.clk)
    dut.b_en.value = 0
    dut.b_wen.value = 0


async def read_port_b(dut, addr):
    """Read one word via port B and return the data (1-cycle latency)."""
    await RisingEdge(dut.clk)
    dut.b_addr.value = addr
    dut.b_en.value = 1
    dut.b_wen.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    val = int(dut.b_dout.value)
    dut.b_en.value = 0
    return val


@cocotb.test()
async def port_a_write_read_latency_one_cycle(dut):
    """Write via port A, read back one cycle later."""
    await setup(dut)
    await write_port_a(dut, 5, 0xDEADBEEF)
    val = await read_port_a(dut, 5)
    assert val == 0xDEADBEEF, f"Expected 0xDEADBEEF, got 0x{val:08X}"


@cocotb.test()
async def port_b_write_read_latency_one_cycle(dut):
    """Write via port B, read back one cycle later."""
    await setup(dut)
    await write_port_b(dut, 10, 0xCAFEBABE)
    val = await read_port_b(dut, 10)
    assert val == 0xCAFEBABE, f"Expected 0xCAFEBABE, got 0x{val:08X}"


@cocotb.test()
async def port_a_and_port_b_different_addresses(dut):
    """Write different data on both ports to different addresses, verify cross-read."""
    await setup(dut)
    await write_port_a(dut, 20, 0x11111111)
    await write_port_b(dut, 30, 0x22222222)

    val_a = await read_port_a(dut, 20)
    val_b = await read_port_b(dut, 30)
    assert val_a == 0x11111111, f"Port A addr 20: got 0x{val_a:08X}"
    assert val_b == 0x22222222, f"Port B addr 30: got 0x{val_b:08X}"

    # Cross read: port B reads addr written by A, port A reads addr written by B
    val_cross_a = await read_port_a(dut, 30)
    val_cross_b = await read_port_b(dut, 20)
    assert val_cross_a == 0x22222222, f"Cross A->30: got 0x{val_cross_a:08X}"
    assert val_cross_b == 0x11111111, f"Cross B->20: got 0x{val_cross_b:08X}"


@cocotb.test()
async def port_a_and_port_b_same_address_concurrent(dut):
    """Both ports write to same address in same cycle; last write wins (B wins per simulation)."""
    await setup(dut)
    # Write different values to same address simultaneously
    await RisingEdge(dut.clk)
    dut.a_addr.value = 50
    dut.a_din.value = 0xAAAAAAAA
    dut.a_en.value = 1
    dut.a_wen.value = 1
    dut.b_addr.value = 50
    dut.b_din.value = 0xBBBBBBBB
    dut.b_en.value = 1
    dut.b_wen.value = 1
    await RisingEdge(dut.clk)
    dut.a_en.value = 0
    dut.a_wen.value = 0
    dut.b_en.value = 0
    dut.b_wen.value = 0

    val = await read_port_a(dut, 50)
    # Either value is acceptable - just verify it's one of the two (not garbage)
    assert val in (0xAAAAAAAA, 0xBBBBBBBB), (
        f"Expected one of the written values, got 0x{val:08X}"
    )


@cocotb.test()
async def write_all_zeros(dut):
    """Write all zeros, read back zero."""
    await setup(dut)
    await write_port_a(dut, 1, 0x00000000)
    val = await read_port_a(dut, 1)
    assert val == 0x00000000, f"Expected 0, got 0x{val:08X}"


@cocotb.test()
async def write_all_ones(dut):
    """Write all ones, read back all ones."""
    await setup(dut)
    await write_port_a(dut, 2, 0xFFFFFFFF)
    val = await read_port_a(dut, 2)
    assert val == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got 0x{val:08X}"


@cocotb.test()
async def write_alternating_pattern(dut):
    """Write 0x55555555 and 0xAAAAAAAA, read back both."""
    await setup(dut)
    await write_port_a(dut, 3, 0x55555555)
    await write_port_a(dut, 4, 0xAAAAAAAA)
    v3 = await read_port_a(dut, 3)
    v4 = await read_port_a(dut, 4)
    assert v3 == 0x55555555, f"addr 3: got 0x{v3:08X}"
    assert v4 == 0xAAAAAAAA, f"addr 4: got 0x{v4:08X}"


@cocotb.test()
async def address_boundary_zero(dut):
    """Read and write at address 0."""
    await setup(dut)
    await write_port_a(dut, 0, 0x12345678)
    val = await read_port_a(dut, 0)
    assert val == 0x12345678, f"addr 0: got 0x{val:08X}"


@cocotb.test()
async def address_boundary_max(dut):
    """Read and write at address 511 (maximum for 512x32)."""
    await setup(dut)
    await write_port_a(dut, 511, 0xFEDCBA98)
    val = await read_port_a(dut, 511)
    assert val == 0xFEDCBA98, f"addr 511: got 0x{val:08X}"


@cocotb.test()
async def multiple_sequential_writes_then_reads(dut):
    """Write 8 locations sequentially, then read all back."""
    await setup(dut)
    test_data = {100 + i: 0xA0000000 + i for i in range(8)}
    for addr, val in test_data.items():
        await write_port_a(dut, addr, val)
    for addr, expected in test_data.items():
        got = await read_port_a(dut, addr)
        assert got == expected, (
            f"addr {addr}: expected 0x{expected:08X}, got 0x{got:08X}"
        )


@cocotb.test()
async def port_a_read_only(dut):
    """Write via B, read via A to confirm shared memory."""
    await setup(dut)
    await write_port_b(dut, 60, 0x98765432)
    val = await read_port_a(dut, 60)
    assert val == 0x98765432, f"Expected 0x98765432, got 0x{val:08X}"


@cocotb.test()
async def port_b_read_only(dut):
    """Write via A, read via B to confirm shared memory."""
    await setup(dut)
    await write_port_a(dut, 70, 0x13579BDF)
    val = await read_port_b(dut, 70)
    assert val == 0x13579BDF, f"Expected 0x13579BDF, got 0x{val:08X}"


@cocotb.test()
async def back_to_back_reads_port_a(dut):
    """Write two words, then read them back-to-back via port A."""
    await setup(dut)
    await write_port_a(dut, 80, 0x0000AAAA)
    await write_port_a(dut, 81, 0x0000BBBB)

    # Start read of 80, then immediately read 81 next cycle
    await RisingEdge(dut.clk)
    dut.a_addr.value = 80
    dut.a_en.value = 1
    dut.a_wen.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    val80 = int(dut.a_dout.value)

    dut.a_addr.value = 81
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    val81 = int(dut.a_dout.value)
    dut.a_en.value = 0

    assert val80 == 0x0000AAAA, f"addr 80: got 0x{val80:08X}"
    assert val81 == 0x0000BBBB, f"addr 81: got 0x{val81:08X}"


@cocotb.test()
async def back_to_back_reads_port_b(dut):
    """Write two words, then read them back-to-back via port B."""
    await setup(dut)
    await write_port_b(dut, 90, 0x0000CCCC)
    await write_port_b(dut, 91, 0x0000DDDD)

    await RisingEdge(dut.clk)
    dut.b_addr.value = 90
    dut.b_en.value = 1
    dut.b_wen.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    val90 = int(dut.b_dout.value)

    dut.b_addr.value = 91
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    val91 = int(dut.b_dout.value)
    dut.b_en.value = 0

    assert val90 == 0x0000CCCC, f"addr 90: got 0x{val90:08X}"
    assert val91 == 0x0000DDDD, f"addr 91: got 0x{val91:08X}"
