// TinyMOA Top-Level -- TinyTapeout IHP26a wrapper
//
// Address decode (24-bit bus):
//   addr[23:11] == 0            -> SRAM (2 KB, 512x32, word addr = addr[10:2])
//   addr[23:22] == 00, !is_sram -> QSPI Flash
//   addr[23:22] == 01           -> Peripherals (DCIM MMIO at 0x400000)
//   addr[23:22] == 10           -> QSPI PSRAM A
//   addr[23:22] == 11           -> QSPI PSRAM B
//
// Port B mux: tinymoa_bootloader owns Port B until boot_done, then tinymoa_dcim takes over.
//
// TCM read latency: 1 cycle (synchronous). tcm_ready registered accordingly.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_top (
    input  clk,
    input  nrst,
    input  [7:0] ui_in,
    output [7:0] uo_out,
    input  [7:0] uio_in,
    output [7:0] uio_out,
    output [7:0] uio_oe
);
    wire [23:0] cpu_addr;
    wire        cpu_read;
    reg  [31:0] cpu_rdata;
    wire        cpu_write;
    wire [31:0] cpu_wdata;
    wire [1:0]  cpu_size;
    reg         cpu_ready;

    // Address decode: 0x000000 - 0x0007FF (SRAM 512x32, 2KB)
    wire is_tcm     = (cpu_addr[23:11] == 13'd0);
    wire is_flash   = (cpu_addr[23:22] == 2'b00) && !is_tcm;
    wire is_periph  = (cpu_addr[23:22] == 2'b01);
    wire is_psram_a = (cpu_addr[23:22] == 2'b10);
    wire is_psram_b = (cpu_addr[23:22] == 2'b11);
    wire is_qspi    = is_flash || is_psram_a || is_psram_b;

    // Boot control
    wire        boot_done;
    wire        cpu_nrst = nrst && boot_done;

    // TCM Port A (CPU)
    wire [9:0]  tcm_a_addr = {1'b0, cpu_addr[10:2]};
    wire [31:0] tcm_a_dout;
    wire [31:0] tcm_a_din  = cpu_wdata;
    wire        tcm_a_en   = is_tcm && (cpu_read || cpu_write);
    wire        tcm_a_wen  = is_tcm && cpu_write;

    // TCM Port B (boot -> DCIM)
    wire [9:0]  boot_b_addr;
    wire [31:0] boot_b_din;
    wire        boot_b_wen;
    wire [9:0]  dcim_b_addr;
    wire [31:0] dcim_b_din;
    wire [31:0] tcm_b_dout;
    wire        dcim_b_wen;
    wire        dcim_b_ren;

    wire [9:0]  tcm_b_addr = boot_done ? dcim_b_addr : boot_b_addr;
    wire [31:0] tcm_b_din  = boot_done ? dcim_b_din  : boot_b_din;
    wire        tcm_b_wen  = boot_done ? dcim_b_wen  : boot_b_wen;
    wire        tcm_b_en   = boot_done ? (dcim_b_wen || dcim_b_ren) : boot_b_wen;

    reg tcm_ready; // Asserted the cycle after the req
    always @(posedge clk) begin
        if (!nrst)
            tcm_ready <= 1'b0;
        else
            tcm_ready <= tcm_a_en;
    end

    // QSPI interface
    wire [3:0]  spi_data_in  = {uio_in[5], uio_in[4], uio_in[2], uio_in[1]};
    wire [3:0]  spi_data_out;
    wire [3:0]  spi_data_oe;
    wire        spi_clk_out;
    wire        spi_flash_cs_n;
    wire        spi_ram_a_cs_n;
    wire        spi_ram_b_cs_n;

    wire [31:0] qspi_rdata;
    wire        qspi_ready;

    // Boot FSM owns QSPI until boot_done sets
    wire [23:0] boot_flash_addr;
    wire        boot_qspi_read;

    wire [23:0] qspi_addr  = boot_done ? cpu_addr               : boot_flash_addr;
    wire        qspi_read  = boot_done ? (cpu_read && is_qspi)  : boot_qspi_read;
    wire        qspi_write = boot_done ? (cpu_write && is_qspi) : 1'b0;
    wire [31:0] qspi_wdata = boot_done ? cpu_wdata              : 32'd0;
    wire [1:0]  qspi_size  = boot_done ? cpu_size               : 2'b10;

    // DCIM MMIO
    wire [31:0] dcim_rdata;
    wire        dcim_ready;

    // CPU memory response mux
    always @(*) begin
        if (is_tcm) begin
            cpu_rdata = tcm_a_dout;
            cpu_ready = tcm_ready;
        end else if (is_qspi) begin
            cpu_rdata = qspi_rdata;
            cpu_ready = qspi_ready;
        end else begin
            cpu_rdata = dcim_rdata;
            cpu_ready = dcim_ready;
        end
    end

    // === Submodule instances ===

    tinymoa_cpu cpu (
        .clk        (clk),
        .nrst       (cpu_nrst),
        .mem_ready  (cpu_ready),
        .mem_size   (cpu_size),
        .mem_read   (cpu_read),
        .mem_rdata  (cpu_rdata),
        .mem_write  (cpu_write),
        .mem_wdata  (cpu_wdata),
        .mem_addr   (cpu_addr)
    );

    tinymoa_tcm tcm (
        .clk    (clk),
        .a_en   (tcm_a_en),
        .a_wen  (tcm_a_wen),
        .a_din  (tcm_a_din),
        .a_dout (tcm_a_dout),
        .a_addr (tcm_a_addr),
        .b_en   (tcm_b_en),
        .b_wen  (tcm_b_wen),
        .b_din  (tcm_b_din),
        .b_dout (tcm_b_dout),
        .b_addr (tcm_b_addr)
    );

    tinymoa_bootloader bootloader (
        .clk       (clk),
        .nrst      (nrst),
        .boot_done (boot_done),
        .rom_ready (qspi_ready),
        .rom_read  (boot_qspi_read),
        .rom_rdata (qspi_rdata),
        .rom_addr  (boot_flash_addr),
        .tcm_din   (boot_b_din),
        .tcm_addr  (boot_b_addr),
        .tcm_wen   (boot_b_wen)

    );

    tinymoa_qspi qspi (
        .clk            (clk),
        .nrst           (nrst),
        .size           (qspi_size),
        .ready          (qspi_ready),
        .read           (qspi_read),
        .rdata          (qspi_rdata),
        .write          (qspi_write),
        .wdata          (qspi_wdata),
        .addr           (qspi_addr),
        .spi_clk_out    (spi_clk_out),
        .spi_flash_cs_n (spi_flash_cs_n),
        .spi_ram_a_cs_n (spi_ram_a_cs_n),
        .spi_ram_b_cs_n (spi_ram_b_cs_n),
        .spi_data_oe    (spi_data_oe),
        .spi_data_in    (spi_data_in),
        .spi_data_out   (spi_data_out)
    );

    tinymoa_dcim dcim (
        .clk        (clk),
        .nrst       (nrst && boot_done),
        .mmio_ready (dcim_ready),
        .mmio_write (is_periph && cpu_write),
        .mmio_wdata (cpu_wdata),
        .mmio_read  (is_periph && cpu_read),
        .mmio_rdata (dcim_rdata),
        .mmio_addr  (cpu_addr[5:0]),
        .mem_write  (dcim_b_wen),
        .mem_wdata  (dcim_b_din),
        .mem_read   (dcim_b_ren),
        .mem_rdata  (tcm_b_dout),
        .mem_addr   (dcim_b_addr)
    );

    wire _unused = &{ui_in, 1'b0};

endmodule
