`default_nettype none
`timescale 1ns / 1ps

// Phase 1 FPGA Bring-up Top-Level for TinyMOA
// Targets: Alchitry Cu V2 (iCE40-HX8K) with IO board
module top (
    input wire clk,

    // IO board: DIP switch [3:0]
    input wire [3:0] sw,

    // IO board: Buttons (A, B, C=reset, D, E)
    input wire btn_a,
    input wire btn_b,
    input wire btn_c,
    input wire btn_d,
    input wire btn_e,

    // IO board: 7-segment display (4 digits)
    // Digit selects (active high for common cathode)
    output wire [3:0] dig_sel,

    // Segment outputs (a-g, active high for common cathode)
    output wire [6:0] seg
);

    wire clk_50mhz;
    wire pll_locked;

    pll_50mhz pll_inst (
        .clkin(clk),
        .clkout(clk_50mhz),
        .locked(pll_locked)
    );

    // Reset: active low, synchronized to clk_50mhz
    wire nrst = pll_locked & ~btn_c;

    // CPU Core
    wire [23:0] mem_addr;
    wire        mem_read;
    wire        mem_write;
    wire [31:0] mem_wdata;
    wire [1:0]  mem_size;
    wire [31:0] mem_rdata_from_loader;
    wire        mem_ready_from_loader;

    wire [2:0]  dbg_state;
    wire [23:0] dbg_pc;
    wire [3:0]  dbg_alu_a;
    wire [3:0]  dbg_alu_b;
    wire [3:0]  dbg_alu_result;
    wire        dbg_alu_carry;
    wire [2:0]  dbg_nibble_cnt;

    tinymoa_core cpu (
        .clk(clk_50mhz),
        .nrst(nrst),

        .mem_addr(mem_addr),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .mem_wdata(mem_wdata),
        .mem_size(mem_size),
        .mem_rdata(mem_rdata_from_loader),
        .mem_ready(mem_ready_from_loader),

        .dbg_state(dbg_state),
        .dbg_pc(dbg_pc),
        .dbg_alu_a(dbg_alu_a),
        .dbg_alu_b(dbg_alu_b),
        .dbg_alu_result(dbg_alu_result),
        .dbg_alu_carry(dbg_alu_carry),
        .dbg_nibble_cnt(dbg_nibble_cnt)
    );

    // Instruction Loader (Manual ROM via IO shield)
    instr_loader loader (
        .clk(clk_50mhz),
        .nrst(nrst),

        .mem_read(mem_read),
        .mem_ready(mem_ready_from_loader),
        .mem_rdata(mem_rdata_from_loader),

        .sw(sw),
        .btn_e(btn_e)
    );

    // Display Controller
    wire [6:0] seg_a, seg_b, seg_c, seg_d;

    debug_display display (
        .clk(clk_50mhz),
        .nrst(nrst),

        .dbg_state(dbg_state),
        .dbg_pc(dbg_pc),
        .dbg_alu_a(dbg_alu_a),
        .dbg_alu_b(dbg_alu_b),
        .dbg_alu_result(dbg_alu_result),
        .dbg_alu_carry(dbg_alu_carry),
        .dbg_nibble_cnt(dbg_nibble_cnt),

        .btn_a(btn_a),
        .btn_b(btn_b),
        .btn_d(btn_d),

        .seg_a(seg_a),
        .seg_b(seg_b),
        .seg_c(seg_c),
        .seg_d(seg_d)
    );

    // ============================================================================
    // 7-Segment Display Multiplexing (4×7-segment display)
    // Alchitry IO board digit selects: dig[0]=A, dig[1]=B, dig[2]=C, dig[3]=D
    // Segments are always driven; multiplexing via digit select
    // ============================================================================
    reg [1:0] mux_counter;
    always @(posedge clk_50mhz) begin
        if (!nrst)
            mux_counter <= 2'd0;
        else
            mux_counter <= mux_counter + 2'd1;
    end

    assign dig_sel = (4'b1 << mux_counter);

    wire [6:0] seg_mux = ({mux_counter} == 2'd0) ? seg_a :
                         ({mux_counter} == 2'd1) ? seg_b :
                         ({mux_counter} == 2'd2) ? seg_c : seg_d;

    assign seg = seg_mux;
endmodule
