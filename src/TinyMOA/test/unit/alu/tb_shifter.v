// Shifter test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_shifter (
    input [3:0]  opcode,
    input [2:0]  nibble_ct,
    input [31:0] data_in,
    input [4:0]  shift_amnt,

    output [3:0] result
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_shifter.fst");
        $dumpvars(0, tb_shifter);
        #1;
    end
    `endif

    tinymoa_shifter dut_shifter (
        .opcode (opcode),
        .nibble_ct (nibble_ct),
        .data_in (data_in),
        .shift_amnt (shift_amnt),
        .result (result)
    );
endmodule
