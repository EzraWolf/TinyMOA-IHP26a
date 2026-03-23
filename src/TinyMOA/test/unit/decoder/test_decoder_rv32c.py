"""
Test suite for decoding RV32C (Zca, Zcb) instructions
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import utility.rv32c_encode as rv32c


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def decode(dut, instr_val):
    dut.instr.value = instr_val
    await ClockCycles(dut.clk, 1)


# === Quadrant 0 ===


@cocotb.test()
async def c_addi4spn_rd_and_sp_as_rs1(dut):
    """C.ADDI4SPN: rd'=x10 (rd_p=2 -> x10), rs1=sp(x2)"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_addi4spn(2, 16))  # rd_p=2 -> x10, imm=16
    assert dut.is_compressed.value == 1
    assert int(dut.rd.value) == 0b1010, f"rd: expected x10, got {int(dut.rd.value)}"
    assert int(dut.rs1.value) == 2, f"rs1: expected sp(x2), got {int(dut.rs1.value)}"


@cocotb.test()
async def c_lw_load_fields(dut):
    """C.LW: is_load, mem_opcode=word, rd'/rs1' fields"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_lw(0, 1, 0))  # rd_p=0->x8, rs1_p=1->x9
    assert dut.is_load.value == 1
    assert dut.is_compressed.value == 1
    assert dut.mem_opcode.value == 0b010  # word
    assert int(dut.rd.value) == 0b1000  # x8
    assert int(dut.rs1.value) == 0b1001  # x9


@cocotb.test()
async def csw_store_fields(dut):
    """C.SW: is_store, mem_opcode=word, rs1'/rs2' fields"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_sw(1, 2, 0))  # rs1_p=1->x9, rs2_p=2->x10
    assert dut.is_store.value == 1
    assert dut.is_compressed.value == 1
    assert dut.mem_opcode.value == 0b010
    assert int(dut.rs1.value) == 0b1001  # x9
    assert int(dut.rs2.value) == 0b1010  # x10


@cocotb.test()
async def zcb_byte_halfword_load_store(dut):
    """Zcb: C.LBU/C.LHU/C.LH/C.SB/C.SH set is_load/is_store with correct mem_opcode"""
    await setup(dut)
    # C.LBU: unsigned byte load
    await decode(dut, rv32c.encode_c_lbu(0, 1, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b100  # byte unsigned

    # C.LHU: unsigned halfword load
    await decode(dut, rv32c.encode_c_lhu(0, 1, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b101  # halfword unsigned

    # C.LH: signed halfword load
    await decode(dut, rv32c.encode_c_lh(0, 1, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b001  # halfword signed

    # C.SB: byte store
    await decode(dut, rv32c.encode_c_sb(1, 2, 0))
    assert dut.is_store.value == 1
    assert dut.mem_opcode.value == 0b000  # byte

    # C.SH: halfword store
    await decode(dut, rv32c.encode_c_sh(1, 2, 0))
    assert dut.is_store.value == 1
    assert dut.mem_opcode.value == 0b001  # halfword


# === Quadrant 1 ===


@cocotb.test()
async def c_nop(dut):
    """C.NOP: is_alu_imm, rd=x0, imm=0"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_nop())
    assert dut.is_alu_imm.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.rd.value) == 0
    assert int(dut.imm.value) == 0


@cocotb.test()
async def c_addi_rd_rs1_immediate(dut):
    """C.ADDI: rd==rs1, is_alu_imm, ADD opcode"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_addi(5, 3))
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b0000  # ADD
    assert int(dut.rd.value) == 5
    assert int(dut.rs1.value) == 5
    assert int(dut.imm.value) == 3


@cocotb.test()
async def c_jal_rd_is_ra(dut):
    """C.JAL: is_jal, rd=x1 (ra)"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_jal(64))
    assert dut.is_jal.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.rd.value) == 1  # ra


@cocotb.test()
async def c_li_rs1_is_x0(dut):
    """C.LI: is_alu_imm, rs1=x0, rd=dest"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_li(6, 5))
    assert dut.is_alu_imm.value == 1
    assert int(dut.rs1.value) == 0
    assert int(dut.rd.value) == 6
    assert int(dut.imm.value) == 5


@cocotb.test()
async def c_lui_is_lui(dut):
    """C.LUI: is_lui, rd, upper immediate placed at [31:12]"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_lui(7, 1 << 12))  # nzimm[16:12]=1 -> imm=0x1000
    assert dut.is_lui.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.rd.value) == 7
    imm = int(dut.imm.value)
    assert imm == 0x1000, f"expected 0x1000, got {hex(imm)}"


@cocotb.test()
async def c_addi16sp_immediate_scale(dut):
    """C.ADDI16SP: is_alu_imm, rd=rs1=sp(x2), scrambled immediate reconstructed"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_addi16sp(16))
    assert dut.is_alu_imm.value == 1
    assert int(dut.rd.value) == 2  # sp
    assert int(dut.rs1.value) == 2  # sp
    assert int(dut.imm.value) == 16, f"expected 16, got {int(dut.imm.value)}"


@cocotb.test()
async def c_srli_opcode(dut):
    """C.SRLI: is_alu_imm, SRL opcode, rd'==rs1'"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_srli(0, 4))  # rd_p=0->x8
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b0101  # SRL
    assert int(dut.rd.value) == 0b1000  # x8
    assert int(dut.rs1.value) == 0b1000  # x8


@cocotb.test()
async def c_srai_opcode(dut):
    """C.SRAI: is_alu_imm, SRA opcode"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_srai(0, 4))
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b1101  # SRA


@cocotb.test()
async def c_andi_opcode(dut):
    """C.ANDI: is_alu_imm, AND opcode"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_andi(0, 7))
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b0111  # AND


@cocotb.test()
async def c_sub_cxor_cor_cand_opcodes(dut):
    """C.SUB/XOR/OR/AND: is_alu_reg, correct alu_opcode"""
    await setup(dut)
    cases = [
        (rv32c.encode_c_sub, 0b1000),  # SUB
        (rv32c.encode_c_xor, 0b0100),  # XOR
        (rv32c.encode_c_or, 0b0110),  # OR
        (rv32c.encode_c_and, 0b0111),  # AND
    ]
    for enc, expected_opcode in cases:
        await decode(dut, enc(0, 1))  # rd_p=0->x8, rs2_p=1->x9
        assert dut.is_alu_reg.value == 1, f"{enc.__name__}: is_alu_reg not set"
        assert int(dut.alu_opcode.value) == expected_opcode, (
            f"{enc.__name__}: expected {bin(expected_opcode)}, got {bin(int(dut.alu_opcode.value))}"
        )


@cocotb.test()
async def c_j_rd_is_x0(dut):
    """C.J: is_jal, rd=x0 (discard)"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_j(64))
    assert dut.is_jal.value == 1
    assert int(dut.rd.value) == 0


@cocotb.test()
async def c_beqz_branch_and_xor_opcode(dut):
    """C.BEQZ: is_branch, alu_opcode=XOR, rs1'"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_beqz(0, 8))  # rs1_p=0->x8
    assert dut.is_branch.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.alu_opcode.value) == 0b0100  # XOR
    assert int(dut.rs1.value) == 0b1000  # x8


@cocotb.test()
async def c_bnez_branch_and_xor_opcode(dut):
    """C.BNEZ: is_branch, alu_opcode=XOR, rs1'"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_bnez(0, 8))
    assert dut.is_branch.value == 1
    assert int(dut.alu_opcode.value) == 0b0100  # XOR


# === Quadrant 2 ===


@cocotb.test()
async def c_slli_opcode(dut):
    """C.SLLI: is_alu_imm, SLL opcode, rd==rs1"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_slli(5, 3))
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b0001  # SLL
    assert int(dut.rd.value) == 5
    assert int(dut.rs1.value) == 5


@cocotb.test()
async def c_lwsp_sp_as_rs1(dut):
    """C.LWSP: is_load, rs1=sp(x2)"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_lwsp(5, 0))
    assert dut.is_load.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.rs1.value) == 2  # sp
    assert int(dut.rd.value) == 5


@cocotb.test()
async def c_jr_rs1_rd_x0(dut):
    """C.JR: is_jalr, rd=x0"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_jr(5))
    assert dut.is_jalr.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.rd.value) == 0
    assert int(dut.rs1.value) == 5


@cocotb.test()
async def c_mv_is_alu_reg(dut):
    """C.MV: is_alu_reg, ADD opcode, rs1=x0"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_mv(5, 3))
    assert dut.is_alu_reg.value == 1
    assert int(dut.alu_opcode.value) == 0b0000  # ADD (rd = x0 + rs2)
    assert int(dut.rd.value) == 5
    assert int(dut.rs1.value) == 0


@cocotb.test()
async def c_add_rd_rs1_same(dut):
    """C.ADD: is_alu_reg, ADD opcode, rd==rs1"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_add(5, 3))
    assert dut.is_alu_reg.value == 1
    assert int(dut.alu_opcode.value) == 0b0000  # ADD
    assert int(dut.rd.value) == 5
    assert int(dut.rs1.value) == 5


@cocotb.test()
async def c_jalr_rd_is_ra(dut):
    """C.JALR: is_jalr, rd=x1 (ra)"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_jalr(5))
    assert dut.is_jalr.value == 1
    assert int(dut.rd.value) == 1  # ra
    assert int(dut.rs1.value) == 5


@cocotb.test()
async def c_mul_nonstandard_opcode(dut):
    """C.MUL: Q2 funct3=101, alu_opcode=1010"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_mul(8, 9))  # rd_p=0->x8, rs2_p=1->x9
    assert dut.is_compressed.value == 1
    assert int(dut.alu_opcode.value) == 0b1010  # MUL


@cocotb.test()
async def c_swsp_sp_as_rs1(dut):
    """C.SWSP: is_store, rs1=sp(x2)"""
    await setup(dut)
    await decode(dut, rv32c.encode_c_swsp(5, 0))
    assert dut.is_store.value == 1
    assert dut.is_compressed.value == 1
    assert int(dut.rs1.value) == 2  # sp


# === Register encoding ===


@cocotb.test()
async def prime_register_decode_x8_to_x15(dut):
    """Compressed prime register fields (3-bit) map to x8-x15"""
    await setup(dut)
    for i in range(8):
        await decode(dut, rv32c.encode_c_lw(i, 0, 0))
        assert int(dut.rd.value) == 8 + i, (
            f"rd_p={i}: expected x{8 + i}, got x{int(dut.rd.value)}"
        )


@cocotb.test()
async def full_register_decode_x0_to_x15(dut):
    """Full register fields (4-bit) in Q2 instructions map to x0-x15"""
    await setup(dut)
    for i in range(1, 16):  # rd=0 is special (C.JR), skip
        await decode(dut, rv32c.encode_c_slli(i, 1))
        assert int(dut.rd.value) == i, (
            f"rd={i}: expected x{i}, got x{int(dut.rd.value)}"
        )


# === is_compressed flag ===


@cocotb.test()
async def compressed_flag_set_for_all_q0_q1_q2(dut):
    """is_compressed=1 for Q0/Q1/Q2, =0 for 32-bit"""
    await setup(dut)
    for instr_val in [
        rv32c.encode_c_lw(0, 0, 0),  # Q0
        rv32c.encode_c_addi(1, 1),  # Q1
        rv32c.encode_c_slli(1, 1),  # Q2
    ]:
        await decode(dut, instr_val)
        assert dut.is_compressed.value == 1, (
            f"instr={hex(instr_val)}: is_compressed not set"
        )


@cocotb.test()
async def compressed_flag_clear_for_32bit(dut):
    """is_compressed=0 for any 32-bit instruction (bits[1:0]=11)"""
    await setup(dut)
    await decode(dut, 0x00000013)  # NOP (ADDI x0, x0, 0)
    assert dut.is_compressed.value == 0
