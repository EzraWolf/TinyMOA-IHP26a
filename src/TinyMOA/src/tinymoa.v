`default_nettype none
`timescale 1ns / 1ps

module tinymoa_top (
    input wire       clk,
    input wire       rst_n,
    input wire       ena,
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe
);

    // Core memory bus
    wire [23:0] mem_addr;
    wire        mem_read;
    wire        mem_write;
    wire [31:0] mem_a_din;
    wire [31:0] mem_b_din;
    wire [1:0]  mem_size;

    // Address decode
    wire is_sram    = (mem_addr[23:11] == 13'd0);
    wire is_flash   = (mem_addr[23:22] == 2'b00) && !is_sram;
    wire is_periph  = (mem_addr[23:22] == 2'b01);
    wire is_psram_a = (mem_addr[23:22] == 2'b10);
    wire is_psram_b = (mem_addr[23:22] == 2'b11);
    wire is_qspi    = is_flash || is_psram_a || is_psram_b;

    // CPU core
    wire [2:0]  dbg_state;
    wire [23:0] dbg_pc;
    reg  [31:0] core_rdata;
    reg         core_ready;

    tinymoa_core core (
        .clk      (clk),
        .nrst     (rst_n),
        .mem_addr (mem_addr),
        .mem_read (mem_read),
        .mem_write(mem_write),
        .mem_wdata(mem_a_din),
        .mem_size (mem_size),
        .mem_rdata(core_rdata),
        .mem_ready(core_ready),
        .dbg_state(dbg_state),
        .dbg_pc   (dbg_pc)
    );

    // SRAM scratchpad (512x32 = 2 KB)
    wire [8:0] sram_a_addr = mem_addr[10:2];
    reg [31:0] sram_a_dout;
    wire [8:0] sram_b_addr;
    reg [31:0] sram_b_dout;
    reg        sram_ready;

    // IHP SG13G2 512x32 single-port SRAM macro
    wire sram_en  = is_sram && (mem_read || mem_write);
    wire sram_wen = is_sram && mem_write;

    // Dual-port
    RM_IHPSG13_2P_512x32_c2_bm_bist sram (
        .A_CLK      (clk),
        .A_MEN      (sram_en),
        .A_WEN      (sram_wen),
        .A_REN      (sram_en && !sram_wen),
        .A_ADDR     (sram_a_addr),
        .A_DIN      (mem_a_din),
        .A_DLY      (1'b0),
        .A_DOUT     (sram_a_dout),
        .A_BM       (32'hFFFFFFFF),

        .A_BIST_CLK (1'b0),
        .A_BIST_EN  (1'b0),
        .A_BIST_MEN (1'b0),
        .A_BIST_WEN (1'b0),
        .A_BIST_REN (1'b0),
        .A_BIST_ADDR(9'd0),
        .A_BIST_DIN (32'd0),
        .A_BIST_BM  (32'd0),

        // Duplicate Port A for now just to get a working macro for OpenLane.
        .B_CLK      (clk),
        .B_MEN      (sram_en),
        .B_WEN      (sram_wen),
        .B_REN      (sram_en && !sram_wen),
        .B_ADDR     (sram_b_addr),
        .B_DIN      (mem_b_din),
        .B_DLY      (1'b0),
        .B_DOUT     (sram_b_dout),
        .B_BM       (32'hFFFFFFFF),

        .B_BIST_CLK (1'b0),
        .B_BIST_EN  (1'b0),
        .B_BIST_MEN (1'b0),
        .B_BIST_WEN (1'b0),
        .B_BIST_REN (1'b0),
        .B_BIST_ADDR(9'd0),
        .B_BIST_DIN (32'd0),
        .B_BIST_BM  (32'd0)
    );

    /* Single-port
    RM_IHPSG13_1P_512x32_c2_bm_bist sram (
        .A_CLK      (clk),
        .A_MEN      (sram_en),
        .A_WEN      (sram_wen),
        .A_REN      (sram_en && !sram_wen),
        .A_ADDR     (sram_a_addr),
        .A_DIN      (mem_a_din),
        .A_DLY      (1'b0),
        .A_DOUT     (sram_a_dout),
        .A_BM       (32'hFFFFFFFF),
        .A_BIST_CLK (1'b0),
        .A_BIST_EN  (1'b0),
        .A_BIST_MEN (1'b0),
        .A_BIST_WEN (1'b0),
        .A_BIST_REN (1'b0),
        .A_BIST_ADDR(9'd0),
        .A_BIST_DIN (32'd0),
        .A_BIST_BM  (32'd0)
    );
    */

    always @(posedge clk) begin
        sram_ready <= sram_en;
    end

    // QSPI controller stubbed out for initial GDS generation
    wire [31:0] qspi_rdata  = 32'd0;
    wire        qspi_ready  = 1'b0;
    wire [3:0]  spi_data_out_w = 4'hF;
    wire [3:0]  spi_data_oe_w  = 4'b0;
    wire        spi_clk_out    = 1'b0;
    wire        spi_flash_cs_n = 1'b1;
    wire        spi_ram_a_cs_n = 1'b1;
    wire        spi_ram_b_cs_n = 1'b1;
    /*
    qspi_controller qspi (
        .clk           (clk),
        .rst_n         (rst_n),
        .addr          (mem_addr),
        .read          (mem_read  && is_qspi),
        .write         (mem_write && is_qspi),
        .wdata         (mem_wdata),
        .size          (mem_size),
        .rdata         (qspi_rdata),
        .ready         (qspi_ready),
        .spi_data_in   (spi_data_in),
        .spi_data_out  (spi_data_out_w),
        .spi_data_oe   (spi_data_oe_w),
        .spi_clk_out   (spi_clk_out),
        .spi_flash_cs_n(spi_flash_cs_n),
        .spi_ram_a_cs_n(spi_ram_a_cs_n),
        .spi_ram_b_cs_n(spi_ram_b_cs_n)
    );
    */

    // Peripherals
    // TODO: CIM, UART, GPIO
    reg [31:0] periph_rdata;
    reg        periph_ready;

    always @(posedge clk) begin
        periph_ready <= 1'b0;
        if (is_periph && (mem_read || mem_write)) begin
            periph_rdata <= 32'd0;
            periph_ready <= 1'b1;
        end
    end

    // Memory response mux
    always @(*) begin
        if (is_sram) begin
            core_rdata = sram_rdata;
            core_ready = sram_ready;
        end else if (is_qspi) begin
            core_rdata = qspi_rdata;
            core_ready = qspi_ready;
        end else begin
            core_rdata = periph_rdata;
            core_ready = periph_ready;
        end
    end

    // QSPI PMOD pin mapping on uio[7:0]
    assign uio_out = {
        spi_ram_b_cs_n,      // [7] RAM_B CS
        spi_ram_a_cs_n,      // [6] RAM_A CS
        spi_data_out_w[3],   // [5] SD3
        spi_data_out_w[2],   // [4] SD2
        spi_clk_out,         // [3] SCK
        spi_data_out_w[1],   // [2] SD1
        spi_data_out_w[0],   // [1] SD0
        spi_flash_cs_n       // [0] Flash CS
    };

    assign uio_oe = {
        1'b1,                // [7] CS always output
        1'b1,                // [6] CS always output
        spi_data_oe_w[3],    // [5]
        spi_data_oe_w[2],    // [4]
        1'b1,                // [3] SCK always output
        spi_data_oe_w[1],    // [2]
        spi_data_oe_w[0],    // [1]
        1'b1                 // [0] CS always output
    };

    // assign spi_data_in = {uio_in[5], uio_in[4], uio_in[2], uio_in[1]};
    wire _unused = &{uio_in, 1'b0};
    assign uo_out = {dbg_state, dbg_pc[4:0]};
endmodule
