// TinyMOA SRAM wrapper -- dual-port TCM
//
// Synthesis: empty body causes OpenLane to use the pre-generated IHP macro.
// Simulation: ifdef FUNCTIONAL provides a behavioral model.
//
// Port A: CPU (read/write). Port B: boot FSM write, then DCIM read/write.
// Address is 10-bit word address (supports up to 1024x32). IHP macro is 9-bit
// (512x32) -- instantiate two or upgrade to 1024x32 macro when available.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_tcm (
    input clk,

    input         a_en,
    input         a_wen,
    input  [31:0] a_din,
    output [31:0] a_dout,
    input  [9:0]  a_addr,

    input         b_en,
    input         b_wen,
    input  [31:0] b_din,
    output [31:0] b_dout,
    input  [9:0]  b_addr
);

`ifdef BEHAVIORAL
    reg [31:0] mem [0:511];
    reg [31:0] a_dout_r, b_dout_r;

    always @(posedge clk) begin
        if (a_en) begin
            if (a_wen) mem[a_addr] <= a_din;
            a_dout_r <= mem[a_addr];
        end
        if (b_en) begin
            if (b_wen) mem[b_addr] <= b_din;
            b_dout_r <= mem[b_addr];
        end
    end

    assign a_dout = a_dout_r;
    assign b_dout = b_dout_r;
`else
    RM_IHPSG13_2P_512x32_c2_bm_bist sram (

        // Port A
        .A_CLK(clk),
        .A_MEN(a_en),
        .A_WEN(a_wen),
        .A_REN(a_en && !a_wen),
        .A_ADDR(a_addr[8:0]),
        .A_DIN(a_din),
        .A_DOUT(a_dout),
        .A_BM(32'hFFFFFFFF),
        .A_DLY(1'b0),

        // Port B
        .B_CLK(clk),
        .B_MEN(b_en),
        .B_WEN(b_wen),
        .B_REN(b_en && !b_wen),
        .B_ADDR(b_addr[8:0]),
        .B_DIN(b_din),
        .B_DOUT(b_dout),
        .B_BM(32'hFFFFFFFF),
        .B_DLY(1'b0),

        // Disabled
        .A_BIST_CLK(1'b0),
        .A_BIST_EN(1'b0),
        .A_BIST_MEN(1'b0),
        .A_BIST_WEN(1'b0),
        .A_BIST_REN(1'b0),
        .A_BIST_ADDR(9'b0),
        .A_BIST_DIN(32'b0),
        .A_BIST_BM(32'b0),

        // Disabled
        .B_BIST_CLK(1'b0),
        .B_BIST_EN(1'b0),
        .B_BIST_MEN(1'b0),
        .B_BIST_WEN(1'b0),
        .B_BIST_REN(1'b0),
        .B_BIST_ADDR(9'b0),
        .B_BIST_DIN(32'b0),
        .B_BIST_BM(32'b0)
    );
`endif

endmodule


module RM_IHPSG13_2P_512x32_c2_bm_bist (

    // Port A
    input         A_CLK,
    input         A_MEN,
    input         A_WEN,
    input         A_REN,
    input  [8:0]  A_ADDR,
    input  [31:0] A_DIN,
    input         A_DLY,
    output [31:0] A_DOUT,
    input  [31:0] A_BM,

    input A_BIST_CLK,
    input A_BIST_EN,
    input A_BIST_MEN,
    input A_BIST_WEN,
    input A_BIST_REN,
    input [8:0] A_BIST_ADDR,
    input [31:0] A_BIST_DIN,
    input [31:0] A_BIST_BM,

    // Port B
    input         B_CLK,
    input         B_MEN,
    input         B_WEN,
    input         B_REN,
    input  [8:0]  B_ADDR,
    input  [31:0] B_DIN,
    input         B_DLY,
    output [31:0] B_DOUT,
    input  [31:0] B_BM,

    input         B_BIST_CLK,
    input         B_BIST_EN,
    input         B_BIST_MEN,
    input         B_BIST_WEN,
    input         B_BIST_REN,
    input  [8:0]  B_BIST_ADDR,
    input  [31:0] B_BIST_DIN,
    input  [31:0] B_BIST_BM
)
    // Empty for LEF.
endmodule
