"""
Test suite for general purpose program/nibble counters

- reset_clears_count
- increment_when_enabled
- hold_when_disabled
- over_run_wraps_to_zero
- under_run_wraps_to_max_val
- carry_asserted_at_max_val
- carry_not_asserted_before_max_val
- load_overrides_count
- load_to_zero
- load_to_max_val
- nibble_mode_eight_cycle_wrap
- nibble_mode_four_cycle_wrap
- load_mid_count
- max_val_one
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the counter"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.nrst.value = 0
    dut.en.value = 0
    dut.wen.value = 0
    dut.data_in.value = 0
    dut.result.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def reset_clears_count(dut):
    """Reset sets result to 0"""
    await setup(dut)
    result = int(dut.result.value)
    assert result == 0, f"expected 0, got {result}"


@cocotb.test()
async def increment_when_enabled(dut):
    """en=1 increments by 1 each cycle"""
    await setup(dut)
    dut.en.value = 1
    await ClockCycles(dut.clk, 1)

    for expected in range(0, 15):
        result = int(dut.result.value)
        assert result == expected, (
            f"cycle {expected}: expected {expected}, got {result}"
        )
        await ClockCycles(dut.clk, 1)


@cocotb.test()
async def hold_when_disabled(dut):
    """en=0 holds the count steady"""
    await setup(dut)
    dut.en.value = 1
    dut.wen.value = 0
    await ClockCycles(dut.clk, 5)  # Arbitrary
    dut.en.value = 0
    await ClockCycles(dut.clk, 1)
    held = int(dut.result.value)
    for _ in range(8):
        result = int(dut.result.value)
        assert result == held, f"expected count to hold at {held}, got {result}"
        await ClockCycles(dut.clk, 1)


@cocotb.test()
async def over_run_wraps_to_zero(dut):
    """0xFFFFFFFF + 1 wraps to 0"""
    await setup(dut)
    dut.wen.value = 1
    dut.data_in.value = 0xFFFFFFFF
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    dut.wen.value = 0
    dut.en.value = 1
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    assert int(dut.result.value) == 0, f"expected 0, got {hex(int(dut.result.value))}"


@cocotb.test()
async def under_run_wraps_to_max_val(dut):
    """No decrement in hardware. Tests wen load of 0 then +1 gives 1 (boundary sanity check)."""
    # tinymoa_counter only increments. True decrement/underflow is not supported.
    await setup(dut)
    dut.wen.value = 1
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    dut.wen.value = 0
    dut.en.value = 1
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    assert int(dut.result.value) == 1, f"expected 1, got {hex(int(dut.result.value))}"


@cocotb.test()
async def carry_asserted_at_max_val(dut):
    """c_out is 1 when result == 0xFFFFFFFF"""
    await setup(dut)
    dut.wen.value = 1
    dut.data_in.value = 0xFFFFFFFF
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    dut.wen.value = 0
    assert int(dut.c_out.value) == 1, "c_out should be 1 at max value"


@cocotb.test()
async def carry_not_asserted_before_max_val(dut):
    """c_out is 0 below max, then 1 after increment to max"""
    await setup(dut)
    dut.wen.value = 1
    dut.data_in.value = 0xFFFFFFFE
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    dut.wen.value = 0
    assert int(dut.c_out.value) == 0, "c_out should be 0 before max"
    dut.en.value = 1
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    assert int(dut.c_out.value) == 1, "c_out should be 1 after incrementing to max"


@cocotb.test()
async def load_overrides_count(dut):
    """Test that loading a value overrides the current count"""
    await setup(dut)
    dut.en.value = 1
    await ClockCycles(dut.clk, 6)  # count up to 5
    dut.wen.value = 1
    dut.data_in.value = 100
    await ClockCycles(dut.clk, 2)
    dut.wen.value = 0
    result = int(dut.result.value)
    assert result == 100, f"expected 100 after load, got {result}"


@cocotb.test()
async def load_to_zero(dut):
    """Loading to zero should be equivalent to reset"""
    await setup(dut)
    dut.en.value = 1
    await ClockCycles(dut.clk, 6)  # count up to 5
    dut.en.value = 0
    dut.wen.value = 1
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.wen.value = 0
    result = int(dut.result.value)
    assert result == 0, f"expected 0 after loading zero, got {result}"


@cocotb.test()
async def load_to_max_val(dut):
    """Test that loading to max value sets the count to max value"""
    await setup(dut)
    dut.wen.value = 1
    dut.data_in.value = 0xFFFFFFFF
    await ClockCycles(dut.clk, 2)
    dut.wen.value = 0
    result = int(dut.result.value)
    assert result == 0xFFFFFFFF, f"expected 0xFFFFFFFF, got {hex(result)}"
    assert int(dut.c_out.value) == 1, "c_out should be 1 at max value"


@cocotb.test(skip=True)
async def nibble_mode_eight_cycle_wrap(dut):
    """
    Test that in nibble mode, the count wraps every 8 cycles
    0, 1, 2, ... 7, 0, 1, 2, ...)
    Requires DATA_WIDTH=3 in testbench.
    """
    await setup(dut)
    dut.en.value = 1
    await ClockCycles(dut.clk, 1)  # load en control
    expected_sequence = [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3]
    for i, expected in enumerate(expected_sequence):
        result = int(dut.result.value)
        assert result == expected, f"cycle {i}: expected {expected}, got {result}"
        await ClockCycles(dut.clk, 1)


@cocotb.test(skip=True)
async def nibble_mode_four_cycle_wrap(dut):
    """
    Test that in nibble mode, the count wraps every 4 cycles
    0, 1, 2, 3, 0, 1, 2, 3, ...)

    Requires DATA_WIDTH=2 in testbench -- not testable with current DATA_WIDTH=32 TB.
    """

    raise NotImplementedError(
        "Requires DATA_WIDTH=2 in testbench, not testable with current DATA_WIDTH=32 TB"
    )


@cocotb.test()
async def load_mid_count(dut):
    """Loading a value overrides count even in the middle of counting"""
    await setup(dut)
    dut.en.value = 1
    await ClockCycles(dut.clk, 4)  # count up to 3
    dut.wen.value = 1
    dut.data_in.value = 50
    await ClockCycles(dut.clk, 2)
    dut.wen.value = 0
    result = int(dut.result.value)
    assert result == 50, f"expected 50 after mid-count load, got {result}"
    await ClockCycles(
        dut.clk, 2
    )  # first clock loads new wen and value, second clock counts up
    result = int(dut.result.value)
    assert result == 51, f"expected 51 after one more increment, got {result}"


@cocotb.test(skip=True)
async def max_val_one(dut):
    """Test that if max value is set to 1, count wraps every 2 cycles (0, 1, 0, 1, ...)
    Requires a max_val port and wrap-on-max logic in hardware.
    """
