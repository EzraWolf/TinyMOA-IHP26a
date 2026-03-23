// Tightly Coupled Memory Testbench

`default_nettype none
`timescale 1ns / 1ps

module tb_tcm (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_tcm.fst");
        $dumpvars(0, tb_tcm);
        #1;
    end
    `endif

    // Port A stimulus (CPU interface, 32-bit)
    reg [9:0] a_addr;
    reg [31:0] a_din;
    reg a_en;
    reg a_wen;

    // Port B stimulus (boot/DCIM interface, 32-bit)
    reg [9:0] b_addr;
    reg [31:0] b_din;
    reg b_en;
    reg b_wen;

    // DUT outputs
    wire [31:0] a_dout;
    wire [31:0] b_dout;

    tinymoa_tcm dut_tcm (
        .clk(clk),
        .a_addr(a_addr),
        .a_din(a_din),
        .a_dout(a_dout),
        .a_en(a_en),
        .a_wen(a_wen),
        .b_addr(b_addr),
        .b_din(b_din),
        .b_dout(b_dout),
        .b_en(b_en),
        .b_wen(b_wen)
    );

    always @(posedge clk) begin
        // Stimulus driving happens via cocotb
    end
endmodule
