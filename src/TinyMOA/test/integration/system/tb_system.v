// TinyMOA system integration testbench
//
// Wraps tinymoa_top with PAR IO signals exposed for cocotb.
// Also provides internal signal access for verification.

`default_nettype none
`timescale 1ns / 1ps

module tb_system (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_system.fst");
        $dumpvars(0, tb_system);
        #1;
    end
    `endif

    // PAR control inputs driven by cocotb
    reg       is_parallel;
    reg       par_space;
    reg       par_cpu_nrst;
    reg       par_we;
    reg       par_oe;
    reg [1:0] par_addr;
    reg       dbg_en;

    wire [7:0] ui;
    assign ui = {dbg_en, par_addr, par_oe, par_we, par_cpu_nrst, par_space, is_parallel};

    // Bidirectional data: cocotb drives uio_in[7:4] for writes
    reg  [3:0] par_data_in;
    wire [7:0] uio_in;
    assign uio_in = {par_data_in, 4'b0};

    // Outputs
    wire [7:0] uo;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    // Output decode
    wire       dbg_strobe    = uo[0];
    wire       dbg_frame_end = uo[1];
    wire       par_rdy       = uo[3];
    wire [3:0] par_addr_out  = uo[7:4];
    wire [3:0] par_data_out  = uio_out[7:4];

    tinymoa_top dut (
        .clk     (clk),
        .nrst    (nrst),
        .ui      (ui),
        .uo      (uo),
        .uio_in  (uio_in),
        .uio_out (uio_out),
        .uio_oe  (uio_oe)
    );

    // Internal signal access for verification
    wire [2:0]  cpu_state  = dut.dbg_cpu_state;
    wire [23:0] cpu_pc     = dut.dbg_cpu_pc;
    wire [31:0] cpu_instr  = dut.dbg_cpu_instr;
    wire [31:0] alu_result = dut.dbg_alu_result;
    wire [2:0]  dcim_state = dut.dbg_dcim_state;

endmodule
