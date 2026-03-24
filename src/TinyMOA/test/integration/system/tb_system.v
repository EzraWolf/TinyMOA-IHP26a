// TinyMOA system integration testbench
//
// Wraps tinymoa_top with all TT pins exposed for cocotb.

`default_nettype none
`timescale 1ns / 1ps

module tb_system (
    input clk,
    input nrst
);

    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_system.fst");
        $dumpvars(0, tb_system);
        #1;
    end
    `endif

    reg  [7:0] ui_in;
    wire [7:0] uo_out;
    reg  [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    tinymoa_top dut (
        .clk     (clk),
        .nrst    (nrst),
        .ui_in   (ui_in),
        .uo_out  (uo_out),
        .uio_in  (uio_in),
        .uio_out (uio_out),
        .uio_oe  (uio_oe)
    );

endmodule
