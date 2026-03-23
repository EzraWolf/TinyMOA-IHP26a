// TinyMOA Register File -- RV32E, 32-bit single-cycle 2R1W
//
// x0:  hardwired 0 (combinational, no storage)
// x3 (gp): pseudo-hardcoded 0x000400 -- TCM globals midpoint
// x4 (tp): pseudo-hardcoded 0x400000 -- DCIM MMIO base
// x1, x2, x5-x15: 12 storage registers (32-bit FFs)
//
// Writes to x0/gp/tp: storage written but read mux always returns hardcoded value.
// Read ports are purely combinational (no read-enable needed).

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_registers (
    input  clk,
    input  nrst,

    input  [3:0]  rs1_sel,
    output [31:0] rs1_data,

    input  [3:0]  rs2_sel,
    output [31:0] rs2_data,

    input         rd_wen,
    input  [3:0]  rd_sel,
    input  [31:0] rd_data
);

    localparam [31:0] GP_VAL = 32'h000400; // x3
    localparam [31:0] TP_VAL = 32'h400000; // x4

    // Storage x1-x15 (x0 hardwired, so no x0 storage needed)
    reg [31:0] r [1:15];

    // Write port: synchronous, x0 writes silently discarded
    integer k;
    always @(posedge clk) begin
        if (!nrst) begin
            for (k = 1; k < 16; k = k + 1)
                r[k] <= 32'd0;
        end else if (rd_wen && rd_sel != 4'd0) begin
            r[rd_sel] <= rd_data;
        end
    end

    // Read mux: combinational, x0/gp/tp return hardcoded values
    function [31:0] reg_read;
        input [3:0] sel;
        case (sel)
            4'd0:    reg_read = 32'd0;
            4'd3:    reg_read = GP_VAL;
            4'd4:    reg_read = TP_VAL;
            4'd1:    reg_read = r[1];
            4'd2:    reg_read = r[2];
            4'd5:    reg_read = r[5];
            4'd6:    reg_read = r[6];
            4'd7:    reg_read = r[7];
            4'd8:    reg_read = r[8];
            4'd9:    reg_read = r[9];
            4'd10:   reg_read = r[10];
            4'd11:   reg_read = r[11];
            4'd12:   reg_read = r[12];
            4'd13:   reg_read = r[13];
            4'd14:   reg_read = r[14];
            4'd15:   reg_read = r[15];
            default: reg_read = 32'd0;
        endcase
    endfunction

    assign rs1_data = reg_read(rs1_sel);
    assign rs2_data = reg_read(rs2_sel);

endmodule
