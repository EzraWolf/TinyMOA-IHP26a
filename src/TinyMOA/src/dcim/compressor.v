// TinyMOA 16-input popcount compressor with 3 modes:
//
// Single approximate compressor (DCIM-S):
//    1 Level of AND/OR approx, then 8 bits of exact popcount
//    Output range 0-8
//    ~40% less transistors than exact
//    Worst-case RMSE ≈ 4.03%
//
// Double approximate compressor (DCIM-D):
//    2 Levels of AND/OR approx, then 4 bits of exact popcount
//    Output range 0-4
//    ~55% less transistors than exact
//    Worst-case RMSE ≈ 6.76%
//
// Exact compressor (DCIM-E):
//    Full 16:5 popcount FA tree
//    Zero RMSE, maximum transistor cost
//
// Reference: ISSCC 2022, Wang et al.
// "DIMC: 2219TOPS/W 2569F2/b Digital In-Memory Computing Macro in 28nm Based on Approximate Arithmetic Hardware"

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_compressor (
    input  [15:0] in,
    output [4:0]  out
);

`ifdef SINGLE_APPROX_COMPRESSOR // DCIM-S

    // Level 1 (Approx.): 8 pairs, alternating AND/OR.
    // AND underestimates (+0 when 1+1 should give 2), OR overestimates.
    // Errors partially cancel across paired AND/OR gates.
    wire l1_0 = in[0]  & in[1];
    wire l1_1 = in[2]  | in[3];
    wire l1_2 = in[4]  & in[5];
    wire l1_3 = in[6]  | in[7];
    wire l1_4 = in[8]  & in[9];
    wire l1_5 = in[10] | in[11];
    wire l1_6 = in[12] & in[13];
    wire l1_7 = in[14] | in[15];

    // Level 2 (exact): popcount of 8 bits → range 0-8, fits in 4 bits.
    // Zero-extend to 5 bits for uniform output width with other modes.
    assign out = {1'b0, (4'd0 + l1_0) + l1_1 + l1_2 + l1_3
                              + l1_4  + l1_5 + l1_6 + l1_7};


`elsif DOUBLE_APPROX_COMPRESSOR // DCIM-D

    // Level 1 (Approx.): 8 pairs, alternating AND/OR
    wire l1_0 = in[0]  & in[1];
    wire l1_1 = in[2]  | in[3];
    wire l1_2 = in[4]  & in[5];
    wire l1_3 = in[6]  | in[7];
    wire l1_4 = in[8]  & in[9];
    wire l1_5 = in[10] | in[11];
    wire l1_6 = in[12] & in[13];
    wire l1_7 = in[14] | in[15];

    // Level 2 (Approx.): 4 pairs, alternating AND/OR
    wire l2_0 = l1_0 & l1_1;
    wire l2_1 = l1_2 | l1_3;
    wire l2_2 = l1_4 & l1_5;
    wire l2_3 = l1_6 | l1_7;

    // Level 3 (Exact): 3-bit popcount counts range 0-4
    // Zero-extend to 5 bits for uniform output width with other modes
    assign out = {2'b0, (3'd0 + l2_0) + l2_1 + l2_2 + l2_3};


`else // EXACT_APPROX_COMPRESSOR (DCIM-E)

    // Synthesis builds an FA tree for exact 16:5 popcount
    // 5'd0 widens the addition chain to prevent 1-bit truncation
    assign out = (5'd0 + in[0]) + in[1]  + in[2]  + in[3]
                       + in[4]  + in[5]  + in[6]  + in[7]
                       + in[8]  + in[9]  + in[10] + in[11]
                       + in[12] + in[13] + in[14] + in[15];
`endif

endmodule
