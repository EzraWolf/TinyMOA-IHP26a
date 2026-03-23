// TinyMOA Top-Level -- TinyTapeout IHP26a wrapper
//
// GDS Milestone 1: TCM macro standalone.
// Verifies the IHP RM_IHPSG13_2P_512x32 dual-port SRAM macro
// integrates cleanly into the OpenLane/TinyTapeout GDS flow.
//
// Port A: CPU (placeholder - tied off for M1)
// Port B: DCIM (placeholder - tied off for M1)
// uo_out driven from a_dout to prevent macro from being optimized away.
//
// Next milestone: add CPU + decoder + registers (Milestone 2).

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_top (
    input  clk,
    input  nrst,
    input  [7:0] ui_in,
    output [7:0] uo_out,
    input  [7:0] uio_in,
    output [7:0] uio_out,
    output [7:0] uio_oe
);

    wire [31:0] tcm_a_dout;
    wire [31:0] tcm_b_dout;

    tinymoa_tcm tcm (
        .clk    (clk),
        // Port A: CPU (inactive for M1)
        .a_en   (1'b0),
        .a_wen  (1'b0),
        .a_din  (32'b0),
        .a_dout (tcm_a_dout),
        .a_addr (10'b0),
        // Port B: DCIM (inactive for M1)
        .b_en   (1'b0),
        .b_wen  (1'b0),
        .b_din  (32'b0),
        .b_dout (tcm_b_dout),
        .b_addr (10'b0)
    );

    // Drive uo_out from a_dout to prevent macro optimization
    assign uo_out  = tcm_a_dout[7:0];
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    wire _unused = &{nrst, ui_in, uio_in, tcm_a_dout[31:8], tcm_b_dout, 1'b0};

endmodule
