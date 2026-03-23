"""
DCIM unit tests (tinymoa_dcim and tinymoa_compressor in isolation).

Compressor (tinymoa_compressor):
- exact_all_zeros
- exact_all_ones
- exact_single_bit_each_position
- exact_random_inputs
- single_approx_all_zeros
- single_approx_all_ones
- single_approx_known_pattern
- single_approx_rmse_under_threshold
- double_approx_all_zeros
- double_approx_all_ones
- double_approx_known_pattern
- double_approx_rmse_under_threshold
- output_width_always_5_bits

XNOR + Popcount Datapath:
- xnor_all_match_popcount_32
- xnor_all_mismatch_popcount_0
- xnor_half_match_popcount_16
- xnor_single_match_popcount_1
- popcount_lo_hi_split_sums_correctly

Shift Accumulator:
- accumulator_clear_on_start
- accumulator_single_bitplane_equals_popcount
- accumulator_two_bitplanes_msb_weighted
- accumulator_four_bitplanes_positional_weights
- accumulator_no_overflow_at_max_4bit

Bias Precomputation:
- bias_1bit_array32
- bias_2bit_array32
- bias_4bit_array32
- bias_1bit_array1
- bias_4bit_array16

FSM State Transitions:
- idle_to_load_weights_on_start_with_reload
- idle_to_fetch_act_on_start_without_reload
- load_weights_to_fetch_act_after_n_rows
- fetch_act_to_compute_after_two_cycles
- compute_loops_to_fetch_act_when_bitplanes_remain
- compute_to_store_result_on_last_bitplane
- store_result_to_done_after_n_columns
- done_to_idle_in_one_cycle
- idle_ignores_when_start_not_set

Weight Register Transpose:
- transpose_identity_matrix
- transpose_all_ones
- transpose_single_row_single_col
- transpose_random_matrix

Signed Conversion Logic:
- store_signed_positive
- store_signed_negative
- store_signed_zero
- store_signed_max_positive
- store_signed_max_negative
- store_word_sign_extension_positive
- store_word_sign_extension_negative

Reset:
- reset_clears_fsm_to_idle
- reset_clears_accumulators
- reset_clears_weight_registers
- reset_clears_status
- reset_restores_config_defaults
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the DCIM"""
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


@cocotb.test()
async def test_foo(dut):
    """Test template"""
    await setup(dut)
    await ClockCycles(dut.clk, 1)

    raise NotImplementedError("Test not implemented yet")
