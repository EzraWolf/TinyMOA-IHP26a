// TinyMOA 32x32 DCIM CORE
// Based on "DIMC-D" (double-approximate) from ISSCC 2022 (see below).
//
// Weights stored as 1024 FFs (32 cols x 32 bits), cached from TCM.
// Activations streamted from TCM Port B
// LOAD_WEIGHTS reads each row, distributes 1 bit to each col reg

//
// Reference: ISSCC 2022, Wang et al.
// "DIMC: 2219TOPS/W 2569F2/b Digital In-Memory Computing Macro in 28nm Based on Approximate Arithmetic Hardware"





// Activations read from TCM Port B bit-serially (1 bit-plane per COMPUTE cycle).
// Results written back to TCM Port B with hardware signed conversion.
// All digital, no ADC, no custom-drawn cells, standard cells only.
//
// Weight loading (LOAD_WEIGHTS state):
//   TCM stores weights row-major: one 32-bit word per row, bit[col] = W[row][col].
//   LOAD_WEIGHTS reads each row and distributes one bit to each column register
//   simultaneously -- a runtime transpose (no CPU software needed).
//   weight_reg[col] is a 32-bit shift register; after loading,
//   weight_reg[col][row] = W[row][col].
//
// Pipelined LOAD_WEIGHTS:
//   The FSM asserts mem_read for row N+1 in the same cycle it latches row N.
//   Total cost: cfg_array_size + 1 cycles (vs. 2*cfg_array_size without pipeline).
//
// Signed conversion (STORE_RESULT state):
//   Raw accumulator holds sum of XNOR popcounts weighted by bit-plane position.
//   Hardware converts to signed dot product: mem_wdata = 2*shift_acc[col] - bias
//   where bias = cfg_array_size * (2^cfg_precision - 1).
//   bias is computed once in IDLE, stored in `bias_reg`.
//   Saves the CPU a 32-iteration loop after every inference.
//
// Compressor:
//   Two tinymoa_compressor instances per column cover bits [15:0] and [31:16].
//   Compressor mode is selected at elaboration time via `define flags:
//     EXACT_COMPRESSOR, SINGLE_APPROX_COMPRESSOR, or double-approx (default).

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_dcim #(
    parameter ARRAY_DIM = 16, // NxN array
    parameter ACC_WIDTH = 9   // max value = N*(2^P-1)
)(
    input clk,
    input nrst,

    output reg        mmio_ready,
    input             mmio_write,
    input      [31:0] mmio_wdata,
    input             mmio_read,
    output reg [31:0] mmio_rdata,
    input      [5:0]  mmio_addr,

    // TCM Port B only
    input      [31:0] mem_rdata,
    output reg [31:0] mem_wdata,
    output reg        mem_write,
    output reg        mem_read,
    output reg [9:0]  mem_addr,

    // Debug
    output [2:0] dbg_state
);

    // MMIO config registers
    reg        cfg_start;
    reg        cfg_reload_weights;
    reg [2:0]  cfg_precision;    // bit-planes per activation: 1, 2, or 4
    reg [9:0]  cfg_weight_base;  // TCM word address of weight row 0  (default 0x180)
    reg [9:0]  cfg_act_base;     // TCM word address of activation word 0 (default 0x1A0)
    reg [9:0]  cfg_result_base;  // TCM word address for result writeback  (default 0x1B0)
    reg [5:0]  cfg_array_size;   // active rows/cols (default ARRAY_DIM, max 64)

    reg [1:0]  status_reg;       // bit 0 = BUSY, bit 1 = DONE

    // Weight cache and accumulators
    // weight_reg[col][row] = W[row][col]  after LOAD_WEIGHTS
    reg [ARRAY_DIM-1:0] weight_reg [0:ARRAY_DIM-1];
    reg [ACC_WIDTH-1:0] shift_acc  [0:ARRAY_DIM-1];

    // Current activation bit-plane (1 bit per row)
    reg [ARRAY_DIM-1:0] act_slice;

    // Signed-conversion bias: bias = cfg_array_size * (2^cfg_precision - 1)
    // Computed once in IDLE when cfg_start fires.
    // Max value: 32 * 15 = 480 fits in 9 bits; use 16 for safety.
    reg [15:0] bias_reg;

    // XNOR + compressor wiring (combinational)
    // One tinymoa_compressor per column (16 rows).
    // popcount[col] range 0-16, 5 bits.
    wire [4:0] comp_out [0:ARRAY_DIM-1];
    wire [5:0] popcount [0:ARRAY_DIM-1];

    genvar col;
    generate
        for (col = 0; col < ARRAY_DIM; col = col + 1) begin : gen_col
            wire [ARRAY_DIM-1:0] xnor_bits = ~(weight_reg[col] ^ act_slice);

            tinymoa_compressor comp (
                .in  (xnor_bits),
                .out (comp_out[col])
            );

            assign popcount[col] = {1'b0, comp_out[col]};
        end
    endgenerate

    // === FSM state encoding ===
    localparam IDLE         = 3'd0;
    localparam LOAD_WEIGHTS = 3'd1;
    localparam FETCH_ACT    = 3'd2;
    localparam COMPUTE      = 3'd3;
    localparam STORE_RESULT = 3'd4;
    localparam DONE         = 3'd5;

    reg [2:0] state;

    assign dbg_state = state;

    reg [5:0] row_idx;    // dual-use as row counter in LOAD_WEIGHTS and STORE_RESULT
    reg [2:0] bit_plane;  // current bit-plane index (counts down from cfg_precision-1 to 0)
    reg [1:0] fetch_wait; // wait counter for FETCH_ACT (registered TCM needs 2 cycles)

    // === MMIO block. Runs independently of FSM, always live for CPU polling ===
    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            cfg_start          <= 1'b0;
            cfg_reload_weights <= 1'b1;
            cfg_precision      <= 3'd1;
            cfg_weight_base    <= 10'h180;
            cfg_act_base       <= 10'h1A0;
            cfg_result_base    <= 10'h1B0;
            cfg_array_size     <= ARRAY_DIM[5:0];
            mmio_ready         <= 1'b0;
            mmio_rdata         <= 32'd0;
        end else begin
            mmio_ready <= 1'b0;

            if (mmio_write) begin
                mmio_ready <= 1'b1;
                case (mmio_addr[5:2])
                    4'd0: {cfg_reload_weights, cfg_precision, cfg_start} <= mmio_wdata[4:0];
                    4'd2: cfg_weight_base <= mmio_wdata[9:0];
                    4'd3: cfg_act_base    <= mmio_wdata[9:0];
                    4'd4: cfg_result_base <= mmio_wdata[9:0];
                    4'd5: cfg_array_size  <= mmio_wdata[5:0];
                    default: ;
                endcase
            end

            if (mmio_read) begin
                mmio_ready <= 1'b1;
                case (mmio_addr[5:2])
                    4'd0: mmio_rdata <= {27'd0, cfg_reload_weights, cfg_precision, cfg_start};
                    4'd1: mmio_rdata <= status_reg;
                    4'd2: mmio_rdata <= {22'd0, cfg_weight_base};
                    4'd3: mmio_rdata <= {22'd0, cfg_act_base};
                    4'd4: mmio_rdata <= {22'd0, cfg_result_base};
                    4'd5: mmio_rdata <= {26'd0, cfg_array_size};
                    default: mmio_rdata <= 32'd0;
                endcase
            end

            // cfg_start self-clears once FSM leaves IDLE (CPU need not clear it)
            if (state != IDLE) cfg_start <= 1'b0;
        end
    end

    // Signed conversion for STORE_RESULT
    // store_signed = 2*shift_acc[row_idx] - bias_reg
    // 17 bits: covers full range (-480 to +960) with sign at [16].
    // {2'b0, shift_acc, 1'b0} is 14-bit; Verilog promotes to 17 for subtraction.
    // {1'b0, bias_reg} is 17-bit; no truncation.
    wire signed [16:0] store_signed =
        {2'b0, shift_acc[row_idx], 1'b0} - {1'b0, bias_reg};
    wire [31:0] store_word =
        {{15{store_signed[16]}}, store_signed};

    // === FSM block ===
    integer i;
    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            state      <= IDLE;
            status_reg <= 2'b0;
            row_idx    <= 6'b0;
            bit_plane  <= 3'b0;
            bias_reg   <= 16'b0;
            fetch_wait <= 2'b0;
            mem_write   <= 1'b0;
            mem_read   <= 1'b0;
            mem_addr  <= 10'b0;
            mem_wdata <= 32'b0;
            act_slice  <= {ARRAY_DIM{1'b0}};
            for (i = 0; i < ARRAY_DIM; i = i + 1) begin
                weight_reg[i] <= {ARRAY_DIM{1'b0}};
                shift_acc[i]  <= {ACC_WIDTH{1'b0}};
            end
        end else begin
            mem_write <= 1'b0;
            mem_read <= 1'b0;

            case (state)
                IDLE: begin
                    if (cfg_start) begin
                        status_reg <= 2'b01; // BUSY

                        // Clear accumulators
                        for (i = 0; i < ARRAY_DIM; i = i + 1)
                            shift_acc[i] <= {ACC_WIDTH{1'b0}};

                        // Precompute bias = cfg_array_size * (2^cfg_precision - 1)
                        // cfg_precision is 3 bits (values 1/2/4), so (1<<P)-1 is small.
                        bias_reg <= cfg_array_size * ((16'd1 << cfg_precision) - 16'd1);

                        // Start with MSB bit-plane
                        bit_plane <= cfg_precision - 3'd1;
                        row_idx   <= 6'd0;

                        state <= cfg_reload_weights ? LOAD_WEIGHTS : FETCH_ACT;
                    end
                end


                // LOAD_WEIGHTS — pipelined for registered TCM (1-cycle read latency).
                //
                // Cycle 0 (row_idx=0): issue read row 0. No latch.
                // Cycle 1 (row_idx=1): issue read row 1. TCM registering row 0. No latch.
                // Cycle 2 (row_idx=2): issue read row 2. Latch row 0 from mem_rdata.
                // ...
                // Cycle N   (row_idx=N):   no more reads. Latch row N-2.
                // Cycle N+1 (row_idx=N+1): latch row N-1 (final). -> FETCH_ACT.
                //
                // Total: cfg_array_size + 2 cycles.
                LOAD_WEIGHTS: begin
                    // Latch: mem_rdata is valid 2 cycles after read was issued
                    if (row_idx > 6'd1) begin
                        for (i = 0; i < ARRAY_DIM; i = i + 1)
                            weight_reg[i][row_idx - 6'd2] <= mem_rdata[i];
                    end

                    if (row_idx < cfg_array_size) begin
                        // Issue next read (pipelined: overlaps with latch above)
                        mem_read  <= 1'b1;
                        mem_addr <= cfg_weight_base + {4'd0, row_idx};
                        row_idx   <= row_idx + 6'd1;
                    end else if (row_idx == cfg_array_size) begin
                        // One extra cycle: latch the second-to-last row
                        row_idx <= row_idx + 6'd1;
                    end else begin
                        // All rows latched, begin activation fetch
                        row_idx <= 6'd0;
                        state   <= FETCH_ACT;
                    end
                end


                // FETCH_ACT: issue one TCM read for the current bit-plane.
                // bit_plane counts MSB-first (cfg_precision-1 down to 0).
                // Registered TCM: data valid 2 cycles after read issued.
                // Cycle 0 (fetch_wait=0): issue read.
                // Cycle 1 (fetch_wait=1): TCM registering. Wait.
                // Cycle 2 (fetch_wait=2): mem_rdata valid. Latch act_slice.
                FETCH_ACT: begin
                    case (fetch_wait)
                        2'd0: begin
                            mem_read   <= 1'b1;
                            mem_addr  <= cfg_act_base + {7'd0, bit_plane};
                            fetch_wait <= 2'd1;
                        end
                        2'd1: begin
                            fetch_wait <= 2'd2;
                        end
                        2'd2: begin
                            fetch_wait <= 2'd0;
                            act_slice  <= mem_rdata[ARRAY_DIM-1:0];
                            state      <= COMPUTE;
                        end
                        default: fetch_wait <= 2'd0;
                    endcase
                end


                // COMPUTE: shift-accumulate one bit-plane across all columns.
                // XNOR outputs are combinational (gen_col block above).
                // shift_acc[col] = (shift_acc[col] << 1) + popcount[col]
                // Counts down bit_plane; loops to FETCH_ACT or exits to STORE_RESULT.
                COMPUTE: begin
                    for (i = 0; i < ARRAY_DIM; i = i + 1)
                        shift_acc[i] <= (shift_acc[i] << 1) + {{(ACC_WIDTH-6){1'b0}}, popcount[i]};

                    if (bit_plane > 3'd0) begin
                        bit_plane <= bit_plane - 3'd1;
                        state     <= FETCH_ACT;
                    end else begin
                        row_idx <= 6'd0;
                        state   <= STORE_RESULT;
                    end
                end


                // STORE_RESULT: write signed results to TCM, one column per cycle.
                //
                // Signed conversion: mem_wdata = 2*shift_acc[col] - bias_reg
                //   Maps raw unsigned accumulator to true signed dot product.
                //   The subtraction is done combinationally; result is sign-extended.
                //
                // row_idx doubles as the column counter here.
                STORE_RESULT: begin
                    if (row_idx < cfg_array_size) begin
                        // Signed conversion: 2*shift_acc[col] - bias_reg
                        // store_signed and store_word are wired combinationally above.
                        mem_wdata <= store_word;
                        mem_addr  <= cfg_result_base + {4'd0, row_idx};
                        mem_write   <= 1'b1;
                        row_idx    <= row_idx + 6'd1;
                    end else begin
                        state <= DONE;
                    end
                end


                DONE: begin
                    status_reg <= 2'b10; // DONE (clears BUSY)
                    state      <= IDLE;
                end


                default: state <= IDLE;
            endcase
        end
    end
endmodule
