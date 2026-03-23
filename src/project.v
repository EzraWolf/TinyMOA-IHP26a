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
    input  wire [7:0] uio_io,
    output wire [7:0] uio_oe
);
    tinymoa_top top (
        .clk    (clk),
        .nrst   (rst_n),
        .ui_in  (ui_in),
        .uo_out (uo_out),
        .uio_io (uio_io),
        .uio_oe (uio_oe)
    );

    wire _unused = ena;
endmodule
