/*
 * Copyright (c) 2026 Ezra Wolf
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Example from
// https://github.com/Dullbi/8bit_up-down_counter/blob/d0e6485f4578b2b1da64d66e02ddbc277e2e7412/src/project.v

module tt_um_tinymoa_ihp26a (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path (unused)
    output wire [7:0] uio_out,  // IOs: Output path (unused)
    output wire [7:0] uio_oe,   // IOs: Enable path (unused)
    input  wire       ena,      // always 1 when powered
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Map ui_in bits for control signals
  wire enable   = ui_in[0];  // bit 0: enable
  wire up_down  = ui_in[1];  // bit 1: direction (1=up, 0=down)

  // Active-low reset is provided, so convert it
  wire reset = ~rst_n;

  // Counter output
  reg [7:0] q;

  always @(posedge clk) begin
      if (reset)
          q <= 8'b00000000;        // reset to 0
      else if (enable) begin
          if (up_down)
              q <= q + 1;          // count up
          else
              q <= q - 1;          // count down
      end
  end

  // Connect outputs
  assign uo_out  = q;      // 8-bit counter output
  assign uio_out = 8'b0;   // unused
  assign uio_oe  = 8'b0;   // unused

  // Prevent warnings for unused inputs
  wire _unused = &{ena, uio_in, 1'b0};
endmodule
