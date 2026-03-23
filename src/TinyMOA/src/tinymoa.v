// TinyMOA RISC-V & DCIM ASIC

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_top (
    input  clk,
    input  nrst,
    input  [7:0] ui_in,
    output [7:0] uo_out,
    input  [7:0] uio_in,
    output [7:0] uio_out,
    output [7:0] uio_oe
);

    // CPU memory interface
    wire [23:0] cpu_mem_addr;
    wire        cpu_mem_read;
    wire        cpu_mem_write;
    wire [1:0]  cpu_mem_size;
    wire [31:0] cpu_mem_wdata;
    wire [31:0] cpu_mem_rdata;
    wire        cpu_mem_ready = 1'b1; // Synced, always ready

    tinymoa_cpu cpu (
        .clk       (clk),
        .nrst      (nrst),
        .mem_ready (cpu_mem_ready),
        .mem_addr  (cpu_mem_addr),
        .mem_read  (cpu_mem_read),
        .mem_write (cpu_mem_write),
        .mem_size  (cpu_mem_size),
        .mem_wdata (cpu_mem_wdata),
        .mem_rdata (cpu_mem_rdata)
    );

    // TCM data wires
    wire [31:0] tcm_a_dout;
    wire [31:0] tcm_b_dout;

    assign cpu_mem_rdata = tcm_a_dout;


    // CPU/bootloader FSM -> TCM Port A
    // TCM is word-addressed (512 words = 2KB). Byte addr[11:2] = word addr[9:0].
    tinymoa_tcm tcm (
        .clk    (clk),
        .a_en   (cpu_mem_read | cpu_mem_write),
        .a_wen  (cpu_mem_write),
        .a_din  (cpu_mem_wdata),
        .a_dout (tcm_a_dout),
        .a_addr (cpu_mem_addr[11:2]),
        .b_en   (1'b0),
        .b_wen  (1'b0),
        .b_din  (32'b0),
        .b_dout (tcm_b_dout),
        .b_addr (10'b0)
    );

    assign uo_out  = tcm_a_dout[7:0];
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    wire _unused = &{ui_in, uio_in, tcm_b_dout, cpu_mem_size, 1'b0};

endmodule
