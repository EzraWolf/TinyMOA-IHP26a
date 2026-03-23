// TinyMOA CPU Core -- RV32EC nibble-serial pipelined processor
//
// FSM: FETCH -> DECODE -> EXECUTE -> WRITEBACK -> MEM (load/store only)
//
// FETCH:     1 cycle TCM (synchronous read, ready asserted next cycle), stall for QSPI.
// DECODE:    1 cycle, combinational.
// EXECUTE:   8 cycles (RV32I) or 4 (some RV32C). Each cycle: regfile outputs nibble,
//            ALU processes with carry chain, result nibble written back. Pipelined.
//            Shifts and C.MUL use separate datapaths inside alu.v.
// WRITEBACK: 1 cycle. Update PC.
// MEM:       Load/store only. Assert mem_read/write, wait for mem_ready.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_cpu (
    input clk,
    input nrst,

    input             mem_ready,
    output reg [1:0]  mem_size,

    output reg        mem_read,
    input      [31:0] mem_rdata,

    output reg        mem_write,
    output reg [31:0] mem_wdata,

    output reg [23:0] mem_addr
);

    localparam S_FETCH     = 3'd0;
    localparam S_DECODE    = 3'd1;
    localparam S_EXECUTE   = 3'd2;
    localparam S_WRITEBACK = 3'd3;
    localparam S_MEM       = 3'd4;

    reg [2:0]  state;
    reg [31:0] instr;
    reg        alu_carry;
    reg        alu_cmp;
    reg        mem_is_load;

    // Program counter
    wire [23:0] pc;
    reg         pc_en;
    reg         pc_wen;

    // Nibble counter
    wire [2:0] nibble_ct;
    reg        nibble_en;
    reg        nibble_wen;

    // Decoder outputs
    wire [31:0] dec_imm;
    wire [3:0]  dec_alu_opcode;
    wire [2:0]  dec_mem_opcode;
    wire [3:0]  dec_rs1, dec_rs2, dec_rd;
    wire        dec_is_load, dec_is_store;
    wire        dec_is_branch, dec_is_jal, dec_is_jalr;
    wire        dec_is_lui, dec_is_auipc;
    wire        dec_is_alu_reg, dec_is_alu_imm;
    wire        dec_is_system;
    wire        dec_is_compressed;

    // Register file
    wire [3:0]  rf_rs1_nibble;
    wire [3:0]  rf_rs2_nibble;
    reg  [3:0]  rf_rd_nibble;
    reg         rf_wen;

    // ALU
    wire [3:0]  alu_result;
    wire        alu_c_out;
    wire        alu_cmp_out;
    reg  [3:0]  alu_b_nibble; // B operand mux: rs2 nibble or imm nibble

    // === Submodule instances ===

    tinymoa_counter #(.DATA_WIDTH(24)) program_counter (
        .clk     (clk),
        .nrst    (nrst),
        .en      (pc_en),
        .wen     (pc_wen),
        .data_in (pc),
        .result  (pc)
    );

    tinymoa_counter #(.DATA_WIDTH(3)) nibble_counter (
        .clk     (clk),
        .nrst    (nrst),
        .en      (nibble_en),
        .wen     (nibble_wen),
        .data_in (3'd0),
        .result  (nibble_ct)
    );

    tinymoa_decoder decoder (
        .instr         (instr),
        .imm           (dec_imm),
        .alu_opcode    (dec_alu_opcode),
        .mem_opcode    (dec_mem_opcode),
        .rs1           (dec_rs1),
        .rs2           (dec_rs2),
        .rd            (dec_rd),
        .is_load       (dec_is_load),
        .is_store      (dec_is_store),
        .is_branch     (dec_is_branch),
        .is_jal        (dec_is_jal),
        .is_jalr       (dec_is_jalr),
        .is_lui        (dec_is_lui),
        .is_auipc      (dec_is_auipc),
        .is_alu_reg    (dec_is_alu_reg),
        .is_alu_imm    (dec_is_alu_imm),
        .is_system     (dec_is_system),
        .is_compressed (dec_is_compressed)
    );

    tinymoa_registers register_file (
        .clk        (clk),
        .nrst       (nrst),
        .nibble_ct  (nibble_ct),
        .rs1_sel    (dec_rs1),
        .rs1_nibble (rf_rs1_nibble),
        .rs2_sel    (dec_rs2),
        .rs2_nibble (rf_rs2_nibble),
        .rd_wen     (rf_wen),
        .rd_sel     (dec_rd),
        .rd_nibble  (rf_rd_nibble)
    );

    tinymoa_alu alu (
        .opcode  (dec_alu_opcode),
        .a_in    (rf_rs1_nibble),
        .b_in    (alu_b_nibble),
        .c_in    (alu_carry),
        .result  (alu_result),
        .c_out   (alu_c_out),
        .cmp_in  (alu_cmp),
        .cmp_out (alu_cmp_out)
    );

    // === Core FSM ===

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            state      <= S_FETCH;
            instr      <= 32'd0;
            mem_read   <= 1'b0;
            mem_write  <= 1'b0;
            rf_wen     <= 1'b0;
            pc_en      <= 1'b0;
            pc_wen     <= 1'b0;
            nibble_en  <= 1'b0;
            nibble_wen <= 1'b0;
            alu_carry  <= 1'b0;
            alu_cmp    <= 1'b1;
        end else begin
            rf_wen     <= 1'b0;
            pc_en      <= 1'b0;
            pc_wen     <= 1'b0;
            nibble_en  <= 1'b0;
            nibble_wen <= 1'b0;
            mem_read   <= 1'b0;
            mem_write  <= 1'b0;

            case (state)
                S_FETCH: begin
                    // Assert read at PC. Transition to DECODE when mem_ready.
                    // mem_addr = pc (byte address).
                    // For QSPI: stall here until mem_ready. For TCM: 1-cycle wait.
                end

                S_DECODE: begin
                    // Latch instruction, clear carry, reset cmp accumulator.
                    // Set alu_b_nibble mux: rs2 for alu_reg, imm for alu_imm/load/store/jal/branch.
                    // Go to EXECUTE.
                end

                S_EXECUTE: begin
                    // Enable nibble counter. Each cycle:
                    //   alu_b_nibble = imm nibble (dec_imm >> (nibble_ct*4)) or rf_rs2_nibble
                    //   rf_rd_nibble = alu_result; rf_wen = 1 (if writing rd)
                    //   alu_carry <= alu_c_out; alu_cmp <= alu_cmp_out
                    // On nibble_done: go to MEM (load/store) or WRITEBACK.
                    // For SLL/SRL/SRA/C.MUL: separate datapath, different timing.
                end

                S_WRITEBACK: begin
                    // Update PC:
                    //   Normal: pc + (dec_is_compressed ? 2 : 4)
                    //   Branch taken: pc + dec_imm[23:0]
                    //   JAL: pc + dec_imm[23:0]
                    //   JALR: (rf_rs1_full + dec_imm) & ~1
                    // Go to S_FETCH.
                end

                S_MEM: begin
                    // Load: mem_addr = computed EA, mem_read = 1, wait mem_ready,
                    //   then route mem_rdata through register_file (byte/half/word with sign extend).
                    // Store: mem_addr = EA, mem_write = 1, mem_wdata = rs2, wait mem_ready.
                    // Go to S_WRITEBACK.
                end
            endcase
        end
    end

    // alu_b_nibble mux (combinational, fully driven in FSM above, default here)
    // In EXECUTE: alu_b_nibble = dec_is_alu_reg ? rf_rs2_nibble : dec_imm[nibble_ct*4+:4]
    always @(*) begin
        alu_b_nibble = rf_rs2_nibble;
    end

endmodule
