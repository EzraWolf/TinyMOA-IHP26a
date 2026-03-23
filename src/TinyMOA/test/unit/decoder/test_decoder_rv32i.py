"""
Test suite for decoding RV32I instructions.

Every test verifies ALL control lines: imm, alu_opcode, mem_opcode, rs1, rs2, rd,
the correct is_* flag high, all others low, and is_compressed=0.

ALU internal opcodes (decoder assigns opcode):
    0000  ADD
    0001  SUB
    0010  SLT
    0011  SLTU
    0100  XOR
    0101  OR
    0110  AND
    1000  SLL
    1001  SRL
    1010  SRA
    1011  MUL  (16x16 unsigned -> 32-bit)
    1110  CZERO.EQZ
    1111  CZERO.NEZ

R-Type instructions:
    [31:25] funct7
    [24:20] rs2
    [19:15] rs1
    [14:12] funct3
    [11:7]  rd
    [6:0]   opcode

I-Type instructions:
    [31:20] imm[11:0]
    [19:15] rs1
    [14:12] funct3
    [11:7]  rd
    [6:0]   opcode

S-Type instructions:
    [31:25] imm[11:5]
    [24:20] rs2
    [19:15] rs1
    [14:12] funct3
    [11:7]  imm[4:0]
    [6:0]   opcode

B-Type instructions:
    [31]    imm[12]
    [30:25] imm[10:5]
    [24:20] rs2
    [19:15] rs1
    [14:12] funct3
    [11:8]  imm[4:1]
    [7]     imm[11]
    [6:0]   opcode

U-Type instructions:
    [31:11] imm[31:12]
    [11:7]  rd
    [6:0]   opcode

J-Type instructions:
    [31]    imm[20]
    [30:21] imm[10:1]
    [20]    imm[11]
    [19:12] imm[19:12]
    [11:7]  rd
    [6:0]   opcode

"""

import cocotb
from cocotb.triggers import Timer
import utility.rv32i_encode as rv32i

# mem_opcode encoding: [1:0]=size (00=byte, 01=half, 10=word), [2]=unsigned
MEM_BYTE = 0b000
MEM_HALF = 0b001
MEM_WORD = 0b010
MEM_BYTE_U = 0b100
MEM_HALF_U = 0b101


async def setup(dut):
    dut.instr.value = 0
    dut.imm.value = 0
    dut.alu_opcode.value = 0
    dut.mem_opcode.value = 0
    dut.rs1.value = 0
    dut.rs2.value = 0
    dut.rd.value = 0
    dut.is_load.value = 0
    dut.is_store.value = 0
    dut.is_branch.value = 0
    dut.is_jal.value = 0
    dut.is_jalr.value = 0
    dut.is_lui.value = 0
    dut.is_auipc.value = 0
    dut.is_system.value = 0
    dut.is_compressed.value = 0
    await Timer(1, unit="ns")


async def decode(dut, instr_val):
    dut.instr.value = instr_val
    await Timer(1, unit="ns")


def verify_flags(
    dut,
    *,
    is_alu_reg=0,
    is_alu_imm=0,
    is_load=0,
    is_store=0,
    is_branch=0,
    is_jal=0,
    is_jalr=0,
    is_lui=0,
    is_auipc=0,
    is_system=0,
    is_compressed=0,  # RV32I instr should always be low
):
    """Verify instruction control decode flags"""
    assert dut.is_alu_reg.value == is_alu_reg
    assert dut.is_alu_imm.value == is_alu_imm
    assert dut.is_load.value == is_load
    assert dut.is_store.value == is_store
    assert dut.is_branch.value == is_branch
    assert dut.is_jal.value == is_jal
    assert dut.is_jalr.value == is_jalr
    assert dut.is_lui.value == is_lui
    assert dut.is_auipc.value == is_auipc
    assert dut.is_system.value == is_system
    assert dut.is_compressed.value == is_compressed
    # assert dut.instr_len.value == 4, "Expected RV32I 32-bit instruction"


def verify_r_type(dut, alu_opcode, rd, rs1, rs2):
    """Verify R-type instruction decodes (opcode 0x33)"""
    assert dut.alu_opcode.value == alu_opcode, (
        f"ALU opcode mismatch: expected {alu_opcode:#06b}, got {dut.alu_opcode.value:#06b}"
    )
    assert dut.rd.value == rd, f"rd mismatch: expected x{rd}, got x{dut.rd.value}"
    assert dut.rs1.value == rs1, f"rs1 mismatch: expected x{rs1}, got x{dut.rs1.value}"
    assert dut.rs2.value == rs2, f"rs2 mismatch: expected x{rs2}, got x{dut.rs2.value}"
    verify_flags(dut, is_alu_reg=1)


def verify_i_type_alu(dut, alu_opcode, rd, rs1, imm):
    """Verify I-type ALU imm instruction decodes (opcode 0x13)"""
    assert dut.alu_opcode.value == alu_opcode, (
        f"ALU opcode mismatch: expected {alu_opcode:#06b}, got {dut.alu_opcode.value:#06b}"
    )
    assert dut.rd.value == rd, f"rd mismatch: expected x{rd}, got x{dut.rd.value}"
    assert dut.rs1.value == rs1, f"rs1 mismatch: expected x{rs1}, got x{dut.rs1.value}"
    assert dut.imm.value.to_signed() == imm, (
        f"Immediate mismatch: expected {imm}, got {dut.imm.value.to_signed()}"
    )
    verify_flags(dut, is_alu_imm=1)


def verify_i_type_shift(dut, alu_opcode, rd, rs1, shamt):
    """Verify I-type shift imm instruction decodes (opcode 0x13)"""
    assert dut.alu_opcode.value == alu_opcode, (
        f"ALU opcode mismatch: expected {alu_opcode:#06b}, got {dut.alu_opcode.value:#06b}"
    )
    assert dut.rd.value == rd, f"rd mismatch: expected x{rd}, got x{dut.rd.value}"
    assert dut.rs1.value == rs1, f"rs1 mismatch: expected x{rs1}, got x{dut.rs1.value}"
    assert (dut.imm.value.integer & 0x1F) == shamt, (
        f"Shift amount mismatch: expected {shamt}, got {dut.imm.value.integer & 0x1F}"
    )
    verify_flags(dut, is_alu_imm=1)


def verify_i_type_load(dut, mem_opcode, rd, rs1, imm):
    """Verify I-type load instruction decodes (opcode 0x03)"""
    assert dut.mem_opcode.value == mem_opcode, (
        f"Memory opcode mismatch: expected {mem_opcode:#05b}, got {dut.mem_opcode.value:#05b}"
    )
    assert dut.rd.value == rd, f"rd mismatch: expected x{rd}, got x{dut.rd.value}"
    assert dut.rs1.value == rs1, f"rs1 mismatch: expected x{rs1}, got x{dut.rs1.value}"
    assert dut.imm.value.to_signed() == imm, (
        f"Immediate mismatch: expected {imm}, got {dut.imm.value.to_signed()}"
    )
    verify_flags(dut, is_load=1)


def verify_s_type(dut, mem_opcode, rs1, rs2, imm):
    """Verify S-type store instruction decodes (opcode 0x23)"""
    assert dut.mem_opcode.value == mem_opcode, (
        f"Memory opcode mismatch: expected {mem_opcode:#05b}, got {dut.mem_opcode.value:#05b}"
    )
    assert dut.rs1.value == rs1, f"rs1 mismatch: expected x{rs1}, got x{dut.rs1.value}"
    assert dut.rs2.value == rs2, f"rs2 mismatch: expected x{rs2}, got x{dut.rs2.value}"
    assert dut.imm.value.to_signed() == imm, (
        f"Immediate mismatch: expected {imm}, got {dut.imm.value.to_signed()}"
    )
    verify_flags(dut, is_store=1)


def verify_u_type(dut, rd, imm, is_lui=False, is_auipc=False):
    """Verify U-type instruction decodes (LUI 0x37 or AUIPC 0x17)"""
    assert dut.rd.value == rd, f"rd mismatch: expected x{rd}, got x{dut.rd.value}"
    assert dut.imm.value.integer == imm, (
        f"Immediate mismatch: expected {imm:#x}, got {int(dut.imm.value):#x}"
    )
    verify_flags(dut, is_lui=(1 if is_lui else 0), is_auipc=(1 if is_auipc else 0))


def verify_b_type(dut, alu_opcode, rs1, rs2, imm):
    """Verify B-type branch instruction decodes (opcode 0x63)"""
    assert dut.alu_opcode.value == alu_opcode, (
        f"ALU opcode mismatch: expected {alu_opcode:#06b}, got {dut.alu_opcode.value:#06b}"
    )
    assert dut.rs1.value == rs1, f"rs1 mismatch: expected x{rs1}, got x{dut.rs1.value}"
    assert dut.rs2.value == rs2, f"rs2 mismatch: expected x{rs2}, got x{dut.rs2.value}"
    assert dut.imm.value.to_signed() == imm, (
        f"Immediate mismatch: expected {imm}, got {dut.imm.value.to_signed()}"
    )
    verify_flags(dut, is_branch=1)


def verify_j_type(dut, rd, imm, is_jal=False, is_jalr=False):
    """Verify J-type jump instruction decodes (JAL 0x6F or JALR 0x67)"""
    assert dut.rd.value == rd, f"rd mismatch: expected x{rd}, got x{dut.rd.value}"
    assert dut.imm.value.to_signed() == imm, (
        f"Immediate mismatch: expected {imm}, got {dut.imm.value.to_signed()}"
    )
    assert dut.alu_opcode.value == 0b0000, "Jump uses ADD for address calculation"
    verify_flags(dut, is_jal=(1 if is_jal else 0), is_jalr=(1 if is_jalr else 0))


def verify_system_type(dut):
    """Verify system instruction decodes (opcode 0x73)"""
    verify_flags(dut, is_system=1)


@cocotb.test()
async def test_add(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_add(rd=5, rs1=6, rs2=7))
    verify_r_type(dut, alu_opcode=0b0000, rd=5, rs1=6, rs2=7)


@cocotb.test()
async def test_sub(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_sub(rd=1, rs1=2, rs2=3))
    verify_r_type(dut, alu_opcode=0b0001, rd=1, rs1=2, rs2=3)


@cocotb.test(skip=True)
async def test_sll(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_slt(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_sltu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_xor(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_srl(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_sra(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_or(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test()
async def test_and(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_and(rd=8, rs1=9, rs2=10))
    verify_r_type(dut, alu_opcode=0b0110, rd=8, rs1=9, rs2=10)


@cocotb.test(skip=True)
async def test_czero_eqz(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_czero_nez(dut):
    await setup(dut)
    raise NotImplementedError


# === I-Type ===


@cocotb.test()
async def test_addi(dut):
    await setup(dut)
    await decode(dut, rv32i.encode_addi(rd=2, rs1=3, imm=100))
    verify_i_type_alu(dut, alu_opcode=0b0000, rd=2, rs1=3, imm=100)


@cocotb.test(skip=True)
async def test_slti(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_sltiu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_xori(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_ori(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_andi(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_slli(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_srli(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_srai(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_lb(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_lh(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_lw(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_lbu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_lhu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_jalr(dut):
    await setup(dut)
    raise NotImplementedError


# === S-Type ===


@cocotb.test(skip=True)
async def test_sb(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_sh(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_sw(dut):
    await setup(dut)
    raise NotImplementedError


# === B-Type ===


@cocotb.test(skip=True)
async def test_beq(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_bne(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_blt(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_bge(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_bltu(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_bgeu(dut):
    await setup(dut)
    raise NotImplementedError


# === U-Type ===


@cocotb.test(skip=True)
async def test_lui(dut):
    await setup(dut)
    raise NotImplementedError


@cocotb.test(skip=True)
async def test_auipc(dut):
    await setup(dut)
    raise NotImplementedError


# === J-Type ===


@cocotb.test(skip=True)
async def test_jal(dut):
    await setup(dut)
    raise NotImplementedError
