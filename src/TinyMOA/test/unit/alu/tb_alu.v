// ALU testbench -- combinational 32-bit ALU, no clock needed

`default_nettype none
`timescale 1ns / 1ps

module tb_alu (
    input  [3:0]  opcode,
    input  [31:0] a_in,
    input  [31:0] b_in,
    output [31:0] result
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_alu.fst");
        $dumpvars(0, tb_alu);
        #1;
    end
    `endif

    tinymoa_alu dut (
        .opcode (opcode),
        .a_in   (a_in),
        .b_in   (b_in),
        .result (result)
    );
endmodule
