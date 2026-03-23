# ==========================================================
# === RV32I Base (32-bit) Instruction Encoding Functions ===
# ==========================================================


def encode_r_type(funct7, rs2, rs1, funct3, rd, opcode):
    """
    Encode R-type:
    funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    """
    return (
        (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
    )


def encode_i_type(imm, rs1, funct3, rd, opcode):
    """
    Encode I-type:
    imm[31:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    """
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def encode_s_type(imm, rs2, rs1, funct3, opcode):
    """
    Encode S-type:
    imm[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | imm[11:7] | opcode[6:0]
    """
    return (
        (((imm >> 5) & 0x7F) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | ((imm & 0x1F) << 7)
        | opcode
    )


def encode_b_type(imm, rs2, rs1, funct3, opcode):
    """
    Encode B-type:
    imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode
    """
    return (
        (((imm >> 12) & 1) << 31)
        | (((imm >> 5) & 0x3F) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (((imm >> 1) & 0xF) << 8)
        | (((imm >> 11) & 1) << 7)
        | opcode
    )


def encode_u_type(imm, rd, opcode):
    """
    Encode U-type:
    imm[31:12] | rd[11:7] | opcode[6:0]
    """
    return ((imm & 0xFFFFF) << 12) | (rd << 7) | opcode


def encode_j_type(imm, rd, opcode):
    """
    Encode J-type:
    imm[20|10:1|11|19:12] | rd | opcod
    """
    return (
        (((imm >> 20) & 1) << 31)
        | (((imm >> 1) & 0x3FF) << 21)
        | (((imm >> 11) & 1) << 20)
        | (((imm >> 12) & 0xFF) << 12)
        | (rd << 7)
        | opcode
    )


# =================================
# === RV32I 32-bit Instructions ===
# =================================
# === R-Type ALU Operations     ===
# =================================


def encode_add(rd, rs1, rs2):
    """
    Addition (R-Type)
    ADD rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x0, rd, 0x33)


def encode_sub(rd, rs1, rs2):
    """
    Subtraction (R-Type)
    SUB rd, rs1, rs2
    """
    return encode_r_type(0x20, rs2, rs1, 0x0, rd, 0x33)


def encode_and(rd, rs1, rs2):
    """
    Bitwise AND (R-Type)
    AND rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x7, rd, 0x33)


def encode_or(rd, rs1, rs2):
    """
    Bitwise OR (R-Type)
    OR rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x6, rd, 0x33)


def encode_xor(rd, rs1, rs2):
    """
    Bitwise XOR (R-Type)
    XOR rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x4, rd, 0x33)


def encode_sll(rd, rs1, rs2):
    """
    Shift Left Logical (R-Type)
    SLL rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x1, rd, 0x33)


def encode_srl(rd, rs1, rs2):
    """
    Shift Right Logical (R-Type)
    SRL rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x5, rd, 0x33)


def encode_sra(rd, rs1, rs2):
    """
    Shift Right Arithmetic (R-Type)
    SRA rd, rs1, rs2
    """
    return encode_r_type(0x20, rs2, rs1, 0x5, rd, 0x33)


def encode_slt(rd, rs1, rs2):
    """
    Set Less Than (R-Type)
    SLT rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x2, rd, 0x33)


def encode_sltu(rd, rs1, rs2):
    """
    Set Less Than Unsigned (R-Type)
    SLTU rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, 0x3, rd, 0x33)


# --- I-Type ALU Operations ---


def encode_addi(rd, rs1, imm):
    """
    Add Immediate (I-Type)
    ADDI rd, rs1, imm
    """
    return encode_i_type(imm, rs1, 0x0, rd, 0x13)


def encode_andi(rd, rs1, imm):
    """
    AND Immediate (I-Type)
    ANDI rd, rs1, imm
    """
    return encode_i_type(imm, rs1, 0x7, rd, 0x13)


def encode_ori(rd, rs1, imm):
    """
    OR Immediate (I-Type)
    ORI rd, rs1, imm
    """
    return encode_i_type(imm, rs1, 0x6, rd, 0x13)


def encode_xori(rd, rs1, imm):
    """
    XOR Immediate (I-Type)
    XORI rd, rs1, imm
    """
    return encode_i_type(imm, rs1, 0x4, rd, 0x13)


def encode_slti(rd, rs1, imm):
    """
    Set Less Than Immediate (I-Type)
    SLTI rd, rs1, imm
    """
    return encode_i_type(imm, rs1, 0x2, rd, 0x13)


def encode_sltiu(rd, rs1, imm):
    """
    Set Less Than Immediate Unsigned (I-Type)
    SLTIU rd, rs1, imm
    """
    return encode_i_type(imm, rs1, 0x3, rd, 0x13)


def encode_slli(rd, rs1, shamt):
    """
    Shift Left Logical Immediate (I-Type)
    SLLI rd, rs1, shamt
    """
    return encode_i_type(shamt & 0x1F, rs1, 0x1, rd, 0x13)


def encode_srli(rd, rs1, shamt):
    """
    Shift Right Logical Immediate (I-Type)
    SRLI rd, rs1, shamt
    """
    return encode_i_type(shamt & 0x1F, rs1, 0x5, rd, 0x13)


def encode_srai(rd, rs1, shamt):
    """
    Shift Right Arithmetic Immediate (I-Type)
    SRAI rd, rs1, shamt
    """
    return encode_i_type(0x400 | (shamt & 0x1F), rs1, 0x5, rd, 0x13)


# =======================
# === Load Operations ===
# ========================


def encode_lw(rd, rs1, imm):
    """
    Load Word (I-Type)
    LW rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x2, rd, 0x03)


def encode_lh(rd, rs1, imm):
    """
    Load Halfword (I-Type)
    LH rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x1, rd, 0x03)


def encode_lb(rd, rs1, imm):
    """
    Load Byte (I-Type)
    LB rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x0, rd, 0x03)


def encode_lbu(rd, rs1, imm):
    """
    Load Byte Unsigned (I-Type)
    LBU rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x4, rd, 0x03)


def encode_lhu(rd, rs1, imm):
    """
    Load Halfword Unsigned (I-Type)
    LHU rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x5, rd, 0x03)


# ========================
# === Store Operations ===
# ========================


def encode_sw(rs1, rs2, imm):
    """
    Store Word (S-Type)
    SW rs2, imm(rs1)
    """
    return encode_s_type(imm, rs2, rs1, 0x2, 0x23)


def encode_sh(rs1, rs2, imm):
    """
    Store Halfword (S-Type)
    SH rs2, imm(rs1)
    """
    return encode_s_type(imm, rs2, rs1, 0x1, 0x23)


def encode_sb(rs1, rs2, imm):
    """
    Store Byte (S-Type)
    SB rs2, imm(rs1)
    """
    return encode_s_type(imm, rs2, rs1, 0x0, 0x23)


# =======================
# === Jump Operations ===
# =======================


def encode_jal(rd, imm):
    """
    Jump and Link (J-Type)
    JAL rd, offset
    """
    return encode_j_type(imm, rd, 0x6F)


def encode_jalr(rd, rs1, imm):
    """
    Jump and Link Register (I-Type)
    JALR rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x0, rd, 0x67)


# =========================
# === Branch Operations ===
# =========================


def encode_beq(rs1, rs2, imm):
    """
    Branch if Equal (B-Type)
    BEQ rs1, rs2, offset
    """
    return encode_b_type(imm, rs2, rs1, 0x0, 0x63)


def encode_bne(rs1, rs2, imm):
    """
    Branch if Not Equal (B-Type)
    BNE rs1, rs2, offset
    """
    return encode_b_type(imm, rs2, rs1, 0x1, 0x63)


def encode_blt(rs1, rs2, imm):
    """
    Branch if Less Than (B-Type)
    BLT rs1, rs2, offset
    """
    return encode_b_type(imm, rs2, rs1, 0x4, 0x63)


def encode_bge(rs1, rs2, imm):
    """
    Branch if Greater Than or Equal (B-Type)
    BGE rs1, rs2, offset
    """
    return encode_b_type(imm, rs2, rs1, 0x5, 0x63)


def encode_bltu(rs1, rs2, imm):
    """
    Branch if Less Than Unsigned (B-Type)
    BLTU rs1, rs2, offset
    """
    return encode_b_type(imm, rs2, rs1, 0x6, 0x63)


def encode_bgeu(rs1, rs2, imm):
    """
    Branch if Greater Than or Equal Unsigned (B-Type)
    BGEU rs1, rs2, offset
    """
    return encode_b_type(imm, rs2, rs1, 0x7, 0x63)


# ==================================
# === Upper Immediate Operations ===
# ==================================


def encode_lui(rd, imm):
    """
    Load Upper Immediate (U-Type)
    LUI rd, imm
    """
    return encode_u_type(imm, rd, 0x37)


def encode_auipc(rd, imm):
    """
    Add Upper Immediate to PC (U-Type)
    AUIPC rd, imm
    """
    return encode_u_type(imm, rd, 0x17)


# =========================
# === System Operations ===
# =========================


def encode_ecall():
    """
    Environment Call (I-Type)
    ECALL
    """
    return 0x73


def encode_ebreak():
    """
    Environment Break (I-Type)
    EBREAK
    """
    return 0x00100073


def encode_fence(pred, succ):
    """
    Memory Fence (I-Type)
    FENCE pred, succ
    """
    return encode_i_type((pred << 4) | succ, 0, 0x0, 0, 0x0F)


def encode_fence_i():
    """
    Instruction Fence (I-Type)
    FENCE.I
    """
    return encode_i_type(0, 0, 0x1, 0, 0x0F)


def encode_mret():
    """
    Machine Return (Privileged)
    MRET
    """
    return 0x30200073


def encode_wfi():
    """
    Wait For Interrupt (Privileged)
    WFI
    """
    return 0x10500073


# ======================
# === CSR Operations ===
# ======================


def encode_csrrw(rd, rs1, csr):
    """
    CSR Read and Write (I-Type)
    CSRRW rd, csr, rs1
    """
    return encode_i_type(csr, rs1, 0x1, rd, 0x73)


def encode_csrrs(rd, rs1, csr):
    """
    CSR Read and Set (I-Type)
    CSRRS rd, csr, rs1
    """
    return encode_i_type(csr, rs1, 0x2, rd, 0x73)


def encode_csrrc(rd, rs1, csr):
    """
    CSR Read and Clear (I-Type)
    CSRRC rd, csr, rs1
    """
    return encode_i_type(csr, rs1, 0x3, rd, 0x73)


def encode_csrrwi(rd, uimm, csr):
    """
    CSR Read and Write Immediate (I-Type)
    CSRRWI rd, csr, uimm
    """
    return encode_i_type(csr, uimm & 0x1F, 0x5, rd, 0x73)


def encode_csrrsi(rd, uimm, csr):
    """
    CSR Read and Set Immediate (I-Type)
    CSRRSI rd, csr, uimm
    """
    return encode_i_type(csr, uimm & 0x1F, 0x6, rd, 0x73)


def encode_csrrci(rd, uimm, csr):
    """
    CSR Read and Clear Immediate (I-Type)
    CSRRCI rd, csr, uimm
    """
    return encode_i_type(csr, uimm & 0x1F, 0x7, rd, 0x73)


# ================================================================================
# === RV32F Floating Point Instructions (Not Used - Included for Completeness) ===
# ================================================================================


def _encode_flw(rd, rs1, imm):  # Not used
    """
    Floating-Point Load Word (I-Type)
    FLW rd, imm(rs1)
    """
    return encode_i_type(imm, rs1, 0x2, rd, 0x07)


def _encode_fsw(rs1, rs2, imm):  # Not used
    """
    Floating-Point Store Word (S-Type)
    FSW rs2, imm(rs1)
    """
    return encode_s_type(imm, rs2, rs1, 0x2, 0x27)


def _encode_fadd_s(rd, rs1, rs2, rm=0b000):  # Not used
    """
    Floating-Point Add Single (R-Type)
    FADD.S rd, rs1, rs2
    """
    return encode_r_type(0x00, rs2, rs1, rm, rd, 0x53)


def _encode_fsub_s(rd, rs1, rs2, rm=0b000):  # Not used
    """
    Floating-Point Subtract Single (R-Type)
    FSUB.S rd, rs1, rs2
    """
    return encode_r_type(0x04, rs2, rs1, rm, rd, 0x53)


def _encode_fmul_s(rd, rs1, rs2, rm=0b000):  # Not used
    """
    Floating-Point Multiply Single (R-Type)
    FMUL.S rd, rs1, rs2
    """
    return encode_r_type(0x08, rs2, rs1, rm, rd, 0x53)


def _encode_fdiv_s(rd, rs1, rs2, rm=0b000):  # Not used
    """
    Floating-Point Divide Single (R-Type)
    FDIV.S rd, rs1, rs2
    """
    return encode_r_type(0x0C, rs2, rs1, rm, rd, 0x53)


def _encode_fsqrt_s(rd, rs1, rm=0b000):  # Not used
    """
    Floating-Point Square Root Single (R-Type)
    FSQRT.S rd, rs1
    """
    return encode_r_type(0x2C, 0, rs1, rm, rd, 0x53)


def _encode_fmin_s(rd, rs1, rs2):  # Not used
    """
    Floating-Point Minimum Single (R-Type)
    FMIN.S rd, rs1, rs2
    """
    return encode_r_type(0x14, rs2, rs1, 0x0, rd, 0x53)


def _encode_fmax_s(rd, rs1, rs2):  # Not used
    """
    Floating-Point Maximum Single (R-Type)
    FMAX.S rd, rs1, rs2
    """
    return encode_r_type(0x14, rs2, rs1, 0x1, rd, 0x53)


def _encode_feq_s(rd, rs1, rs2):  # Not used
    """
    Floating-Point Equal Single (R-Type)
    FEQ.S rd, rs1, rs2
    """
    return encode_r_type(0x50, rs2, rs1, 0x2, rd, 0x53)


def _encode_flt_s(rd, rs1, rs2):  # Not used
    """
    Floating-Point Less Than Single (R-Type)
    FLT.S rd, rs1, rs2
    """
    return encode_r_type(0x50, rs2, rs1, 0x1, rd, 0x53)


def _encode_fle_s(rd, rs1, rs2):  # Not used
    """
    Floating-Point Less Than or Equal Single (R-Type)
    FLE.S rd, rs1, rs2
    """
    return encode_r_type(0x50, rs2, rs1, 0x0, rd, 0x53)
