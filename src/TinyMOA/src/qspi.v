// QSPI controller -- flash read, PSRAM read/write.
// Shared by boot FSM and CPU (muxed in tinymoa.v).
// CS selection driven by addr[23:22] in tinymoa.v, passed in as decoded enables.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_qspi (
    input clk,
    input nrst,

    input      [1:0]  size,
    output reg        ready,

    input             write,
    input      [31:0] wdata,
    input             read,
    output reg [31:0] rdata,
    input      [23:0] addr,

    output reg         spi_clk_out,
    output reg         spi_flash_cs_n,
    output reg         spi_ram_a_cs_n,
    output reg         spi_ram_b_cs_n,
    output reg  [3:0]  spi_data_oe,
    input       [3:0]  spi_data_in,
    output reg  [3:0]  spi_data_out
);
    localparam IDLE    = 3'd0;
    localparam CMD     = 3'd1;
    localparam ADDR_TX = 3'd2;
    localparam DATA_RX = 3'd3;
    localparam DATA_TX = 3'd4;
    localparam DONE    = 3'd5;

    reg [2:0] state;
    reg [4:0] bit_cnt;

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            state          <= IDLE;
            ready          <= 1'b0;
            rdata          <= 32'd0;
            spi_clk_out    <= 1'b0;
            spi_flash_cs_n <= 1'b1;
            spi_ram_a_cs_n <= 1'b1;
            spi_ram_b_cs_n <= 1'b1;
            spi_data_out   <= 4'd0;
            spi_data_oe    <= 4'd0;
            bit_cnt        <= 5'd0;
        end else begin
            ready <= 1'b0;
            case (state)
                IDLE: begin
                    // On read or write: assert CS based on addr[23:22], go to CMD
                end
                CMD: begin
                    // Shift out SPI command (0x03 for flash read, 0x02 for PSRAM write)
                    // In QSPI mode, 2 cycles for 8-bit command at 4b/cycle
                end
                ADDR_TX: begin
                    // Shift out 24-bit address, 4 bits/cycle (6 cycles)
                end
                DATA_RX: begin
                    // Clock in 32-bit data from spi_data_in (8 cycles at 4b/cycle)
                    // Assemble into rdata
                end
                DATA_TX: begin
                    // Clock out wdata to spi_data_out (PSRAM write only)
                end
                DONE: begin
                    // Deassert CS, assert ready, return to IDLE
                end
            endcase
        end
    end

endmodule
