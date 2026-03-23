`default_nettype none
`timescale 1ns / 1ps

// Hex-to-7-segment decoder (common cathode)
// seg = {g, f, e, d, c, b, a}
module segment_display (
    input wire [3:0] hex,
    output reg [6:0] seg
);
    always @(*) begin
        case (hex)
            4'h0: seg = 7'b0111111;  // 0
            4'h1: seg = 7'b0000110;  // 1
            4'h2: seg = 7'b1011011;  // 2
            4'h3: seg = 7'b1001111;  // 3
            4'h4: seg = 7'b1100110;  // 4
            4'h5: seg = 7'b1101101;  // 5
            4'h6: seg = 7'b1111101;  // 6
            4'h7: seg = 7'b0000111;  // 7
            4'h8: seg = 7'b1111111;  // 8
            4'h9: seg = 7'b1101111;  // 9
            4'hA: seg = 7'b1110111;  // A
            4'hB: seg = 7'b1111100;  // b
            4'hC: seg = 7'b0111001;  // C
            4'hD: seg = 7'b1011110;  // d
            4'hE: seg = 7'b1111001;  // E
            4'hF: seg = 7'b1110001;  // F
        endcase
    end
endmodule
