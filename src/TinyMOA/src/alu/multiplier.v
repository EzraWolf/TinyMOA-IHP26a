// Multiplier: 16x16 signed -> 32-bit, pipelined.
// Product is registered on posedge clk (breaks long combinational path).
// Core presents a_in/b_in, waits one cycle, then streams product nibble-by-nibble via nibble_ct.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_multiplier (
    input clk,

    input  signed [15:0] a_in,
    input  signed [15:0] b_in,
    input  [2:0]  nibble_ct,

    output [3:0] result
);

    reg signed [31:0] product_reg;

    always @(posedge clk)
        product_reg <= a_in * b_in;

    assign result = product_reg[{nibble_ct, 2'b00} +: 4];

endmodule
