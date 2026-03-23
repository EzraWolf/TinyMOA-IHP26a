"""
Test suite for the boot FSM (boot_fsm)

- reset_holds_boot_done_low
- idle_to_fetch_on_reset_deassert
- flash_addr_starts_at_0x001000
- flash_read_asserted_during_fetch
- write_tcm_sram_wen_one_cycle
- write_tcm_correct_sram_addr
- word_index_increments_after_each_word
- all_512_words_copied_in_order
- boot_done_asserts_after_512_words
- boot_done_stays_high_after_completion
- flash_stall_fsm_waits_for_ready
- flash_ready_deasserted_after_word
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup_tb_bootloader(dut):
    """Initialize the bootloader"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup_tb_bootloader(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")
