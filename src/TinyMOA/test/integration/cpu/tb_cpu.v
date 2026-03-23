// CPU core integration test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_cpu (
    input clk,
    input nrst,

    output [23:0] mem_addr,
    output        mem_read,
    output        mem_write,
    output [31:0] mem_wdata,
    output [1:0]  mem_size,

    input [31:0]  mem_rdata,
    input         mem_ready
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_cpu.fst");
        $dumpvars(0, tb_cpu);
        #1;
    end
    `endif

    tinymoa_cpu dut_cpu (
        .clk(clk),
        .nrst(nrst),
        .mem_addr(mem_addr),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .mem_wdata(mem_wdata),
        .mem_size(mem_size),
        .mem_rdata(mem_rdata),
        .mem_ready(mem_ready)
    );
endmodule
