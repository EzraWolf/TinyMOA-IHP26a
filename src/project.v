/*
 * Copyright (c) 2026 Ezra Wolf
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
`default_nettype none

module tt_um_tinymoa_ihp26a (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       ena, // always high, can ignore.
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    inout  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe
);

    tinymoa_top top (
      .clk     (clk),                                                                                                                                                                                                                                                
      .nrst    (rst_n),
      .ena     (ena),                                                                                                                                                                                                                                                
      .ui_in   (ui_in),                                      
      .uo_out  (uo_out),                                                                                                                                                                                                                                             
      .uio_in  (uio_in),
      .uio_out (uio_out),
      .uio_oe  (uio_oe)                                                                                                                                                                                                                                              
    );       

    wire _unused = ena;
endmodule
