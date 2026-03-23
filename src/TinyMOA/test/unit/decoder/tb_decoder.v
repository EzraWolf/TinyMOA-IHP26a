// RV32EC decoder test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_decoder (
    input [31:0] instr,

    output reg  [31:0] imm,
    output reg  [3:0]  alu_opcode,
    output reg  [2:0]  mem_opcode, // [1:0]=size, [2]=unsigned
    output reg  [3:0]  rs1,
    output reg  [3:0]  rs2,
    output reg  [3:0]  rd,

    output reg         is_load,
    output reg         is_store,
    output reg         is_branch,
    output reg         is_jal,
    output reg         is_jalr,
    output reg         is_lui,
    output reg         is_auipc,
    output reg         is_alu_reg,
    output reg         is_alu_imm,
    output reg         is_system,
    output reg         is_compressed
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_decoder.fst");
        $dumpvars(0, tb_decoder);
        #1;
    end
    `endif

    tinymoa_decoder dut_decoder (
        .instr         (instr),
        .imm           (imm),
        .alu_opcode    (alu_opcode),
        .mem_opcode    (mem_opcode),
        .rs1           (rs1),
        .rs2           (rs2),
        .rd            (rd),
        .is_load       (is_load),
        .is_store      (is_store),
        .is_branch     (is_branch),
        .is_jal        (is_jal),
        .is_jalr       (is_jalr),
        .is_lui        (is_lui),
        .is_auipc      (is_auipc),
        .is_alu_reg    (is_alu_reg),
        .is_alu_imm    (is_alu_imm),
        .is_system     (is_system),
        .is_compressed (is_compressed)
    );
endmodule
