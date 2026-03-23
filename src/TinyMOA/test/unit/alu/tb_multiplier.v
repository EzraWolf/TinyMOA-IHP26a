// Multiplier test bench
// Wraps tinymoa_multiplier: drives nibble_ct internally and assembles
// the nibble-serial output into a 32-bit product register.
// After loading a_in/b_in, wait 9 clocks (1 pipeline + 8 nibble reads).

`default_nettype none
`timescale 1ns / 1ps

module tb_multiplier (
    input clk,
    input nrst,

    input [15:0] a_in,
    input [15:0] b_in,

    output reg [31:0] product
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_multiplier.fst");
        $dumpvars(0, tb_multiplier);
        #1;
    end
    `endif

    reg [2:0] nibble_ct;

    always @(posedge clk)
        if (!nrst) nibble_ct <= 0;
        else       nibble_ct <= nibble_ct + 1;

    wire [3:0] result;

    tinymoa_multiplier dut_multiplier (
        .clk      (clk),
        .a_in     (a_in),
        .b_in     (b_in),
        .nibble_ct(nibble_ct),
        .result   (result)
    );

    // Assemble nibble-serial output into full product word.
    // After 9 clocks from stable inputs, all 8 nibble positions have been
    // written with the current product regardless of nibble_ct phase.
    always @(posedge clk)
        product[nibble_ct*4 +: 4] <= result;

endmodule
