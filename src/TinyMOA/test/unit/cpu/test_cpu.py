"""
CPU unit tests (tinymoa_cpu in isolation, memory bus mocked).

Pipeline FSM:
- reset_state_is_fetch
- fetch_asserts_mem_read_with_pc
- fetch_to_decode_on_mem_ready
- decode_to_execute_in_one_cycle
- execute_runs_8_cycles_rv32i
- execute_runs_4_cycles_rv32c
- execute_runs_8_cycles_cmul
- writeback_updates_rd_and_advances_pc
- mem_stage_skipped_for_alu_ops
- mem_stage_entered_for_load_store
- mem_stall_holds_pipeline_until_ready

PC:
- pc_starts_at_zero_after_reset
- pc_increments_by_4_for_rv32i
- pc_increments_by_2_for_rv32c
- pc_jumps_on_jal
- pc_jumps_on_jalr
- pc_branches_forward_taken
- pc_branches_backward_taken
- pc_branches_not_taken

RV32I ALU (through pipeline):
- add_rd_rs1_rs2
- addi_rd_rs1_imm
- sub_rd_rs1_rs2
- and_or_xor_rd_rs1_rs2
- andi_ori_xori_rd_rs1_imm
- slt_signed_less_than
- sltu_unsigned_less_than
- slti_sltiu_immediate

RV32I Shifts (through pipeline):
- sll_rd_rs1_rs2
- slli_rd_rs1_shamt
- srl_rd_rs1_rs2
- srli_rd_rs1_shamt
- sra_rd_rs1_rs2
- srai_rd_rs1_shamt
- shift_by_zero
- shift_by_31

RV32I Upper Immediate:
- lui_loads_upper_20_bits
- auipc_adds_pc_plus_upper_20

RV32I Branches:
- beq_taken_equal
- beq_not_taken_unequal
- bne_taken_unequal
- bne_not_taken_equal
- blt_signed_less
- bge_signed_greater_or_equal
- bltu_unsigned_less
- bgeu_unsigned_greater_or_equal

RV32I Jumps:
- jal_saves_pc_plus_4_to_rd
- jalr_saves_pc_plus_4_to_rd
- jalr_target_from_rs1_plus_imm
- jalr_clears_lsb

Zicond:
- czero_eqz_zeroes_when_rs2_zero
- czero_eqz_passes_when_rs2_nonzero
- czero_nez_zeroes_when_rs2_nonzero
- czero_nez_passes_when_rs2_zero

RV32C Quadrant 0:
- c_addi4spn
- c_lw
- c_sw
- c_lbu
- c_lhu
- c_lh
- c_sb
- c_sh

RV32C Quadrant 1:
- c_nop
- c_addi
- c_jal
- c_li
- c_addi16sp
- c_lui
- c_srli
- c_srai
- c_andi
- c_sub
- c_xor
- c_or
- c_and
- c_not
- c_zext_b
- c_sext_b
- c_zext_h
- c_sext_h
- c_j
- c_beqz_taken
- c_beqz_not_taken
- c_bnez_taken
- c_bnez_not_taken

RV32C Quadrant 2:
- c_slli
- c_jr
- c_mv
- c_jalr
- c_add
- c_mul_positive
- c_mul_negative
- c_mul_overflow_truncates
- c_ebreak

Special Registers:
- x0_always_reads_zero
- x0_write_has_no_effect
- gp_reads_0x000400
- tp_reads_0x400000
- gp_tp_not_writable

Memory Bus Protocol:
- load_word_asserts_mem_read
- store_word_asserts_mem_write
- load_byte_sign_extends
- load_byte_unsigned_zero_extends
- load_halfword_sign_extends
- load_halfword_unsigned_zero_extends
- store_byte_masks_correctly
- store_halfword_masks_correctly

Nibble Sequencing:
- nibble_ct_counts_0_to_7_for_rv32i
- nibble_ct_counts_0_to_3_for_rv32c
- carry_propagates_across_all_8_nibbles
- register_read_one_nibble_ahead_of_write

Edge Cases:
- add_overflow_wraps
- sub_underflow_wraps
- immediate_sign_extension
- branch_offset_negative
- lui_with_zero_immediate
- addi_with_negative_immediate
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def setup(dut):
    """Initialize the CPU core"""
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
