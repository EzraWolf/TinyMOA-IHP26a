// ALU test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_alu (
    input clk,
    input nrst,

    input [3:0]  opcode,

    input [31:0] a_in,
    input [31:0] b_in,
    input        c_in,

    output reg [31:0] result,
    output reg        c_out,
    output reg        cmp_out
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_alu.fst");
        $dumpvars(0, tb_alu);
        #1;
    end
    `endif

    reg [2:0] nibble_ct;

    always @(posedge clk)
        if (!nrst)
            nibble_ct <= 0;
        else
            nibble_ct <= nibble_ct + 1;

    wire c_chain   = (nibble_ct == 0) ? c_in : c_out;
    wire cmp_chain = (nibble_ct == 0) ? 1'b1 : cmp_out;
    wire [3:0] result_nibble;
    wire c_out_nibble;
    wire cmp_out_nibble;

    tinymoa_alu dut_alu (
        .opcode (opcode),
        .a_in   (a_in[nibble_ct*4+:4]),
        .b_in   (b_in[nibble_ct*4+:4]),
        .c_in   (c_chain),
        .result (result_nibble),
        .c_out  (c_out_nibble),
        .cmp_in (cmp_chain),
        .cmp_out(cmp_out_nibble)
    );

    always @(posedge clk) begin
        result[nibble_ct*4+:4] <= result_nibble;
        c_out   <= c_out_nibble;
        cmp_out <= cmp_out_nibble;
    end
endmodule
