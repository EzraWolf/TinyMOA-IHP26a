// TinyMOA ALU -- full 32-bit combinational
//
// Opcodes:
//   0000  ADD
//   0001  SUB
//   0010  SLT
//   0011  SLTU
//   0100  XOR
//   0101  OR
//   0110  AND
//   1000  SLL
//   1001  SRL
//   1010  SRA
//   1011  MUL  (16x16 unsigned -> 32-bit)
//   1110  CZERO.EQZ
//   1111  CZERO.NEZ

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_alu (
    input  [3:0]  opcode,
    input  [31:0] a_in,
    input  [31:0] b_in,
    input         c_in,
    output [31:0] result
);

    // opcodes 00xx all use the adder; 0001/0010/0011 subtract
    wire is_sub = opcode[0] | opcode[1];
    wire [31:0] sum = is_sub ?
        (a_in - b_in + {31'd0, c_in}) :
        (a_in + b_in + {31'd0, c_in});

    reg [31:0] out;
    always @(*) begin
        case (opcode)
            4'b0000: out = sum;                                    // ADD
            4'b0001: out = sum;                                    // SUB
            4'b0010: out = {31'd0, $signed(a_in) < $signed(b_in)}; // SLT
            4'b0011: out = {31'd0, a_in < b_in};                   // SLTU

            4'b0100: out = a_in ^ b_in;                            // XOR
            4'b0101: out = a_in | b_in;                            // OR
            4'b0110: out = a_in & b_in;                            // AND

            4'b1000: out = a_in << b_in[4:0];                      // SLL
            4'b1001: out = a_in >> b_in[4:0];                      // SRL
            4'b1010: out = $unsigned($signed(a_in) >>> b_in[4:0]); // SRA

            4'b1011: out = a_in[15:0] * b_in[15:0];                // MUL
            
            4'b1110: out = (b_in == 32'd0) ? 32'd0 : a_in;         // CZERO.EQZ
            4'b1111: out = (b_in != 32'd0) ? 32'd0 : a_in;         // CZERO.NEZ
            default: out = 32'd0;
        endcase
    end

    assign result = out;

endmodule
