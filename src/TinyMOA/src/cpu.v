// TinyMOA CPU Core
// Single-cycle 32-bit FSM: FETCH -> DECODE -> EXECUTE -> MEM -> WB
//
// Memory interface is unified (one port for fetch + data).
// TCM is synchronous: address presented in FETCH, data valid in DECODE.
// instr_reg is stable from DECODE through WB, so decoder/regfile outputs
// are combinationally valid throughout -- no need to re-latch them.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_cpu (
    input  clk,
    input  nrst,

    // Unified memory interface (TCM Port A)
    input         mem_ready,
    output [23:0] mem_addr,
    output        mem_read,
    output        mem_write,
    output [1:0]  mem_size,    // [1:0]=size: 00=byte, 01=half, 10=word
    output [31:0] mem_wdata,
    input  [31:0] mem_rdata
);

    reg [2:0]  state;
    reg [23:0] pc;
    reg [31:0] instr_reg;       // latched from mem_rdata in DECODE
    reg [31:0] alu_result_reg;  // latched from alu_result in EXECUTE
    reg [31:0] load_data_reg;   // latched from mem_rdata in MEM (loads only)

    // === Decoder ===
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
        .instr         (instr_reg),
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


    // === Register file ===
    wire [31:0] regfile_rs1_data;
    wire [31:0] regfile_rs2_data;

    reg        regfile_rd_wen;
    reg [31:0] regfile_rd_data;

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


    // === ALU ===
    reg  [31:0] alu_a_in;
    reg  [31:0] alu_b_in;
    wire [31:0] alu_result;

    // Input mux
    always @(*) begin
        alu_a_in = regfile_rs1_data;
        alu_b_in = decoder_imm;
        if (decoder_is_alu_reg) alu_b_in = regfile_rs2_data;
        if (decoder_is_branch)  alu_b_in = regfile_rs2_data;
        if (decoder_is_auipc)   alu_a_in = {8'b0, pc};
    end

    tinymoa_alu alu (
        .opcode (decoder_alu_opcode),
        .a_in   (alu_a_in),
        .b_in   (alu_b_in),
        .result (alu_result)
    );


    // === Derived combinational signals ===
    wire [23:0] instr_len = decoder_is_compressed ? 24'd2 : 24'd4; // RV32I = 4, RV32C = 2
    wire [23:0] link_addr = pc + instr_len; // JAL/JALR return address: PC + instr_len

    // mem_opcode[1:0]=size (00=byte, 01=half, 10=word), [2]=unsigned
    reg [31:0] load_ext;
    always @(*) begin
        case (decoder_mem_opcode)
            3'b000:  load_ext = {{24{load_data_reg[7]}},  load_data_reg[7:0]};  // LB
            3'b100:  load_ext = {24'b0,                   load_data_reg[7:0]};  // LBU
            3'b001:  load_ext = {{16{load_data_reg[15]}}, load_data_reg[15:0]}; // LH
            3'b101:  load_ext = {16'b0,                   load_data_reg[15:0]}; // LHU
            default: load_ext = load_data_reg;                                  // LW
        endcase
    end


    // === Memory interface ===
    reg [23:0] mem_addr_r;
    reg        mem_read_r;
    reg        mem_write_r;

    assign mem_addr  = mem_addr_r;
    assign mem_read  = mem_read_r;
    assign mem_write = mem_write_r;
    assign mem_wdata = regfile_rs2_data; // store data
    assign mem_size  = decoder_mem_opcode[1:0];


    // === FSM ===
    localparam FSM_FETCH   = 3'd0;
    localparam FSM_DECODE  = 3'd1;
    localparam FSM_EXECUTE = 3'd2;
    localparam FSM_MEM     = 3'd3;
    localparam FSM_WB      = 3'd4;

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            state          <= FSM_FETCH;
            pc             <= 24'd0;
            instr_reg      <= 32'b0;
            alu_result_reg <= 32'b0;
            load_data_reg  <= 32'b0;
            mem_addr_r     <= 24'd0;
            mem_read_r     <= 1'b0;
            mem_write_r    <= 1'b0;
            regfile_rd_wen  <= 1'b0;
            regfile_rd_data <= 32'b0;
        end else begin
            regfile_rd_wen <= 1'b0; // default: no write

            case (state)

                FSM_FETCH: begin
                    // Present PC to TCM. Synchronous SRAM: data valid next cycle.
                    mem_addr_r  <= pc;
                    mem_read_r  <= 1'b1;
                    mem_write_r <= 1'b0;
                    state       <= FSM_DECODE;
                end

                FSM_DECODE: begin
                    // mem_rdata now valid. Latch instruction; decoder sees it next cycle.
                    mem_read_r <= 1'b0;
                    instr_reg  <= mem_rdata;
                    state      <= FSM_EXECUTE;
                end

                FSM_EXECUTE: begin
                    // Decoder and regfile outputs are combinationally valid from instr_reg.
                    // Latch ALU result for use in MEM and WB.
                    alu_result_reg <= alu_result;

                    if (decoder_is_load || decoder_is_store) begin
                        state <= FSM_MEM;
                    end else begin
                        state <= FSM_WB;
                    end
                end

                FSM_MEM: begin
                    // Drive effective address (rs1 + imm, computed by ALU in EXECUTE).
                    mem_addr_r  <= alu_result_reg[23:0];
                    mem_read_r  <= decoder_is_load;
                    mem_write_r <= decoder_is_store;
                    if (mem_ready) begin
                        mem_read_r    <= 1'b0;
                        mem_write_r   <= 1'b0;
                        load_data_reg <= mem_rdata;
                        state         <= FSM_WB;
                    end
                end

                FSM_WB: begin
                    // Select writeback value
                    if (decoder_is_lui) begin
                        regfile_rd_data <= decoder_imm;
                    end else if (decoder_is_jal || decoder_is_jalr) begin
                        regfile_rd_data <= {8'b0, link_addr};
                    end else if (decoder_is_load) begin
                        regfile_rd_data <= load_ext;
                    end else begin
                        regfile_rd_data <= alu_result_reg;
                    end
                    regfile_rd_wen <= (decoder_rd != 4'd0);

                    // Update PC
                    if (decoder_is_jal) begin
                        pc <= pc + decoder_imm[23:0];
                    end else if (decoder_is_jalr) begin
                        pc <= alu_result_reg[23:0] & 24'hFFFFFE;
                    end else begin
                        // Branch: not-taken stub (B-type imm not yet assembled in decoder)
                        pc <= pc + instr_len;
                    end

                    state <= FSM_FETCH;
                end

                default: state <= FSM_FETCH;
            endcase
        end
    end

    wire _unused = &{decoder_is_system, decoder_is_alu_imm, decoder_is_branch,
                     decoder_is_auipc, 1'b0};

endmodule
