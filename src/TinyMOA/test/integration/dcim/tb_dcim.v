// DCIM integration testbench
//
// Wraps tinymoa_dcim with a behavioral 512x32 TCM stub (Port B only).
// Cocotb drives MMIO and pre-loads TCM via the tb_mem_* ports before START;
// the DCIM FSM exercises Port B as it would in the real system.

`default_nettype none
`timescale 1ns / 1ps

module tb_dcim (
    input clk,
    input nrst,

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

    // Behavioral TCM (512x32) shared between test driver (Port A) and DCIM (Port B)
    reg [31:0] mem [0:511];
    reg [31:0] mem_b_dout;

    // Port A: test setup (synchronous write, combinational read)
    always @(posedge clk) begin
        if (tb_mem_wen)
            mem[tb_mem_addr] <= tb_mem_wdata;
    end
    assign tb_mem_rdata = mem[tb_mem_raddr];

    // Port B: DCIM FSM (synchronous write, registered read)
    wire [31:0] dcim_mem_wdata;
    wire        dcim_mem_write;
    wire        dcim_mem_read;
    wire [9:0]  dcim_mem_addr;

    always @(posedge clk) begin
        if (dcim_mem_write)
            mem[dcim_mem_addr] <= dcim_mem_wdata;
        mem_b_dout <= mem[dcim_mem_addr];
    end

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