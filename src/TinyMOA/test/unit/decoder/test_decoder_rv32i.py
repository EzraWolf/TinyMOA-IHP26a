"""
Test suite for decoding RV32I instructions
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import utility.rv32i_encode as rv32i


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    dut.nrst.value = 0
    await ClockCycles(dut.clk, 1)
    dut.nrst.value = 1


async def decode(dut, instr_val):
    dut.instr.value = instr_val
    await ClockCycles(dut.clk, 1)


# === Loads ===


@cocotb.test()
async def load_byte_signed(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lb(1, 2, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b000


@cocotb.test()
async def load_halfword_signed(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lh(1, 2, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b001


@cocotb.test()
async def load_word(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lw(1, 2, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b010


@cocotb.test()
async def load_byte_unsigned(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lbu(1, 2, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b100


@cocotb.test()
async def load_halfword_unsigned(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lhu(1, 2, 0))
    assert dut.is_load.value == 1
    assert dut.mem_opcode.value == 0b101


@cocotb.test()
async def load_immediate_sign_extension(dut):
    """Negative immediate sign-extends to 32 bits"""
    await setup(dut)
    await decode(dut, rv32i.encode_lw(1, 2, -4))
    imm = int(dut.imm.value)
    assert imm == 0xFFFFFFFC, f"expected 0xFFFFFFFC, got {hex(imm)}"


@cocotb.test()
async def load_register_fields(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lw(5, 3, 8))
    assert int(dut.rd.value) == 5, f"rd: expected 5, got {int(dut.rd.value)}"
    assert int(dut.rs1.value) == 3, f"rs1: expected 3, got {int(dut.rs1.value)}"
    assert int(dut.imm.value) == 8


# === Stores ===


@cocotb.test()
async def store_byte(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_sb(2, 3, 0))
    assert dut.is_store.value == 1
    assert dut.mem_opcode.value == 0b000


@cocotb.test()
async def store_halfword(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_sh(2, 3, 0))
    assert dut.is_store.value == 1
    assert dut.mem_opcode.value == 0b001


@cocotb.test()
async def store_word(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_sw(2, 3, 0))
    assert dut.is_store.value == 1
    assert dut.mem_opcode.value == 0b010


@cocotb.test()
async def store_immediate_reconstruction(dut):
    """S-type imm is split across [31:25] and [11:7] -- decoder must reassemble"""
    await setup(dut)
    await decode(dut, rv32i.encode_sw(2, 3, -8))
    imm = int(dut.imm.value)
    assert imm == 0xFFFFFFF8, f"expected 0xFFFFFFF8, got {hex(imm)}"


@cocotb.test()
async def store_register_fields(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_sw(3, 5, 4))
    assert int(dut.rs1.value) == 3, f"rs1: expected 3, got {int(dut.rs1.value)}"
    assert int(dut.rs2.value) == 5, f"rs2: expected 5, got {int(dut.rs2.value)}"
    assert int(dut.imm.value) == 4


# === ALU immediate ===


@cocotb.test()
async def addi_basic(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_addi(1, 2, 10))
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b0000  # ADD
    assert int(dut.imm.value) == 10


@cocotb.test()
async def addi_immediate_min_max(dut):
    """ADDI with +2047 and -2048"""
    await setup(dut)
    await decode(dut, rv32i.encode_addi(1, 0, 2047))
    assert int(dut.imm.value) == 2047
    await decode(dut, rv32i.encode_addi(1, 0, -2048))
    imm = int(dut.imm.value)
    assert imm == 0xFFFFF800, f"expected 0xFFFFF800, got {hex(imm)}"


@cocotb.test()
async def slti_sltiu(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_slti(1, 2, 0))
    assert dut.is_alu_imm.value == 1
    assert int(dut.alu_opcode.value) == 0b0010  # SLT
    await decode(dut, rv32i.encode_sltiu(1, 2, 0))
    assert int(dut.alu_opcode.value) == 0b0011  # SLTU


@cocotb.test()
async def xori_ori_andi(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_xori(1, 2, 0))
    assert int(dut.alu_opcode.value) == 0b0100  # XOR
    await decode(dut, rv32i.encode_ori(1, 2, 0))
    assert int(dut.alu_opcode.value) == 0b0110  # OR
    await decode(dut, rv32i.encode_andi(1, 2, 0))
    assert int(dut.alu_opcode.value) == 0b0111  # AND


@cocotb.test()
async def slli_srli_srai_opcode(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_slli(1, 2, 4))
    assert int(dut.alu_opcode.value) == 0b0001  # SLL
    await decode(dut, rv32i.encode_srli(1, 2, 4))
    assert int(dut.alu_opcode.value) == 0b0101  # SRL
    await decode(dut, rv32i.encode_srai(1, 2, 4))
    assert int(dut.alu_opcode.value) == 0b1101  # SRA


@cocotb.test()
async def srai_vs_srli_funct7(dut):
    """SRAI and SRLI share funct3=101 -- funct7 bit distinguishes them"""
    await setup(dut)
    await decode(dut, rv32i.encode_srli(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0101  # SRL
    await decode(dut, rv32i.encode_srai(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b1101  # SRA


# === ALU reg-reg ===


@cocotb.test()
async def add_sub_funct7_distinguishes(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_add(1, 2, 3))
    assert dut.is_alu_reg.value == 1
    assert int(dut.alu_opcode.value) == 0b0000  # ADD
    await decode(dut, rv32i.encode_sub(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b1000  # SUB


@cocotb.test()
async def shift_opcodes(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_sll(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0001  # SLL
    await decode(dut, rv32i.encode_srl(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0101  # SRL
    await decode(dut, rv32i.encode_sra(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b1101  # SRA


@cocotb.test()
async def logical_opcodes(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_and(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0111  # AND
    await decode(dut, rv32i.encode_or(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0110  # OR
    await decode(dut, rv32i.encode_xor(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0100  # XOR


@cocotb.test()
async def slt_sltu_opcodes(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_slt(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0010  # SLT
    await decode(dut, rv32i.encode_sltu(1, 2, 3))
    assert int(dut.alu_opcode.value) == 0b0011  # SLTU


# === Zicond ===


@cocotb.test()
async def czero_eqz_opcode(dut):
    """CZERO.EQZ: funct7=0x07, funct3=5, OP"""
    await setup(dut)
    await decode(dut, rv32i.encode_r_type(0x07, 3, 2, 0x5, 1, 0x33))
    assert dut.is_alu_reg.value == 1
    assert int(dut.alu_opcode.value) == 0b1110  # CZERO.EQZ


@cocotb.test()
async def czero_nez_opcode(dut):
    """CZERO.NEZ: funct7=0x07, funct3=7, OP"""
    await setup(dut)
    await decode(dut, rv32i.encode_r_type(0x07, 3, 2, 0x7, 1, 0x33))
    assert dut.is_alu_reg.value == 1
    assert int(dut.alu_opcode.value) == 0b1111  # CZERO.NEZ


# === Branches ===


@cocotb.test()
async def branch_all_types(dut):
    """All six branch types set is_branch and correct alu_opcode"""
    await setup(dut)
    cases = [
        (rv32i.encode_beq, 0b0100),  # XOR for equality
        (rv32i.encode_bne, 0b0100),  # XOR
        (rv32i.encode_blt, 0b0010),  # SLT
        (rv32i.encode_bge, 0b0010),  # SLT
        (rv32i.encode_bltu, 0b0011),  # SLTU
        (rv32i.encode_bgeu, 0b0011),  # SLTU
    ]
    for enc, expected_opcode in cases:
        await decode(dut, enc(1, 2, 0))
        assert dut.is_branch.value == 1, f"{enc.__name__}: is_branch not set"
        assert int(dut.alu_opcode.value) == expected_opcode, (
            f"{enc.__name__}: expected {bin(expected_opcode)}, got {bin(int(dut.alu_opcode.value))}"
        )


@cocotb.test()
async def branch_immediate_sign_extension(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_beq(1, 2, -8))
    imm = int(dut.imm.value)
    assert imm == 0xFFFFFFF8, f"expected 0xFFFFFFF8, got {hex(imm)}"


@cocotb.test()
async def branch_immediate_max_min(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_beq(1, 2, 4094))
    assert int(dut.imm.value) == 4094
    await decode(dut, rv32i.encode_beq(1, 2, -4096))
    imm = int(dut.imm.value)
    assert imm == 0xFFFFF000, f"expected 0xFFFFF000, got {hex(imm)}"


# === Jumps ===


@cocotb.test()
async def jal_immediate_encoding(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_jal(1, 256))
    assert dut.is_jal.value == 1
    assert int(dut.imm.value) == 256


@cocotb.test()
async def jal_rd_zero(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_jal(0, 16))
    assert dut.is_jal.value == 1
    assert int(dut.rd.value) == 0


@cocotb.test()
async def jalr_immediate_and_rs1(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_jalr(1, 3, 12))
    assert dut.is_jalr.value == 1
    assert int(dut.rs1.value) == 3
    assert int(dut.imm.value) == 12


# === Upper immediate ===


@cocotb.test()
async def lui_immediate_lower_zeros(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_lui(1, 0xABCDE))
    assert dut.is_lui.value == 1
    imm = int(dut.imm.value)
    assert imm == 0xABCDE000, f"expected 0xABCDE000, got {hex(imm)}"
    assert (imm & 0xFFF) == 0


@cocotb.test()
async def auipc_immediate_lower_zeros(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_auipc(1, 0x12345))
    assert dut.is_auipc.value == 1
    imm = int(dut.imm.value)
    assert imm == 0x12345000, f"expected 0x12345000, got {hex(imm)}"
    assert (imm & 0xFFF) == 0


# === System / other ===


@cocotb.test()
async def fence_is_nop(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_fence(0xF, 0xF))
    assert dut.is_load.value == 0
    assert dut.is_store.value == 0
    assert dut.is_branch.value == 0
    assert dut.is_alu_imm.value == 0
    assert dut.is_alu_reg.value == 0
    assert dut.is_jal.value == 0
    assert dut.is_jalr.value == 0
    assert dut.is_lui.value == 0
    assert dut.is_auipc.value == 0
    assert dut.is_system.value == 0
    assert dut.is_compressed.value == 0


@cocotb.test()
async def jal_negative_immediate(dut):
    """JAL J-type scrambled immediate with negative offset"""
    await setup(dut)
    await decode(dut, rv32i.encode_jal(1, -256))
    assert dut.is_jal.value == 1
    imm = int(dut.imm.value)
    assert imm == 0xFFFFFF00, f"expected 0xFFFFFF00, got {hex(imm)}"


@cocotb.test()
async def ecall_ebreak_is_system(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_ecall())
    assert dut.is_system.value == 1
    await decode(dut, rv32i.encode_ebreak())
    assert dut.is_system.value == 1


@cocotb.test()
async def all_zeros_instruction(dut):
    """All-zero instruction -- bits[1:0]=00 routes to compressed"""
    await setup(dut)
    await decode(dut, 0x00000000)
    assert dut.is_compressed.value == 1
    assert dut.is_load.value == 0
    assert dut.is_store.value == 0


@cocotb.test()
async def bits_not_11_routes_to_compressed(dut):
    await setup(dut)
    await decode(dut, 0x00000001)  # bits[1:0]=01
    assert dut.is_compressed.value == 1
    await decode(dut, 0x00000002)  # bits[1:0]=10
    assert dut.is_compressed.value == 1
    await decode(dut, 0x00000003)  # bits[1:0]=11
    assert dut.is_compressed.value == 0
