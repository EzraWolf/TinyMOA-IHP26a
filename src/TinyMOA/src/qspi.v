// TinyMOA QSPI controller
//
// QSPI mode (4 bits per system clock cycle).
// CS selection: addr[23:22]: 00=flash, 01=ram_a, 10=ram_b, 11=peripheral
//
// Transaction sequence:
//    CMD     (2 cycles):     8-bit command, 4b/cycle, MSN first (0x03=read, 0x02=write)
//    ADDR_TX (6 cycles):     24-bit address, 4b/cycle, MSN first
//    DATA_RX (2/4/8 cycles): read data in from SPI (byte/half/word)
//    DATA_TX (2/4/8 cycles): write data out to SPI (byte/half/word)
//    DONE    (1 cycle):      deassert CS, pulse ready, return IDLE
//
// spi_clk_out toggles every system clock during CMD/ADDR_TX/DATA_RX/DATA_TX.
// spi_data_oe = 4'hF during CMD/ADDR_TX/DATA_TX, 4'h0 during DATA_RX.

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

    output reg        spi_clk_out,
    output reg        spi_flash_cs_n,
    output reg        spi_ram_a_cs_n,
    output reg        spi_ram_b_cs_n,
    output reg [3:0]  spi_data_oe,
    input      [3:0]  spi_data_in,
    output reg [3:0]  spi_data_out
);
    localparam IDLE    = 3'd0;
    localparam CMD     = 3'd1;
    localparam ADDR_TX = 3'd2;
    localparam DATA_RX = 3'd3;
    localparam DATA_TX = 3'd4;
    localparam DONE    = 3'd5;

    reg [2:0]  state;
    reg [3:0]  cnt;        // nibble counter within each state
    reg [23:0] addr_reg;
    reg [31:0] wdata_reg;  // pre-shifted so MSN is first nibble to send
    reg [1:0]  size_reg;
    reg        is_write;

    // Last nibble index for data phase: byte=1, half=3, word=7
    wire [3:0] data_last = (size_reg == 2'd0) ? 4'd1 :
                           (size_reg == 2'd1) ? 4'd3 : 4'd7;

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
            cnt            <= 4'd0;
            addr_reg       <= 24'd0;
            wdata_reg      <= 32'd0;
            size_reg       <= 2'd0;
            is_write       <= 1'b0;
        end else begin
            ready <= 1'b0;
            case (state)
                IDLE: begin
                    spi_clk_out <= 1'b0;
                    spi_data_oe <= 4'd0;
                    if (read || write) begin
                        addr_reg  <= addr;
                        size_reg  <= size;
                        is_write  <= write;
                        // Pre-shift write data so MSN is at bits[31:28]
                        case (size)
                            2'd0: wdata_reg <= {wdata[7:0],  24'b0};
                            2'd1: wdata_reg <= {wdata[15:0], 16'b0};
                            default: wdata_reg <= wdata;
                        endcase
                        // Assert CS (active low) based on addr[23:22]
                        case (addr[23:22])
                            2'b01: spi_ram_a_cs_n <= 1'b0;
                            2'b10: spi_ram_b_cs_n <= 1'b0;
                            default: spi_flash_cs_n <= 1'b0;
                        endcase
                        cnt   <= 4'd0;
                        state <= CMD;
                    end
                end

                // --------------------------------------------------------
                // CMD: 2 nibbles of command byte (0x03=read, 0x02=write)
                // --------------------------------------------------------
                CMD: begin
                    spi_clk_out  <= ~spi_clk_out;
                    spi_data_oe  <= 4'hF;
                    spi_data_out <= (cnt == 4'd0) ?
                        (is_write ? 4'h0 : 4'h0) :   // cmd upper nibble: 0x0 for both
                        (is_write ? 4'h2 : 4'h3);     // cmd lower nibble: 2=write, 3=read
                    cnt <= cnt + 4'd1;
                    if (cnt == 4'd1) begin
                        cnt   <= 4'd0;
                        state <= ADDR_TX;
                    end
                end

                // ADDR_TX: 6 nibbles of 24-bit address, MSN first
                ADDR_TX: begin
                    spi_clk_out  <= ~spi_clk_out;
                    spi_data_oe  <= 4'hF;
                    case (cnt[2:0])
                        3'd0: spi_data_out <= addr_reg[23:20];
                        3'd1: spi_data_out <= addr_reg[19:16];
                        3'd2: spi_data_out <= addr_reg[15:12];
                        3'd3: spi_data_out <= addr_reg[11:8];
                        3'd4: spi_data_out <= addr_reg[7:4];
                        3'd5: spi_data_out <= addr_reg[3:0];
                        default: spi_data_out <= 4'd0;
                    endcase
                    cnt <= cnt + 4'd1;
                    if (cnt == 4'd5) begin
                        cnt   <= 4'd0;
                        state <= is_write ? DATA_TX : DATA_RX;
                    end
                end

                // DATA_RX: clock in data nibbles, MSN first, shift into rdata
                DATA_RX: begin
                    spi_clk_out  <= ~spi_clk_out;
                    spi_data_oe  <= 4'h0;
                    spi_data_out <= 4'd0;
                    rdata        <= {rdata[27:0], spi_data_in};
                    cnt          <= cnt + 4'd1;
                    if (cnt == data_last) begin
                        cnt   <= 4'd0;
                        state <= DONE;
                    end
                end

                // DATA_TX: clock out wdata nibbles, MSN first
                DATA_TX: begin
                    spi_clk_out  <= ~spi_clk_out;
                    spi_data_oe  <= 4'hF;
                    spi_data_out <= wdata_reg[31:28];
                    wdata_reg    <= {wdata_reg[27:0], 4'b0};
                    cnt          <= cnt + 4'd1;
                    if (cnt == data_last) begin
                        cnt   <= 4'd0;
                        state <= DONE;
                    end
                end

                // --------------------------------------------------------
                // DONE: deassert CS, pulse ready, return to IDLE
                // --------------------------------------------------------
                DONE: begin
                    spi_clk_out    <= 1'b0;
                    spi_data_oe    <= 4'h0;
                    spi_flash_cs_n <= 1'b1;
                    spi_ram_a_cs_n <= 1'b1;
                    spi_ram_b_cs_n <= 1'b1;
                    ready          <= 1'b1;
                    state          <= IDLE;
                end

                default: state <= IDLE;

            endcase
        end
    end

endmodule
