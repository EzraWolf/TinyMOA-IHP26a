// DCIM unit testbench

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

    reg  [31:0] mem [0:511];
    wire [31:0] mem_b_dout;

    always @(posedge clk) begin
        if (tb_mem_wen)
            mem[tb_mem_addr] <= tb_mem_wdata;
    end
    assign tb_mem_rdata = mem[tb_mem_raddr];

    // Port B: registered read + synchronous write (matches real TCM)
    wire [31:0] dcim_mem_wdata;
    wire        dcim_mem_write;
    wire        dcim_mem_read;
    wire [9:0]  dcim_mem_addr;
    reg  [31:0] mem_b_dout_r;

    always @(posedge clk) begin
        if (dcim_mem_read | dcim_mem_write) begin
            if (dcim_mem_write)
                mem[dcim_mem_addr] <= dcim_mem_wdata;
            mem_b_dout_r <= mem[dcim_mem_addr];
        end
    end

    assign mem_b_dout = mem_b_dout_r;

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
