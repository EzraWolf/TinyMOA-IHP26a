// TinyMOA test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_tinymoa (
    input clk,
    input nrst,

    // TODO
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_tinymoa.fst");
        $dumpvars(0, tb_tinymoa);
        #1;
    end
    `endif

    tinymoa_top dut_tinymoa (
        // TODO
    );
endmodule
