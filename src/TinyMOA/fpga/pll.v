`default_nettype none
`timescale 1ns / 1ps

// Simple clock divider for Phase 1 testing.
// For production FPGA deployment, generate with icepll:
//   icepll -i 100 -o 50 -f pll_50mhz.v -m
// This generates a PLL using iCE40 SB_PLL40_CORE primitives.

module pll (
    input wire  clkin,
    output wire clkout,
    output wire locked
);

    // Simple 2:1 clock divider (50 MHz from 100 MHz input)
    // Production: replace with icepll-generated SB_PLL40_CORE
    // divider[0] naturally divides the clock by 2
    reg divider;

    always @(posedge clkin) begin
        divider <= ~divider;
    end

    assign clkout = divider;
    assign locked = 1'b1;  // Always locked for clock divider
endmodule
