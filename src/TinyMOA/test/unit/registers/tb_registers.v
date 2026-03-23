// Register file test bench -- 32-bit single-cycle interface

`default_nettype none
`timescale 1ns / 1ps

module tb_registers (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_registers.fst");
        $dumpvars(0, tb_registers);
        #1;
    end
    `endif

    reg  [3:0]  rs1_sel;
    reg  [3:0]  rs2_sel;
    reg  [3:0]  rd_sel;
    reg  [31:0] rd_data;
    reg         rd_wen;

    wire [31:0] rs1_data;
    wire [31:0] rs2_data;

    tinymoa_registers dut_registers (
        .clk      (clk),
        .nrst     (nrst),
        .rs1_sel  (rs1_sel),
        .rs1_data (rs1_data),
        .rs2_sel  (rs2_sel),
        .rs2_data (rs2_data),
        .rd_wen   (rd_wen),
        .rd_sel   (rd_sel),
        .rd_data  (rd_data)
    );

endmodule
