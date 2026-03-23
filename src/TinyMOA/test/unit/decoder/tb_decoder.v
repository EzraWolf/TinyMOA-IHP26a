// RV32EC decoder test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_decoder (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_decoder.fst");
        $dumpvars(0, tb_decoder);
        #1;
    end
    `endif

    // Test stimulus (combinational)
    reg [31:0] instr;

    // DUT outputs
    wire [31:0] imm;
    wire [3:0] alu_opcode;
    wire [2:0] mem_opcode;
    wire [3:0] rs1, rs2, rd;
    wire is_load, is_store, is_branch, is_jal, is_jalr;
    wire is_lui, is_auipc, is_alu_reg, is_alu_imm;
    wire is_system, is_compressed;

    tinymoa_decoder dut_decoder (
        .instr(instr),
        .imm(imm),
        .alu_opcode(alu_opcode),
        .mem_opcode(mem_opcode),
        .rs1(rs1),
        .rs2(rs2),
        .rd(rd),
        .is_load(is_load),
        .is_store(is_store),
        .is_branch(is_branch),
        .is_jal(is_jal),
        .is_jalr(is_jalr),
        .is_lui(is_lui),
        .is_auipc(is_auipc),
        .is_alu_reg(is_alu_reg),
        .is_alu_imm(is_alu_imm),
        .is_system(is_system),
        .is_compressed(is_compressed)
    );

    always @(posedge clk) begin
        // Stimulus driving happens via cocotb
    end
endmodule
