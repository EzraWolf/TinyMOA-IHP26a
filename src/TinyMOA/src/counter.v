// Generic counter with variable data width
// Used for program/nibble counter in cpu.v

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_counter #(
    parameter DATA_WIDTH = 32
) (
    input clk,
    input nrst,

    input en,
    input wen,
    input [DATA_WIDTH-1:0]  data_in,

    output [DATA_WIDTH-1:0] result,
    output c_out
);
    reg [DATA_WIDTH-1:0] count;

    always @(posedge clk or negedge nrst) begin
        if (!nrst)
            count <= {DATA_WIDTH{1'b0}};
        else if (wen)
            count <= data_in;
        else if (en)
            count <= count + 1;
    end

    assign result = count;
    assign c_out = &count;

endmodule
