// Program counter test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_counter (
    input clk,
    input nrst,

    input         en,
    input         wen,
    input  [31:0] data_in,

    output [31:0] result,
    output        c_out
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_counter.fst");
        $dumpvars(0, tb_counter);
        #1;
    end
    `endif

    tinymoa_counter #(
        .DATA_WIDTH(32)
    ) dut_counter (
        .clk    (clk),
        .nrst   (nrst),
        .en     (en),
        .wen    (wen),
        .data_in(data_in),
        .result (result),
        .c_out  (c_out)
    );
endmodule
