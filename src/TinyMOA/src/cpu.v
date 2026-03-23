// TinyMOA CPU Core
// 5-stage FSM: FETCH -> DECODE -> EXECUTE -> MEM (loads/stores only) -> WB
//
// Word-addressed: PC counts words (1 word = 32 bits).
//   - RV32I: PC += 1
//   - RV32C: PC handling TBD (compressed = half-word)
//
// Cycle counts (TCM, same-cycle ready):
//   ALU/LUI/AUIPC:  FETCH(1) + DECODE(1) + EXECUTE(1) + WB(1) = 4
//   Load/Store:      FETCH(1) + DECODE(1) + EXECUTE(1) + MEM(1) + WB(1) = 5
//   Branch/JAL/JALR: FETCH(1) + DECODE(1) + EXECUTE(1) + WB(1) = 4

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_cpu (
    input  clk,
    input  nrst,

    // Memory bus (word-addressed)
    input             mem_ready,
    output reg [23:0] mem_addr,
    output reg        mem_read,
    output reg        mem_write,
    output reg [1:0]  mem_size,
    output reg [31:0] mem_wdata,
    input      [31:0] mem_rdata,

    // Debug
    output [2:0]  dbg_state,
    output        dbg_done,
    output [23:0] dbg_pc,
    output [31:0] dbg_instr,
    output [31:0] dbg_alu_result,
    output [3:0]  dbg_dec_alu_opcode,
    output [2:0]  dbg_dec_mem_opcode,
    output [3:0]  dbg_dec_rs1,
    output [3:0]  dbg_dec_rs2,
    output [3:0]  dbg_dec_rd,
    output [10:0] dbg_dec_flags,
    output        dbg_branch_taken
);

    // === FSM states ===
    localparam FSM_FETCH   = 3'd0;
    localparam FSM_DECODE  = 3'd1;
    localparam FSM_EXECUTE = 3'd2;
    localparam FSM_MEM     = 3'd3;
    localparam FSM_WB      = 3'd4;

    // === State registers ===
    reg [2:0]  cpu_state;
    reg [23:0] cpu_pc;
    reg [31:0] cpu_instr;
    reg [31:0] cpu_execute;
    reg [31:0] cpu_writeback;

    // === Debug ===
    assign dbg_state      = cpu_state;
    assign dbg_done       = (cpu_state == FSM_WB);
    assign dbg_pc         = cpu_pc;
    assign dbg_instr      = cpu_instr;
    assign dbg_alu_result = cpu_execute;

    // === Decoder (combinational on cpu_instr) ===
    wire [31:0] decoder_imm;
    wire [3:0]  decoder_alu_opcode;
    wire [2:0]  decoder_mem_opcode;
    wire [3:0]  decoder_rs1;
    wire [3:0]  decoder_rs2;
    wire [3:0]  decoder_rd;
    wire        decoder_is_load;
    wire        decoder_is_store;
    wire        decoder_is_branch;
    wire        decoder_is_jal;
    wire        decoder_is_jalr;
    wire        decoder_is_lui;
    wire        decoder_is_auipc;
    wire        decoder_is_alu_reg;
    wire        decoder_is_alu_imm;
    wire        decoder_is_system;
    wire        decoder_is_compressed;

    tinymoa_decoder decoder (
        .instr         (cpu_instr),
        .imm           (decoder_imm),
        .alu_opcode    (decoder_alu_opcode),
        .mem_opcode    (decoder_mem_opcode),
        .rs1           (decoder_rs1),
        .rs2           (decoder_rs2),
        .rd            (decoder_rd),
        .is_load       (decoder_is_load),
        .is_store      (decoder_is_store),
        .is_branch     (decoder_is_branch),
        .is_jal        (decoder_is_jal),
        .is_jalr       (decoder_is_jalr),
        .is_lui        (decoder_is_lui),
        .is_auipc      (decoder_is_auipc),
        .is_alu_reg    (decoder_is_alu_reg),
        .is_alu_imm    (decoder_is_alu_imm),
        .is_system     (decoder_is_system),
        .is_compressed (decoder_is_compressed)
    );

    // === Register file (combinational read, synchronous write) ===
    wire [31:0] regfile_rs1_data;
    wire [31:0] regfile_rs2_data;
    reg  [31:0] regfile_rd_data;
    reg         regfile_rd_wen;

    tinymoa_registers registers (
        .clk      (clk),
        .nrst     (nrst),
        .rs1_sel  (decoder_rs1),
        .rs1_data (regfile_rs1_data),
        .rs2_sel  (decoder_rs2),
        .rs2_data (regfile_rs2_data),
        .rd_wen   (regfile_rd_wen),
        .rd_sel   (decoder_rd),
        .rd_data  (regfile_rd_data)
    );

    // === ALU (combinational) ===
    // a_in: rs1 for most ops, PC for AUIPC
    // b_in: imm for I-type/loads/stores/AUIPC, rs2 for R-type/branches
    reg  [31:0] alu_a_in;
    reg  [31:0] alu_b_in;
    wire [31:0] alu_result;

    always @(*) begin
        alu_a_in = regfile_rs1_data;
        alu_b_in = decoder_imm;

        if (decoder_is_alu_reg) alu_b_in = regfile_rs2_data;
        if (decoder_is_branch)  alu_b_in = regfile_rs2_data;
        if (decoder_is_auipc)   alu_a_in = {8'b0, cpu_pc};
    end

    tinymoa_alu alu (
        .opcode (decoder_alu_opcode),
        .a_in   (alu_a_in),
        .b_in   (alu_b_in),
        .result (alu_result)
    );

    // === Load sign/zero extension (combinational on cpu_writeback) ===
    reg [31:0] load_ext;
    always @(*) begin
        case (decoder_mem_opcode)
            3'b000:  load_ext = {{24{cpu_writeback[7]}},  cpu_writeback[7:0]};   // LB
            3'b100:  load_ext = {24'b0,                   cpu_writeback[7:0]};   // LBU
            3'b001:  load_ext = {{16{cpu_writeback[15]}}, cpu_writeback[15:0]};  // LH
            3'b101:  load_ext = {16'b0,                   cpu_writeback[15:0]};  // LHU
            default: load_ext = cpu_writeback;                                   // LW
        endcase
    end

    // === Branch condition (combinational on cpu_execute) ===
    // Equality branches (BEQ/BNE/C.BEQZ/C.BNEZ): ALU does SUB (opcode 0001), taken when result==0
    // Comparison branches (BLT/BGE/BLTU/BGEU):    ALU does SLT/SLTU,          taken when result[0]==1
    // Inversion (BNE, BGE, BGEU, C.BNEZ): cpu_instr[12]==1 for both 32-bit funct3[0] and C encoding
    wire branch_is_eq  = (decoder_alu_opcode == 4'b0001);
    wire branch_cond   = branch_is_eq ? (cpu_execute == 32'b0) : cpu_execute[0];
    wire branch_taken  = decoder_is_branch && (branch_cond ^ cpu_instr[12]);

    assign dbg_dec_alu_opcode = decoder_alu_opcode;
    assign dbg_dec_mem_opcode = decoder_mem_opcode;
    assign dbg_dec_rs1        = decoder_rs1;
    assign dbg_dec_rs2        = decoder_rs2;
    assign dbg_dec_rd         = decoder_rd;
    assign dbg_dec_flags      = {decoder_is_load, decoder_is_store, decoder_is_branch,
                                  decoder_is_jal, decoder_is_jalr, decoder_is_lui,
                                  decoder_is_auipc, decoder_is_alu_reg, decoder_is_alu_imm,
                                  decoder_is_system, decoder_is_compressed};
    assign dbg_branch_taken   = branch_taken;

    // === Write-back data mux (combinational) ===
    wire writes_rd = decoder_is_alu_reg || decoder_is_alu_imm
                   || decoder_is_lui || decoder_is_auipc
                   || decoder_is_jal || decoder_is_jalr
                   || decoder_is_load;

    reg [31:0] wb_data;
    always @(*) begin
        if (decoder_is_load)
            wb_data = load_ext;
        else if (decoder_is_lui)
            wb_data = decoder_imm;
        else if (decoder_is_jal || decoder_is_jalr)
            wb_data = {8'b0, cpu_pc + 24'd1};
        else
            wb_data = cpu_execute;
    end

    // === FSM ===
    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            cpu_state       <= FSM_FETCH;
            cpu_pc          <= 24'b0;
            cpu_instr       <= 32'b0;
            cpu_execute     <= 32'b0;
            cpu_writeback   <= 32'b0;
            mem_addr        <= 24'd0;
            mem_read        <= 1'b0;
            mem_write       <= 1'b0;
            mem_size        <= 2'b10;
            mem_wdata       <= 32'b0;
            regfile_rd_wen  <= 1'b0;
            regfile_rd_data <= 32'b0;

        end else begin
            regfile_rd_wen <= 1'b0;

            case (cpu_state)

                FSM_FETCH: begin
                    mem_addr <= cpu_pc;
                    mem_read <= 1'b1;
                    mem_size <= 2'b10;
                    if (mem_ready) begin
                        cpu_instr <= mem_rdata;
                        mem_read  <= 1'b0;
                        cpu_state <= FSM_DECODE;
                    end
                end

                FSM_DECODE: begin
                    cpu_state <= FSM_EXECUTE;
                end

                FSM_EXECUTE: begin
                    cpu_execute <= alu_result;
                    if (decoder_is_load || decoder_is_store)
                        cpu_state <= FSM_MEM;
                    else
                        cpu_state <= FSM_WB;
                end

                FSM_MEM: begin
                    mem_addr <= cpu_execute[23:0];
                    mem_size <= decoder_mem_opcode[1:0];
                    if (!mem_ready) begin
                        // Assertion phase: drive bus signals
                        if (decoder_is_store) begin
                            mem_write <= 1'b1;
                            mem_wdata <= regfile_rs2_data;
                        end else begin
                            mem_read <= 1'b1;
                        end
                    end else begin
                        // Completion phase: clear bus and transition
                        mem_read  <= 1'b0;
                        mem_write <= 1'b0;
                        if (decoder_is_load)
                            cpu_writeback <= mem_rdata;
                        cpu_state <= FSM_WB;
                    end
                end

                FSM_WB: begin
                    regfile_rd_wen  <= writes_rd;
                    regfile_rd_data <= wb_data;

                    if (branch_taken || decoder_is_jal)
                        cpu_pc <= cpu_pc + {{2{decoder_imm[23]}}, decoder_imm[23:2]};
                    else if (decoder_is_jalr)
                        cpu_pc <= cpu_execute[23:0];
                    else
                        cpu_pc <= cpu_pc + 24'd1;

                    cpu_state <= FSM_FETCH;
                end

                default: cpu_state <= FSM_FETCH;
            endcase
        end
    end

    wire _unused = &{decoder_is_system, 1'b0};

endmodule
