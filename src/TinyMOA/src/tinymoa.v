// TinyMOA DCIM Accelerator ASIC

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

    /* Goodbye CPU
    wire [23:0] cpu_mem_addr;
    wire        cpu_mem_read;
    wire        cpu_mem_write;
    wire [1:0]  cpu_mem_size;
    wire [31:0] cpu_mem_wdata;
    wire [31:0] cpu_mem_rdata;
    wire        cpu_mem_ready = 1'b1;

    tinymoa_cpu cpu (
        .clk       (clk),
        .nrst      (nrst),
        .mem_ready (cpu_mem_ready),
        .mem_addr  (cpu_mem_addr),
        .mem_read  (cpu_mem_read),
        .mem_write (cpu_mem_write),
        .mem_size  (cpu_mem_size),
        .mem_wdata (cpu_mem_wdata),
        .mem_rdata (cpu_mem_rdata)
    );
    */

    // Pin mapping
    wire pin_target     = ui_in[0];
    wire pin_rw         = ui_in[1];
    wire pin_addr_load  = ui_in[2];
    wire pin_halt       = ui_in[3]; // gates clock for DCIM + ext_io FSM. debug pins stay readable.
    wire pin_strobe     = ui_in[4];
    wire pin_execute    = ui_in[5];
    wire pin_dbg_strobe = ui_in[6];

    // Halt freezes DCIM and ext_io FSM. Debug pins are combinational and always readable.
    wire clk_gated = clk & ~pin_halt;

    // Edge detection on clk_gated
    reg strobe_prev;
    reg execute_prev;

    wire strobe_rise  = pin_strobe  & ~strobe_prev;
    wire execute_rise = pin_execute & ~execute_prev;

    always @(posedge clk_gated or negedge nrst) begin
        if (!nrst) begin
            strobe_prev  <= 1'b0;
            execute_prev <= 1'b0;
        end else begin
            strobe_prev  <= pin_strobe;
            execute_prev <= pin_execute;
        end
    end

    // Byte accumulator and address register
    reg [31:0] data_reg;
    reg [1:0]  byte_idx;
    reg [15:0] addr_reg;
    reg        addr_byte_idx;

    // Read output
    reg [31:0] read_reg;
    reg [1:0]  read_byte_idx;

    // UIO output
    reg [7:0] uio_out_reg;
    reg       uio_driving;

    assign uio_out = uio_out_reg;
    assign uio_oe  = uio_driving ? 8'hFF : 8'h00;

    // Status
    reg out_ready;
    reg out_word_done;

    // ext_io FSM
    localparam IDLE    = 2'd0;
    localparam EXECUTE = 2'd1;
    localparam WAIT    = 2'd2; // TCM read: one extra cycle for a_dout_r to settle
    localparam LATCH   = 2'd3;

    reg [1:0] ext_state;
    reg       lat_target;
    reg       lat_rw;

    // TCM Port A
    reg         tcm_a_en;
    reg         tcm_a_wen;
    reg  [31:0] tcm_a_din;
    reg  [9:0]  tcm_a_addr;
    wire [31:0] tcm_a_dout;

    // DCIM Port B
    wire [31:0] tcm_b_dout;
    wire [31:0] dcim_mem_wdata;
    wire        dcim_mem_write;
    wire        dcim_mem_read;
    wire [9:0]  dcim_mem_addr;

    // DCIM MMIO
    reg         mmio_write;
    reg         mmio_read;
    reg  [31:0] mmio_wdata;
    reg  [5:0]  mmio_addr;
    wire [31:0] mmio_rdata;
    wire        mmio_ready;

    wire [2:0] dcim_dbg_state;

    always @(posedge clk_gated or negedge nrst) begin
        if (!nrst) begin
            data_reg      <= 32'b0;
            byte_idx      <= 2'b0;
            addr_reg      <= 16'b0;
            addr_byte_idx <= 1'b0;
            read_reg      <= 32'b0;
            read_byte_idx <= 2'b0;
            uio_out_reg   <= 8'b0;
            uio_driving   <= 1'b0;
            out_ready     <= 1'b0;
            out_word_done <= 1'b0;
            tcm_a_en      <= 1'b0;
            tcm_a_wen     <= 1'b0;
            tcm_a_din     <= 32'b0;
            tcm_a_addr    <= 10'b0;
            mmio_write    <= 1'b0;
            mmio_read     <= 1'b0;
            mmio_wdata    <= 32'b0;
            mmio_addr     <= 6'b0;
            ext_state     <= IDLE;
            lat_target    <= 1'b0;
            lat_rw        <= 1'b0;
        end else begin
            out_ready     <= 1'b0;
            out_word_done <= 1'b0;
            tcm_a_en      <= 1'b0;
            tcm_a_wen     <= 1'b0;
            mmio_write    <= 1'b0;
            mmio_read     <= 1'b0;

            // Address loading
            if (strobe_rise && pin_addr_load) begin
                if (!addr_byte_idx)
                    addr_reg[7:0] <= uio_in;
                else
                    addr_reg[15:8] <= uio_in;
                addr_byte_idx <= ~addr_byte_idx;
                out_ready     <= 1'b1;
            end

            // Data byte in/out
            if (strobe_rise && !pin_addr_load) begin
                if (pin_rw) begin
                    case (byte_idx)
                        2'd0: data_reg[7:0]   <= uio_in;
                        2'd1: data_reg[15:8]  <= uio_in;
                        2'd2: data_reg[23:16] <= uio_in;
                        2'd3: data_reg[31:24] <= uio_in;
                    endcase
                    byte_idx  <= byte_idx + 2'd1;
                    out_ready <= 1'b1;
                    if (byte_idx == 2'd3)
                        out_word_done <= 1'b1;
                end else begin
                    uio_driving <= 1'b1;
                    case (read_byte_idx)
                        2'd0: uio_out_reg <= read_reg[7:0];
                        2'd1: uio_out_reg <= read_reg[15:8];
                        2'd2: uio_out_reg <= read_reg[23:16];
                        2'd3: uio_out_reg <= read_reg[31:24];
                    endcase
                    read_byte_idx <= read_byte_idx + 2'd1;
                    out_ready     <= 1'b1;
                    if (read_byte_idx == 2'd3) begin
                        out_word_done <= 1'b1;
                        uio_driving   <= 1'b0;
                    end
                end
            end

            // Transaction FSM
            case (ext_state)
                IDLE: begin
                    if (execute_rise) begin
                        lat_target <= pin_target;
                        lat_rw     <= pin_rw;
                        ext_state  <= EXECUTE;
                    end
                end

                EXECUTE: begin
                    if (!lat_target) begin
                        // TCM access via Port A
                        tcm_a_en   <= 1'b1;
                        tcm_a_addr <= addr_reg[9:0];
                        if (lat_rw) begin
                            tcm_a_wen <= 1'b1;
                            tcm_a_din <= data_reg;
                            ext_state <= LATCH; // write: fire-and-forget
                        end else begin
                            ext_state <= WAIT;  // read: wait for a_dout_r to settle
                        end
                    end else begin
                        // DCIM MMIO access
                        mmio_addr <= addr_reg[5:0];
                        if (lat_rw) begin
                            mmio_write <= 1'b1;
                            mmio_wdata <= data_reg;
                        end else begin
                            mmio_read <= 1'b1;
                        end
                        ext_state <= LATCH;
                    end
                end

                // TCM read only: TCM registered output needs one cycle to settle
                // after a_en is asserted. WAIT provides that cycle before LATCH captures.
                WAIT: begin
                    ext_state <= LATCH;
                end

                LATCH: begin
                    if (!lat_target) begin
                        // TCM: data is stable
                        if (!lat_rw) begin
                            read_reg      <= tcm_a_dout;
                            read_byte_idx <= 2'b0;
                        end
                        addr_reg  <= addr_reg + 16'd1;
                        byte_idx  <= 2'b0;
                        out_ready <= 1'b1;
                        ext_state <= IDLE;
                    end else begin
                        // MMIO: poll until DCIM acknowledges
                        if (mmio_ready) begin
                            if (!lat_rw) begin
                                read_reg      <= mmio_rdata;
                                read_byte_idx <= 2'b0;
                            end
                            addr_reg  <= addr_reg + 16'd1;
                            byte_idx  <= 2'b0;
                            out_ready <= 1'b1;
                            ext_state <= IDLE;
                        end
                    end
                end
            endcase
        end
    end

    // TCM: Port A = ext IO, Port B = DCIM. Runs on ungated clk.
    tinymoa_tcm tcm (
        .clk    (clk),
        .a_en   (tcm_a_en),
        .a_wen  (tcm_a_wen),
        .a_din  (tcm_a_din),
        .a_dout (tcm_a_dout),
        .a_addr (tcm_a_addr),
        .b_en   (dcim_mem_read | dcim_mem_write),
        .b_wen  (dcim_mem_write),
        .b_din  (dcim_mem_wdata),
        .b_dout (tcm_b_dout),
        .b_addr (dcim_mem_addr)
    );

    // DCIM: runs on gated clock (halted by pin_halt)
    tinymoa_dcim dcim (
        .clk        (clk_gated),
        .nrst       (nrst),
        .mmio_ready (mmio_ready),
        .mmio_write (mmio_write),
        .mmio_wdata (mmio_wdata),
        .mmio_read  (mmio_read),
        .mmio_rdata (mmio_rdata),
        .mmio_addr  (mmio_addr),
        .mem_rdata  (tcm_b_dout),
        .mem_wdata  (dcim_mem_wdata),
        .mem_write  (dcim_mem_write),
        .mem_read   (dcim_mem_read),
        .mem_addr   (dcim_mem_addr),
        .dbg_state  (dcim_dbg_state)
    );

    // Output pins
    assign uo_out[0]   = 1'b0;
    assign uo_out[1]   = out_ready;
    assign uo_out[2]   = out_word_done;
    assign uo_out[5:3] = dcim_dbg_state;
    assign uo_out[6]   = (dcim_dbg_state != 3'd0);
    assign uo_out[7]   = (dcim_dbg_state == 3'd5);

    wire _unused = &{ui_in[7], pin_dbg_strobe, 1'b0};

endmodule
