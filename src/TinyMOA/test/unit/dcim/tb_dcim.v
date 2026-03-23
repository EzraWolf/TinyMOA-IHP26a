// DCIM unit testbench
//
// Contains a behavioral 512x32 memory stub (1-cycle read latency).
// Cocotb pre-loads the memory via tb_mem_wen/tb_mem_wdata/tb_mem_addr,
// then starts inference and reads results back via tb_mem_raddr/tb_mem_rdata.
// This avoids driving mem_rdata directly from Python (VPI limitation with
// top-level input ports that feed directly into sub-module ports).

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

    input         tb_mem_wen,
    input  [31:0] tb_mem_wdata,
    input  [9:0]  tb_mem_addr,
    input  [9:0]  tb_mem_raddr,
    output [31:0] tb_mem_rdata
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_dcim.fst");
        $dumpvars(0, tb_dcim);
        #1;
    end
    `endif

    reg [31:0] mem [0:511];
    wire [31:0] mem_b_dout;

    always @(posedge clk) begin
        if (tb_mem_wen)
            mem[tb_mem_addr] <= tb_mem_wdata;
    end
    assign tb_mem_rdata = mem[tb_mem_raddr];

    // Write is synchronous, read is combinational
    wire [31:0] dcim_mem_wdata;
    wire        dcim_mem_write;
    wire        dcim_mem_read;
    wire [9:0]  dcim_mem_addr;

    always @(posedge clk) begin
        if (dcim_mem_write)
            mem[dcim_mem_addr] <= dcim_mem_wdata;
    end

    assign mem_b_dout = mem[dcim_mem_addr];

    tinymoa_dcim dut (
        .clk        (clk),
        .nrst       (nrst),
        .mmio_ready (mmio_ready),
        .mmio_write (mmio_write),
        .mmio_wdata (mmio_wdata),
        .mmio_read  (mmio_read),
        .mmio_rdata (mmio_rdata),
        .mmio_addr  (mmio_addr),
        .mem_rdata  (mem_b_dout),
        .mem_wdata  (dcim_mem_wdata),
        .mem_write  (dcim_mem_write),
        .mem_read   (dcim_mem_read),
        .mem_addr   (dcim_mem_addr)
    );

endmodule
