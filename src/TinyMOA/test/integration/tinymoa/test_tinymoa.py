"""
TinyMOA top-level integration tests (full system: CPU + TCM + QSPI + bootloader + DCIM).

Boot Sequence:
- boot_loads_flash_to_tcm
- boot_holds_cpu_in_reset_during_load
- boot_releases_cpu_after_done
- boot_tcm_contents_match_flash_image
- cpu_starts_at_pc_zero_after_boot

TCM Only:
- tcm_lw_sw_round_trip
- tcm_lb_sb_all_four_byte_offsets
- tcm_lh_sh_both_halfword_offsets
- tcm_lbu_lhu_zero_extension
- tcm_store_then_fetch_as_instruction
- tcm_write_read_boundary_addresses
- tcm_c_lw_c_sw_round_trip
- tcm_c_lbu_c_sb_round_trip

QSPI Flash:
- qspi_flash_read_word
- qspi_flash_read_byte
- qspi_flash_read_halfword
- qspi_flash_sequential_reads
- qspi_flash_fetch_instruction
- qspi_flash_stall_holds_pipeline

QSPI PSRAM:
- psram_a_write_read_word
- psram_a_write_read_byte
- psram_b_write_read_word
- psram_b_write_read_byte
- psram_a_then_psram_b_different_data
- psram_sequential_write_then_sequential_read

Mixed Memory:
- tcm_store_then_qspi_flash_fetch
- qspi_flash_load_then_tcm_store
- tcm_code_loads_from_psram_a
- tcm_code_stores_to_psram_b
- tcm_to_psram_memcpy
- psram_to_tcm_memcpy
- load_from_all_four_regions_in_sequence
- store_to_tcm_and_psram_interleaved

DCIM via MMIO (CPU-driven):
- cpu_writes_dcim_config_via_tp
- cpu_reads_dcim_status_via_tp
- cpu_polls_dcim_busy_then_done
- cpu_writes_weights_to_tcm_then_starts_dcim
- cpu_reads_dcim_results_from_tcm
- cpu_runs_two_inferences_back_to_back

Address Decode:
- tcm_region_decoded_correctly
- qspi_flash_region_decoded_correctly
- dcim_mmio_region_decoded_correctly
- psram_a_region_decoded_correctly
- psram_b_region_decoded_correctly
- access_near_region_boundary

RV32I Full Instruction Set:
- rv32i_add_sub
- rv32i_and_or_xor
- rv32i_slt_sltu
- rv32i_sll_srl_sra
- rv32i_addi_andi_ori_xori
- rv32i_slti_sltiu
- rv32i_slli_srli_srai
- rv32i_lui
- rv32i_auipc
- rv32i_lw_sw
- rv32i_lb_lbu_lh_lhu_sb_sh
- rv32i_beq_bne
- rv32i_blt_bge
- rv32i_bltu_bgeu
- rv32i_jal
- rv32i_jalr
- rv32i_czero_eqz_czero_nez

RV32C Full Instruction Set:
- rv32c_c_addi
- rv32c_c_li
- rv32c_c_lui
- rv32c_c_addi16sp
- rv32c_c_addi4spn
- rv32c_c_mv
- rv32c_c_add
- rv32c_c_sub
- rv32c_c_and_or_xor
- rv32c_c_not
- rv32c_c_slli_srli_srai
- rv32c_c_andi
- rv32c_c_zext_b_sext_b
- rv32c_c_zext_h_sext_h
- rv32c_c_lw_c_sw
- rv32c_c_lbu_c_lhu_c_lh
- rv32c_c_sb_c_sh
- rv32c_c_j
- rv32c_c_jal
- rv32c_c_jr
- rv32c_c_jalr
- rv32c_c_beqz
- rv32c_c_bnez
- rv32c_c_mul

Mixed RV32I/C:
- interleave_32bit_16bit_instructions
- rv32c_branch_to_rv32i_target
- rv32i_branch_to_rv32c_target
- rv32i_jal_to_rv32c_function
- rv32c_j_to_rv32i_function
- mixed_alu_then_mixed_load_store

Reset:
- full_reset_clears_cpu_and_dcim
- reset_during_qspi_access_recovers
- reset_during_dcim_inference_recovers
- reset_re_triggers_boot_sequence

Programs:
- prog_fibonacci_30_terms
- prog_bubble_sort_16_elements
- prog_binary_search_sorted_array
- prog_memcpy_tcm_to_psram
- prog_memset_psram_region
- prog_matrix_multiply_4x4_software
- prog_dcim_1bit_inference_and_read_results
- prog_dcim_4bit_inference_and_read_results
- prog_dcim_multi_layer_two_sequential_inferences
- prog_dcim_weight_reuse_across_activations
- prog_linked_list_traversal_in_tcm
- prog_function_call_stack_frames
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize TinyMOA"""
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
