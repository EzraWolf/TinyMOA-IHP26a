"""
CPU integration tests (tinymoa_cpu + TCM + decoder + ALU + registers).

Reset and Boot:
- reset_pc_zero
- reset_all_registers_zero
- first_fetch_reads_tcm_address_zero

RV32I End-to-End (instruction in TCM, execute, verify register/memory result):
- add_two_registers
- addi_immediate
- sub_two_registers
- and_or_xor_registers
- andi_ori_xori_immediate
- slt_sltu_registers
- slti_sltiu_immediate
- sll_srl_sra_registers
- slli_srli_srai_immediate
- lui_loads_upper
- auipc_adds_pc
- jal_jumps_and_links
- jalr_jumps_from_register
- beq_taken
- beq_not_taken
- bne_taken
- blt_bge_signed
- bltu_bgeu_unsigned

RV32C End-to-End:
- c_addi_four_cycles
- c_li_loads_immediate
- c_lui_loads_upper
- c_mv_copies_register
- c_add_two_registers
- c_sub_two_registers
- c_and_or_xor_registers
- c_slli_srli_srai
- c_not_inverts
- c_zext_b_sext_b
- c_zext_h_sext_h
- c_mul_16x16_to_32
- c_j_jumps
- c_jal_jumps_and_links
- c_jr_jumps_from_register
- c_jalr_jumps_and_links_from_register
- c_beqz_taken
- c_beqz_not_taken
- c_bnez_taken
- c_bnez_not_taken
- c_addi4spn
- c_addi16sp

Load/Store Through TCM:
- lw_sw_round_trip
- lb_sb_round_trip
- lh_sh_round_trip
- lbu_zero_extends
- lhu_zero_extends
- lw_sw_all_byte_offsets
- c_lw_c_sw_round_trip
- c_lbu_c_sb_round_trip
- c_lhu_c_lh_c_sh_round_trip
- store_then_load_same_address
- store_then_load_adjacent_addresses

Special Registers:
- gp_reads_as_0x000400
- tp_reads_as_0x400000
- gp_relative_load_store
- tp_relative_load_store
- x0_write_ignored_in_instruction

Mixed RV32I and RV32C:
- rv32i_then_rv32c_sequential
- rv32c_then_rv32i_sequential
- interleaved_32bit_and_16bit_instructions
- branch_from_rv32c_to_rv32i
- branch_from_rv32i_to_rv32c_aligned

Pipeline Hazards:
- back_to_back_alu_no_stall
- load_use_stall
- store_after_alu_no_stall
- branch_after_alu
- jal_after_store

Multi-Instruction Sequences:
- fibonacci_10_terms_rv32i
- fibonacci_10_terms_rv32c
- fibonacci_mixed_rv32i_rv32c
- sum_array_rv32i
- sum_array_rv32c
- memcpy_loop_rv32i
- bubble_sort_4_elements
- multiply_accumulate_loop
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the CPU"""
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
