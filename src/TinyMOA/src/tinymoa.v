// TinyMOA top-level wrapper
//
// See docs/Architecture.md for full pin map and debug frame format.
//
// SER mode (ui[0]=0): QSPI interface on uo[7:2] and uio[7:4]
// PAR mode (ui[0]=1): nibble-serial host interface
//   uo[3]   = par_ready (commit pulse after 8 nibbles written)
//   uo[7:4] = addr[3:0] (current word address, low 4 bits)
//   uio[7:4] = data[3:0] (nibble in/out)
//
// Debug (ui[7]=1, any mode): cpu_clk gated, 144-bit frame on uo[0]

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_top (
    input  wire        clk,
    input  wire        nrst,
    input  wire        ena,
    input  wire [7:0]  ui_in,
    output wire [7:0]  uo_out,
    inout  wire [7:0]  uio_io,
    output wire [7:0]  uio_oe
);

    // === Input decode ===
    wire       is_parallel  = ui_in[0];
    wire       par_space    = ui_in[1];
    wire       par_cpu_nrst = ui_in[2];
    wire       par_we       = ui_in[3] & is_parallel;
    wire       par_oe       = ui_in[4] & is_parallel;
    wire [1:0] par_addr     = ui_in[6:5];
    wire       dbg_en       = ui_in[7];

    wire par_is_tcm  = is_parallel & ~par_space;
    wire par_is_mmio = is_parallel &  par_space;

    wire [3:0] par_data_in = uio_io[7:4];

    // === CPU clock gate ===
    wire cpu_clk = clk & ~dbg_en;

    // === PAR nibble + address state machine ===
    //
    // Write: host pulses par_we high for exactly 1 clock per nibble.
    //        After 8 nibbles, par_rdy pulses and word commits.
    // Read:  host holds par_oe high. Nibble counter advances each clock.
    //        After 8 nibbles (wrap), word address increments.
    //
    // par_addr selects region base (TCM mode):
    //   00=code(0x000), 01=weights(0x1A0), 10=acts(0x1C0), 11=results(0x1E0)
    // par_addr selects register (MMIO mode):
    //   00=CTRL, 01=STATUS, 10=WEIGHT_BASE, 11=ACT_BASE

    reg [31:0] par_word_buf;
    reg [2:0]  par_nibble_idx;
    reg        par_rdy;
    reg [9:0]  par_word_addr;
    reg [1:0]  par_addr_prev;

    wire [9:0] par_region_base = (par_addr == 2'd0) ? 10'h000 :
                                  (par_addr == 2'd1) ? 10'h1A0 :
                                  (par_addr == 2'd2) ? 10'h1C0 : 10'h1E0;

    wire par_addr_changed = (par_addr != par_addr_prev);

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            par_word_buf   <= 32'b0;
            par_nibble_idx <= 3'd0;
            par_rdy        <= 1'b0;
            par_word_addr  <= 10'd0;
            par_addr_prev  <= 2'd0;
        end else begin
            // Advance word address on the cycle AFTER par_rdy was asserted.
            // This ensures TCM sees the correct address during the write cycle.
            if (par_rdy)
                par_word_addr <= par_word_addr + 10'd1;

            par_rdy       <= 1'b0;
            par_addr_prev <= par_addr;

            if (par_addr_changed) begin
                par_word_addr  <= par_region_base;
                par_nibble_idx <= 3'd0;
            end else if (par_we) begin
                par_word_buf[par_nibble_idx*4 +: 4] <= par_data_in;
                if (par_nibble_idx == 3'd7) begin
                    par_nibble_idx <= 3'd0;
                    par_rdy        <= 1'b1;
                end else begin
                    par_nibble_idx <= par_nibble_idx + 3'd1;
                end
            end else if (par_oe) begin
                if (par_nibble_idx == 3'd7) begin
                    par_nibble_idx <= 3'd0;
                    par_word_addr  <= par_word_addr + 10'd1;
                end else begin
                    par_nibble_idx <= par_nibble_idx + 3'd1;
                end
            end
        end
    end

    // === CPU memory interface ===
    wire [23:0] cpu_mem_addr;
    wire        cpu_mem_read;
    wire        cpu_mem_write;
    wire [1:0]  cpu_mem_size;
    wire [31:0] cpu_mem_wdata;
    wire [31:0] cpu_mem_rdata;
    wire        cpu_mem_ready;

    wire cpu_is_mmio = (cpu_mem_addr[23:22] == 2'b01);
    wire cpu_is_tcm  = ~cpu_is_mmio;
    wire cpu_mmio_wr = cpu_mem_write & cpu_is_mmio;
    wire cpu_mmio_rd = cpu_mem_read  & cpu_is_mmio;
    wire cpu_tcm_en  = (cpu_mem_read | cpu_mem_write) & cpu_is_tcm;

    // === DCIM MMIO bus ===
    wire        dcim_mmio_write;
    wire        dcim_mmio_read;
    wire [5:0]  dcim_mmio_addr;
    wire [31:0] dcim_mmio_wdata;
    wire [31:0] dcim_mmio_rdata;
    wire        dcim_mmio_ready;

    assign dcim_mmio_write = cpu_mmio_wr | (par_is_mmio & par_rdy);
    assign dcim_mmio_read  = cpu_mmio_rd | (par_is_mmio & par_oe);
    assign dcim_mmio_addr  = par_is_mmio ? {2'b0, par_addr, 2'b0} : cpu_mem_addr[5:0];
    assign dcim_mmio_wdata = par_is_mmio ? par_word_buf            : cpu_mem_wdata;

    wire [31:0] tcm_a_dout;

    wire cpu_bus_active = cpu_mem_read | cpu_mem_write;
    assign cpu_mem_ready = cpu_bus_active ? (cpu_is_mmio ? dcim_mmio_ready : 1'b1) : 1'b0;
    assign cpu_mem_rdata = cpu_is_mmio ? dcim_mmio_rdata : tcm_a_dout;

    wire cpu_nrst = nrst & (is_parallel ? par_cpu_nrst : 1'b1);

    // === CPU ===
    wire [2:0]  dbg_cpu_state;
    wire [23:0] dbg_cpu_pc;
    wire [31:0] dbg_cpu_instr;
    wire [31:0] dbg_alu_result;
    wire [3:0]  dbg_dec_alu_opcode;
    wire [2:0]  dbg_dec_mem_opcode;
    wire [3:0]  dbg_dec_rs1;
    wire [3:0]  dbg_dec_rs2;
    wire [3:0]  dbg_dec_rd;
    wire [10:0] dbg_dec_flags;
    wire        dbg_branch_taken;

    tinymoa_cpu cpu (
        .clk                (cpu_clk),
        .nrst               (cpu_nrst),
        .mem_ready          (cpu_mem_ready),
        .mem_addr           (cpu_mem_addr),
        .mem_read           (cpu_mem_read),
        .mem_write          (cpu_mem_write),
        .mem_size           (cpu_mem_size),
        .mem_wdata          (cpu_mem_wdata),
        .mem_rdata          (cpu_mem_rdata),
        .dbg_state          (dbg_cpu_state),
        .dbg_done           (),
        .dbg_pc             (dbg_cpu_pc),
        .dbg_instr          (dbg_cpu_instr),
        .dbg_alu_result     (dbg_alu_result),
        .dbg_dec_alu_opcode (dbg_dec_alu_opcode),
        .dbg_dec_mem_opcode (dbg_dec_mem_opcode),
        .dbg_dec_rs1        (dbg_dec_rs1),
        .dbg_dec_rs2        (dbg_dec_rs2),
        .dbg_dec_rd         (dbg_dec_rd),
        .dbg_dec_flags      (dbg_dec_flags),
        .dbg_branch_taken   (dbg_branch_taken)
    );

    // === DCIM ===
    wire        dcim_mem_read;
    wire        dcim_mem_write;
    wire [9:0]  dcim_mem_addr;
    wire [31:0] dcim_mem_wdata;
    wire [31:0] dcim_mem_rdata;
    wire [2:0]  dbg_dcim_state;

    tinymoa_dcim dcim (
        .clk        (clk),
        .nrst       (nrst),
        .mmio_ready (dcim_mmio_ready),
        .mmio_write (dcim_mmio_write),
        .mmio_wdata (dcim_mmio_wdata),
        .mmio_read  (dcim_mmio_read),
        .mmio_rdata (dcim_mmio_rdata),
        .mmio_addr  (dcim_mmio_addr),
        .mem_rdata  (dcim_mem_rdata),
        .mem_wdata  (dcim_mem_wdata),
        .mem_write  (dcim_mem_write),
        .mem_read   (dcim_mem_read),
        .mem_addr   (dcim_mem_addr),
        .dbg_state  (dbg_dcim_state)
    );

    // === TCM ===
    // Port A: CPU (instruction fetch + data load/store)
    // Port B: DCIM FSM or PAR host (PAR wins only when DCIM is idle)
    wire [31:0] tcm_b_dout;

    wire dcim_b_active = dcim_mem_read | dcim_mem_write;
    wire par_tcm_win   = par_is_tcm & ~dcim_b_active;

    wire        tcm_b_en   = par_tcm_win ? (par_rdy | par_oe) : dcim_b_active;
    wire        tcm_b_wen  = par_tcm_win ? par_rdy             : dcim_mem_write;
    wire [9:0]  tcm_b_addr = par_tcm_win ? par_word_addr       : dcim_mem_addr;
    wire [31:0] tcm_b_din  = par_tcm_win ? par_word_buf        : dcim_mem_wdata;

    assign dcim_mem_rdata = tcm_b_dout;

    tinymoa_tcm tcm (
        .clk    (clk),
        .a_en   (cpu_tcm_en),
        .a_wen  (cpu_mem_write & cpu_is_tcm),
        .a_din  (cpu_mem_wdata),
        .a_dout (tcm_a_dout),
        .a_addr (cpu_mem_addr[9:0]),
        .b_en   (tcm_b_en),
        .b_wen  (tcm_b_wen),
        .b_din  (tcm_b_din),
        .b_dout (tcm_b_dout),
        .b_addr (tcm_b_addr)
    );

    // === Debug frame shift register ===
    localparam DBG_FRAME_W = 144;

    wire [DBG_FRAME_W-1:0] dbg_frame = {
        8'hAA,
        dbg_cpu_state,
        dbg_cpu_pc,
        dbg_cpu_instr,
        dbg_dec_alu_opcode,
        dbg_dec_mem_opcode,
        dbg_dec_rs1,
        dbg_dec_rs2,
        dbg_dec_rd,
        dbg_dec_flags,
        dbg_branch_taken,
        dbg_alu_result,
        dbg_dcim_state,
        par_nibble_idx,
        8'h55
    };

    reg [DBG_FRAME_W-1:0] dbg_shift;
    reg [7:0]             dbg_bit_cnt;
    reg                   dbg_frame_end_r;

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            dbg_shift       <= {DBG_FRAME_W{1'b0}};
            dbg_bit_cnt     <= 8'd0;
            dbg_frame_end_r <= 1'b0;
        end else if (dbg_en) begin
            dbg_frame_end_r <= 1'b0;
            if (dbg_bit_cnt == 8'd0) begin
                dbg_bit_cnt <= 8'd1;
            end else if (dbg_bit_cnt == DBG_FRAME_W) begin
                dbg_shift       <= dbg_frame;
                dbg_bit_cnt     <= 8'd0;
                dbg_frame_end_r <= 1'b1;
            end else begin
                dbg_shift   <= {dbg_shift[DBG_FRAME_W-2:0], 1'b0};
                dbg_bit_cnt <= dbg_bit_cnt + 8'd1;
            end
        end else begin
            dbg_shift       <= dbg_frame;
            dbg_bit_cnt     <= 8'd0;
            dbg_frame_end_r <= 1'b0;
        end
    end

    wire dbg_strobe = dbg_shift[DBG_FRAME_W-1];

    // === PAR read data ===
    wire [31:0] par_read_word   = par_is_mmio ? dcim_mmio_rdata : tcm_b_dout;
    wire [3:0]  par_read_nibble = par_read_word[par_nibble_idx*4 +: 4];

    // === QSPI stubs (M3) ===
    wire qspi_oe    = 1'b0;
    wire qspi_sck   = 1'b0;
    wire cs_flash_n = 1'b1;
    wire cs_ram_a_n = 1'b1;
    wire cs_ram_b_n = 1'b1;
    wire cs_peri_n  = 1'b1;

    // === Outputs ===
    // uo[7:4]: SER = NCS lines, PAR = word address [3:0]
    // uo[3]:   SER = qspi_sck,  PAR = par_rdy
    // uo[2:0]: always dbg/qspi
    assign uo_out = {
        is_parallel ? par_word_addr[3:0]
                    : {cs_peri_n, cs_ram_b_n, cs_ram_a_n, cs_flash_n},
        is_parallel ? par_rdy : qspi_sck,
        qspi_oe,
        dbg_frame_end_r,
        dbg_strobe
    };

    assign uio_io = is_parallel ? {par_read_nibble, 4'b0} : 8'b0;
    assign uio_oe  = is_parallel ? {{4{par_oe}}, 4'b0}     : 8'b0;

    wire _unused = &{cpu_mem_size, ena, 1'b0};

endmodule
