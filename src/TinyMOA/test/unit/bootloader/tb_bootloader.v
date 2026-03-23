// Physical bootloader FSM test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_bootloader (
    input clk,
    input nrst,

    output boot_done,

    input             rom_ready,
    output reg        rom_read,
    input      [31:0] rom_rdata,
    output reg [23:0] rom_addr,

    output reg        tcm_wen,
    output reg [31:0] tcm_din,
    output reg [9:0]  tcm_addr
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_bootloader.fst");
        $dumpvars(0, tb_bootloader);
        #1;
    end
    `endif

    tinymoa_bootloader dut_boot (
        .clk       (clk),
        .nrst      (nrst),
        .boot_done (boot_done),
        .rom_ready (rom_ready),
        .rom_read  (rom_read),
        .rom_rdata (rom_rdata),
        .tcm_addr  (tcm_addr),
        .tcm_wen   (tcm_wen),
        .tcm_din   (tcm_din),
        .rom_addr  (rom_addr)
    );

    always @(posedge clk) begin
        // Stimulus (rom_dout, rom_ready) driven via cocotb
    end
endmodule
