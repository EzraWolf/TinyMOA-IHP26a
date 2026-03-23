"""
Test suite for the QSPI controller (qspi_controller)

- reset_all_cs_deasserted
- reset_clk_low
- flash_read_cs_selection
- flash_read_cmd_phase_0x03
- flash_read_addr_phase_24bit
- flash_read_data_phase_32bit
- psram_a_read_cs_selection
- psram_b_read_cs_selection
- psram_write_data_tx_phase
- ready_asserted_after_done
- cs_deasserted_after_done
- spi_data_oe_only_during_tx
- byte_size_mode
- halfword_size_mode
- word_size_mode
- back_to_back_reads
- clk_toggles_only_during_transaction
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the QSPI controller"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")
