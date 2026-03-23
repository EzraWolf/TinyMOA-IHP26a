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

    wire [7:0] ui_in;
    assign ui_in = {dbg_en, par_addr, par_oe, par_we, par_cpu_nrst, par_space, is_parallel};

    // Bidirectional IO bus
    // cocotb drives par_data_in for writes; DUT drives uio_io when uio_oe is set
    reg  [3:0] par_data_in;
    wire [7:0] uio_io;
    wire [7:0] uio_oe;

    // When uio_oe bits are high, the DUT is driving. Otherwise, testbench drives.
    // For simulation, use assign with conditional to model the bidirectional bus.
    assign uio_io[7:4] = uio_oe[7] ? 4'bz : par_data_in;
    assign uio_io[3:0] = 4'b0;

    // Outputs
    wire [7:0] uo_out;

    // Output decode
    wire       dbg_strobe    = uo_out[0];
    wire       dbg_frame_end = uo_out[1];
    wire       par_rdy       = uo_out[3];
    wire [3:0] par_addr_out  = uo_out[7:4];
    wire [3:0] par_data_out  = uio_io[7:4];

    tinymoa_top dut (
        .clk     (clk),
        .nrst    (nrst),
        .ena     (1'b1),
        .ui_in   (ui_in),
        .uo_out  (uo_out),
        .uio_io  (uio_io),
        .uio_oe  (uio_oe)
    );

    // Internal signal access for verification
    wire [2:0]  cpu_state  = dut.dbg_cpu_state;
    wire [23:0] cpu_pc     = dut.dbg_cpu_pc;
    wire [31:0] cpu_instr  = dut.dbg_cpu_instr;
    wire [31:0] alu_result = dut.dbg_alu_result;
    wire [2:0]  dcim_state = dut.dbg_dcim_state;

endmodule
