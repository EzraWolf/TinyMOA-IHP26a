// TinyMOA ALU — 4-bit nibble-serial with shifter and multiplier
//
// Three datapaths, selected by core FSM based on decoded opcode:
//   1. Nibble-serial ALU — carry-chained ADD/SUB/AND/OR/XOR/SLT/SLTU/CZERO
//   2. Shifter           — SLL/SRL/SRA (needs full operand + shift amount)
//   3. Multiplier        — C.MUL: 16x16 signed -> 32-bit
//
// Comparison outputs (cmp_out) used for branches:
//   opcode[0]=1: unsigned compare (SLTU/BGEU/BLTU)
//   opcode[1]=1: signed compare (SLT/BGE/BLT)
//   else:        equality (XOR == 0, for BEQ/BNE)

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_alu (
    input [3:0] opcode,

    input [3:0] a_in,
    input [3:0] b_in,
    input       c_in,

    output reg [3:0] result,
    output     c_out,

    input      cmp_in,
    output reg cmp_out
);

    // Conditional invert for SUB (opcode[3]) and compares (opcode[1])
    wire [3:0] b_inv   = (opcode[1] || opcode[3]) ? ~b_in : b_in;
    wire [4:0] sum     = {1'b0, a_in} + {1'b0, b_inv} + {4'b0, c_in};
    wire [3:0] xor_out = a_in ^ b_in;

    assign c_out = sum[4];

    always @(*) begin
        result  = 4'd0;
        cmp_out = cmp_in;

        case (opcode)
            4'b0000: result = sum[3:0];    // ADD
            4'b1000: result = sum[3:0];    // SUB (b_inv already inverts B)
            4'b0100: result = xor_out;     // XOR
            4'b0110: result = a_in | b_in; // OR
            4'b0111: result = a_in & b_in; // AND
            4'b1110: result = a_in;        // CZERO.EQZ (zeroes rd if rs2==0)
            4'b1111: result = a_in;        // CZERO.NEZ (zeroes rd if rs2!=0)
            default: result = 4'd0;
        endcase

        // Comparison logic (valid for SLT/SLTU/BEQ/BNE/BLT/BGE etc.)
        // NOTE: While this "falsely" updates on unintended instructions like AND/OR, cmp_out is simply ignored.
        if      (opcode[0]) cmp_out = ~sum[4];                     // SLTU
        else if (opcode[1]) cmp_out = a_in[3] ^ b_inv[3] ^ sum[4]; // SLT
        else                cmp_out = cmp_in && (xor_out == 4'd0); // EQ
    end

endmodule
