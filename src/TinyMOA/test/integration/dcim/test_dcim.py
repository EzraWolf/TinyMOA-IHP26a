"""
DCIM integration tests (DCIM + TCM + MMIO bus).

MMIO Interface:
- mmio_config_defaults_after_reset
- mmio_write_readback_all_registers
- mmio_status_busy_during_inference
- mmio_status_done_after_inference
- mmio_start_self_clears
- mmio_read_invalid_address_returns_zero

TCM Port B Bus Protocol:
- tcm_weight_read_addresses_sequential
- tcm_activation_read_addresses_per_bitplane
- tcm_result_write_addresses_sequential
- tcm_no_write_during_read_phases
- tcm_no_read_during_write_phase
- tcm_custom_base_addresses_honored
- tcm_pipelined_weight_load_overlaps_read_and_latch

End-to-End Inference (exact compressor):
- e2e_identity_weights_1bit
- e2e_all_ones_weights_1bit
- e2e_all_zeros_weights_1bit
- e2e_random_1bit_vs_golden
- e2e_random_2bit_vs_golden
- e2e_random_4bit_vs_golden
- e2e_random_100_vectors_1bit
- e2e_random_100_vectors_4bit

Signed Conversion Through TCM:
- signed_result_positive_in_tcm
- signed_result_negative_in_tcm
- signed_result_zero_in_tcm
- signed_result_max_positive_in_tcm
- signed_result_max_negative_in_tcm
- signed_result_sign_extended_to_32bit

Weight Persistence Across Inferences:
- weights_persist_when_reload_off
- weights_overwritten_when_reload_on
- back_to_back_different_activations_same_weights
- back_to_back_different_weights_different_activations
- back_to_back_different_precision_modes

Array Size Through Bus:
- array_size_1_minimal_inference
- array_size_16_partial_array
- array_size_32_full_array
- array_size_16_ignores_extra_tcm_data

Reset Recovery:
- reset_during_load_weights_then_reinfer
- reset_during_compute_then_reinfer
- reset_during_store_result_then_reinfer
- reset_clears_status_and_config

Cycle Counting:
- cycle_count_1bit_with_reload
- cycle_count_1bit_without_reload
- cycle_count_4bit_with_reload
- cycle_count_4bit_without_reload
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the DCIM core"""
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
