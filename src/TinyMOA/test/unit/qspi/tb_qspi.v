// QSPI controller testbench

`default_nettype none
`timescale 1ns / 1ps

module tb_qspi (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_qspi.fst");
        $dumpvars(0, tb_qspi);
        #1;
    end
    `endif

    reg  [23:0] addr;
    reg         read;
    reg         write;
    reg  [31:0] wdata;
    reg  [1:0]  size;

    wire [31:0] rdata;
    wire        ready;

    reg  [3:0]  spi_data_in;
    wire [3:0]  spi_data_out;
    wire [3:0]  spi_data_oe;
    wire        spi_clk_out;
    wire        spi_flash_cs_n;
    wire        spi_ram_a_cs_n;
    wire        spi_ram_b_cs_n;

    tinymoa_qspi dut (
        .clk            (clk),
        .nrst           (nrst),
        .addr           (addr),
        .read           (read),
        .write          (write),
        .wdata          (wdata),
        .size           (size),
        .rdata          (rdata),
        .ready          (ready),
        .spi_data_in    (spi_data_in),
        .spi_data_out   (spi_data_out),
        .spi_data_oe    (spi_data_oe),
        .spi_clk_out    (spi_clk_out),
        .spi_flash_cs_n (spi_flash_cs_n),
        .spi_ram_a_cs_n (spi_ram_a_cs_n),
        .spi_ram_b_cs_n (spi_ram_b_cs_n)
    );
endmodule
