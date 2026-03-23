// Embedded (x0-x15) register test bench

`default_nettype none
`timescale 1ns / 1ps

module tb_registers (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_registers.fst");
        $dumpvars(0, tb_registers);
        #1;
    end
    `endif

    reg [3:0]  rs1_sel;
    reg [3:0]  rs2_sel;
    reg [3:0]  rd_sel;
    reg [31:0] rd_data;
    reg        rd_wen;

    reg [2:0]  nibble_ct;

    reg [31:0] rs1_data;
    reg [31:0] rs2_data;

    // Nibble-serial DUT interface
    wire [3:0] rs1_nibble;
    wire [3:0] rs2_nibble;
    wire [3:0] rd_nibble = rd_data[{nibble_ct, 2'b00} +: 4];

    tinymoa_registers dut_registers (
        .clk       (clk),
        .nrst      (nrst),
        .nibble_ct (nibble_ct),
        .rs1_sel   (rs1_sel),
        .rs1_nibble(rs1_nibble),
        .rs2_sel   (rs2_sel),
        .rs2_nibble(rs2_nibble),
        .rd_wen    (rd_wen),
        .rd_sel    (rd_sel),
        .rd_nibble (rd_nibble)
    );

    always @(posedge clk) begin
        if (!nrst) begin
            nibble_ct <= 3'd0;
            rs1_data  <= 32'd0;
            rs2_data  <= 32'd0;
        end else begin
            // Accumulate read data from nibbles
            rs1_data[{nibble_ct, 2'b00} +: 4] <= rs1_nibble;
            rs2_data[{nibble_ct, 2'b00} +: 4] <= rs2_nibble;

            // Increment nibble counter (test harness will reset when needed)
            nibble_ct <= nibble_ct + 3'd1;
        end
    end
endmodule
