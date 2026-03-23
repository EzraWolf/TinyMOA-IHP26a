// DCIM unit testbench
//
// Exposes the full DCIM interface as top-level ports.
// Cocotb drives all inputs directly, including the memory bus (mem_rdata),
// so FSM states, weight loading, and signed conversion can be tested in
// isolation without a TCM.

`default_nettype none
`timescale 1ns / 1ps

module tb_dcim (
    input  clk,
    input  nrst,

    output        mmio_ready,
    input         mmio_write,
    input  [31:0] mmio_wdata,
    input         mmio_read,
    output [31:0] mmio_rdata,
    input  [5:0]  mmio_addr,

    output        mem_read,
    input  [31:0] mem_rdata,
    output        mem_write,
    output [31:0] mem_wdata,
    output [9:0]  mem_addr
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_dcim.fst");
        $dumpvars(0, tb_dcim);
        #1;
    end
    `endif

    tinymoa_dcim dut (
        .clk        (clk),
        .nrst       (nrst),
        .mmio_ready (mmio_ready),
        .mmio_write (mmio_write),
        .mmio_wdata (mmio_wdata),
        .mmio_read  (mmio_read),
        .mmio_rdata (mmio_rdata),
        .mmio_addr  (mmio_addr),
        .mem_rdata  (mem_rdata),
        .mem_wdata  (mem_wdata),
        .mem_write  (mem_write),
        .mem_read   (mem_read),
        .mem_addr   (mem_addr)
    );

endmodule