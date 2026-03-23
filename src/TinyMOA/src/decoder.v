// TinyMOA Combinational Instruction Decoder
//
// Decodes RV32I, C/Zca, Zcb, and Zicond from a 32-bit word.
// 16-bit compressed instructions arrive zero-extended to 32 bits.
//
// Compressed register fields (3-bit) map to x8-x15: rd = {1'b1, instr[N:M]}.
// C.MUL: Q1 CA-type (instr[15:13]=100, instr[12:10]=111, instr[6:5]=10), ALU opcode 4'b1010.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_decoder (
    input [31:0] instr,

    output reg  [31:0] imm,
    output reg  [3:0]  alu_opcode,
    output reg  [2:0]  mem_opcode, // [1:0]=size, [2]=unsigned
    output reg  [3:0]  rs1,
    output reg  [3:0]  rs2,
    output reg  [3:0]  rd,

    output reg         is_load,
    output reg         is_store,
    output reg         is_branch,
    output reg         is_jal,
    output reg         is_jalr,
    output reg         is_lui,
    output reg         is_auipc,
    output reg         is_alu_reg,
    output reg         is_alu_imm,
    output reg         is_system,
    output reg         is_compressed
);

    // 32-bit fields
    wire [4:0] opcode5 = instr[6:2];   // bits[1:0] == 2'b11 for all 32-bit insns
    wire [2:0] funct3  = instr[14:12];
    wire [6:0] funct7  = instr[31:25];
    wire [3:0] rs1_32  = instr[18:15]; // RV32E: only x0-x15 (4 bits)
    wire [3:0] rs2_32  = instr[23:20];
    wire [3:0] rd_32   = instr[10:7];

    // 16-bit compressed fields
    wire [1:0] c_quad  = instr[1:0];
    wire [2:0] c_f3    = instr[15:13];

    // Compressed register fields (prime registers: x8-x15)
    wire [3:0] c_rd_p  = {1'b1, instr[4:2]};
    wire [3:0] c_rs1_p = {1'b1, instr[9:7]};
    wire [3:0] c_rs2_p = {1'b1, instr[4:2]};

    // Full register fields for non-prime compressed (4-bit RV32E: bits[10:7])
    wire [3:0] c_rd_f  = instr[10:7];
    wire [3:0] c_rs1_f = instr[10:7];
    wire [3:0] c_rs2_f = instr[5:2];

    always @(*) begin
        imm           = 32'd0;
        alu_opcode    = 4'd0;
        mem_opcode    = 3'd0;
        rs1           = 4'd0;
        rs2           = 4'd0;
        rd            = 4'd0;
        is_load       = 1'b0;
        is_store      = 1'b0;
        is_branch     = 1'b0;
        is_jal        = 1'b0;
        is_jalr       = 1'b0;
        is_lui        = 1'b0;
        is_auipc      = 1'b0;
        is_alu_reg    = 1'b0;
        is_alu_imm    = 1'b0;
        is_system     = 1'b0;
        is_compressed = 1'b0;

        if (instr[1:0] == 2'b11) begin
            rs1 = rs1_32;
            rs2 = rs2_32;
            rd  = rd_32;
            case (opcode5)
                5'b00000: begin // LOAD
                    is_load    = 1'b1;
                    alu_opcode = 4'b0000; // ADD for EA
                    mem_opcode = funct3;
                    imm        = {{20{instr[31]}}, instr[31:20]};
                end
                5'b00100: begin // OP-IMM
                    is_alu_imm = 1'b1;
                    imm        = {{20{instr[31]}}, instr[31:20]};
                    case (funct3)
                        3'b000: alu_opcode = 4'b0000; // ADDI
                        3'b001: alu_opcode = 4'b0001; // SLLI
                        3'b010: alu_opcode = 4'b0010; // SLTI
                        3'b011: alu_opcode = 4'b0011; // SLTIU
                        3'b100: alu_opcode = 4'b0100; // XORI
                        3'b101: alu_opcode = instr[30] ? 4'b1101 : 4'b0101; // SRAI:SRLI
                        3'b110: alu_opcode = 4'b0110; // ORI
                        3'b111: alu_opcode = 4'b0111; // ANDI
                    endcase
                end
                5'b00101: begin // AUIPC
                    is_auipc   = 1'b1;
                    alu_opcode = 4'b0000;
                    imm        = {instr[31:12], 12'd0};
                end
                5'b01000: begin // STORE
                    is_store   = 1'b1;
                    alu_opcode = 4'b0000;
                    mem_opcode = funct3;
                    imm        = {{20{instr[31]}}, instr[31:25], instr[11:7]};
                end
                5'b01100: begin // OP (reg-reg, includes Zicond)
                    is_alu_reg = 1'b1;
                    if (funct7 == 7'h07) begin // Zicond
                        alu_opcode = {3'b111, funct3[1]}; // EQZ=1110, NEZ=1111
                    end else begin
                        case (funct3)
                            3'b000: alu_opcode = funct7[5] ? 4'b1000 : 4'b0000; // SUB:ADD
                            3'b001: alu_opcode = 4'b0001; // SLL
                            3'b010: alu_opcode = 4'b0010; // SLT
                            3'b011: alu_opcode = 4'b0011; // SLTU
                            3'b100: alu_opcode = 4'b0100; // XOR
                            3'b101: alu_opcode = funct7[5] ? 4'b1101 : 4'b0101; // SRA:SRL
                            3'b110: alu_opcode = 4'b0110; // OR
                            3'b111: alu_opcode = 4'b0111; // AND
                        endcase
                    end
                end
                5'b01101: begin // LUI
                    is_lui = 1'b1;
                    imm    = {instr[31:12], 12'd0};
                end
                5'b11000: begin // BRANCH
                    is_branch  = 1'b1;
                    imm        = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
                    case (funct3[2:1])
                        2'b00: alu_opcode = 4'b0100; // BEQ/BNE -> XOR
                        2'b10: alu_opcode = 4'b0010; // BLT/BGE  -> SLT
                        2'b11: alu_opcode = 4'b0011; // BLTU/BGEU -> SLTU
                        default: alu_opcode = 4'b0100;
                    endcase
                end
                5'b11001: begin // JALR
                    is_jalr    = 1'b1;
                    alu_opcode = 4'b0000;
                    imm        = {{20{instr[31]}}, instr[31:20]};
                end
                5'b11011: begin // JAL
                    is_jal = 1'b1;
                    imm    = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};
                end
                5'b11100: begin // SYSTEM (Zicsr stub: reads return 0, writes ignored)
                    is_system = 1'b1;
                end
                5'b00011: begin // FENCE/NOP in this implementation
                end
                default: begin end
            endcase
        end else begin
            is_compressed = 1'b1;
            case (c_quad)
                2'b00: begin
                    case (c_f3)
                        3'b000: begin // C.ADDI4SPN: rd' = sp + nzuimm*4
                            rd  = c_rd_p;
                            rs1 = 4'd2; // sp
                        end
                        3'b010: begin // C.LW
                            is_load    = 1'b1;
                            rd         = c_rd_p;
                            rs1        = c_rs1_p;
                            mem_opcode = 3'b010;
                            alu_opcode = 4'b0000;
                        end
                        3'b100: begin // Zcb: C.LBU/C.LHU/C.LH/C.SB/C.SH
                            rd  = c_rd_p;
                            rs1 = c_rs1_p;
                            rs2 = c_rs2_p;
                            alu_opcode = 4'b0000;
                            if (!instr[11]) begin // loads
                                is_load = 1'b1;
                                if (!instr[10])       mem_opcode = 3'b100; // C.LBU byte unsigned
                                else if (!instr[6])   mem_opcode = 3'b101; // C.LHU halfword unsigned
                                else                  mem_opcode = 3'b001; // C.LH halfword signed
                            end else begin // stores
                                is_store = 1'b1;
                                mem_opcode = instr[10] ? 3'b001 : 3'b000; // C.SH : C.SB
                            end
                        end
                        3'b110: begin // C.SW
                            is_store   = 1'b1;
                            rs1        = c_rs1_p;
                            rs2        = c_rs2_p;
                            mem_opcode = 3'b010;
                            alu_opcode = 4'b0000;
                        end
                        default: begin end
                    endcase
                end
                2'b01: begin
                    case (c_f3)
                        3'b000: begin // C.ADDI / C.NOP
                            is_alu_imm = 1'b1;
                            rd         = c_rd_f;
                            rs1        = c_rd_f;
                            alu_opcode = 4'b0000;
                            imm        = {{26{instr[12]}}, instr[12], instr[6:2]};
                        end
                        3'b001: begin // C.JAL (RV32 only)
                            is_jal = 1'b1;
                            rd     = 4'd1; // ra
                        end
                        3'b010: begin // C.LI
                            is_alu_imm = 1'b1;
                            rd         = c_rd_f;
                            rs1        = 4'd0;
                            alu_opcode = 4'b0000;
                            imm        = {{26{instr[12]}}, instr[12], instr[6:2]};
                        end
                        3'b011: begin // C.ADDI16SP or C.LUI
                            if (c_rd_f == 4'd2) begin // C.ADDI16SP
                                is_alu_imm = 1'b1;
                                rd         = 4'd2;
                                rs1        = 4'd2;
                                alu_opcode = 4'b0000;
                                imm        = {{23{instr[12]}}, instr[4:3], instr[5], instr[2], instr[6], 4'b0};
                            end else begin // C.LUI
                                is_lui = 1'b1;
                                rd     = c_rd_f;
                                imm    = {{14{instr[12]}}, instr[12], instr[6:2], 12'd0};
                            end
                        end
                        3'b100: begin // C.SRLI/C.SRAI/C.ANDI/C.SUB/C.XOR/C.OR/C.AND
                            rd  = c_rs1_p;
                            rs1 = c_rs1_p;
                            rs2 = c_rs2_p;
                            case (instr[11:10])
                                2'b00: begin // C.SRLI
                                    is_alu_imm = 1'b1;
                                    alu_opcode = 4'b0101; // SRL
                                end
                                2'b01: begin // C.SRAI
                                    is_alu_imm = 1'b1;
                                    alu_opcode = 4'b1101; // SRA
                                end
                                2'b10: begin // C.ANDI
                                    is_alu_imm = 1'b1;
                                    alu_opcode = 4'b0111; // AND
                                end
                                2'b11: begin // C.SUB/XOR/OR/AND (CA) or C.MUL (Zcb, instr[12]=1, funct2=10)
                                    is_alu_reg = 1'b1;
                                    if (instr[12] && instr[6:5] == 2'b10) begin
                                        alu_opcode = 4'b1010; // C.MUL
                                    end else begin
                                        case (instr[6:5])
                                            2'b00: alu_opcode = 4'b1000; // SUB
                                            2'b01: alu_opcode = 4'b0100; // XOR
                                            2'b10: alu_opcode = 4'b0110; // OR
                                            2'b11: alu_opcode = 4'b0111; // AND
                                        endcase
                                    end
                                end
                            endcase
                        end
                        3'b101: begin // C.J
                            is_jal = 1'b1;
                            rd     = 4'd0; // discard
                        end
                        3'b110: begin // C.BEQZ
                            is_branch  = 1'b1;
                            rs1        = c_rs1_p;
                            alu_opcode = 4'b0100; // XOR for eq test
                        end
                        3'b111: begin // C.BNEZ
                            is_branch  = 1'b1;
                            rs1        = c_rs1_p;
                            alu_opcode = 4'b0100;
                        end
                    endcase
                end
                2'b10: begin
                    case (c_f3)
                        3'b000: begin // C.SLLI
                            is_alu_imm = 1'b1;
                            rd         = c_rd_f;
                            rs1        = c_rd_f;
                            alu_opcode = 4'b0001;
                        end
                        3'b010: begin // C.LWSP
                            is_load    = 1'b1;
                            rd         = c_rd_f;
                            rs1        = 4'd2; // sp
                            mem_opcode = 3'b010;
                            alu_opcode = 4'b0000;
                        end
                        3'b100: begin // C.JR / C.MV / C.ADD / C.JALR / C.EBREAK
                            rd  = c_rd_f;
                            rs1 = c_rd_f;
                            rs2 = c_rs2_f;
                            if (!instr[12]) begin
                                if (c_rs2_f == 4'd0) begin // C.JR
                                    is_jalr    = 1'b1;
                                    rd         = 4'd0;
                                    alu_opcode = 4'b0000;
                                end else begin // C.MV
                                    is_alu_reg = 1'b1;
                                    rs1        = 4'd0;
                                    alu_opcode = 4'b0000;
                                end
                            end else begin
                                if (c_rs2_f == 4'd0) begin
                                    if (c_rd_f == 4'd0) begin // C.EBREAK
                                        is_system = 1'b1;
                                    end else begin // C.JALR
                                        is_jalr    = 1'b1;
                                        rd         = 4'd1; // ra
                                        alu_opcode = 4'b0000;
                                    end
                                end else begin // C.ADD
                                    is_alu_reg = 1'b1;
                                    alu_opcode = 4'b0000;
                                end
                            end
                        end
                        
                        // 3'b101: begin end // reserved
                        3'b110: begin // C.SWSP
                            is_store   = 1'b1;
                            rs1        = 4'd2; // sp
                            rs2        = c_rs2_f;
                            mem_opcode = 3'b010;
                            alu_opcode = 4'b0000;
                        end
                        default: begin end
                    endcase
                end
                default: begin end
            endcase
        end
    end

endmodule
