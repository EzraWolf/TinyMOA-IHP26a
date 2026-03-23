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

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup_tb_tcm(dut):
    """Initialize the TCM"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup_tb_tcm(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")
