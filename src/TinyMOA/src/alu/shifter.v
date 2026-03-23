// Shifter: barrel shift on full 32-bit value, output nibble-by-nibble.
// Core collects full rs1 then reads result_nibble for nibble_ct 0..7.
// opcode: 0001=SLL, 0101=SRL, 1101=SRA.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_shifter (
    input  [3:0]  opcode,

    input  [2:0]  nibble_ct,
    
    input  [31:0] data_in,
    input  [4:0]  shift_amnt,

    output [3:0]  result
);

    wire [31:0] sll = data_in << shift_amnt;
    wire [31:0] srl = data_in >> shift_amnt;
    wire signed [31:0] sra = $signed(data_in) >>> shift_amnt;

    wire [31:0] shifted = (!opcode[2]) ? sll :
                           opcode[3]   ? sra : srl;

    assign result = shifted[{nibble_ct, 2'b00} +: 4];

endmodule
