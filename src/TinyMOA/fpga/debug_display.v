`default_nettype none
`timescale 1ns / 1ps

// Debug display controller for 4× 7-segment display
// Selects display mode based on button inputs
// Latches all debug values when CPU reaches S_WRITEBACK
module debug_display (
    input wire        clk,
    input wire        nrst,

    input wire [2:0]  dbg_state,
    input wire [23:0] dbg_pc,
    input wire [3:0]  dbg_alu_a,
    input wire [3:0]  dbg_alu_b,
    input wire [3:0]  dbg_alu_result,
    input wire        dbg_alu_carry,
    input wire [2:0]  dbg_nibble_cnt,

    input wire btn_a,
    input wire btn_b,
    input wire btn_d,

    output wire [6:0] seg_a,
    output wire [6:0] seg_b,
    output wire [6:0] seg_c,
    output wire [6:0] seg_d
);
    localparam S_WRITEBACK = 3'd3;

    // Latch debug values when entering S_WRITEBACK
    reg [23:0] latched_pc;
    reg [3:0]  latched_alu_result;
    reg [3:0]  latched_alu_a;
    reg [3:0]  latched_alu_b;
    reg        latched_alu_carry;
    reg [2:0]  latched_nibble_cnt;
    reg [2:0]  latched_state;
    reg        prev_in_writeback;

    always @(posedge clk) begin
        if (!nrst) begin
            prev_in_writeback <= 1'b0;
            latched_pc <= 24'd0;
            latched_alu_result <= 4'd0;
            latched_alu_a <= 4'd0;
            latched_alu_b <= 4'd0;
            latched_alu_carry <= 1'b0;
            latched_nibble_cnt <= 3'd0;
            latched_state <= 3'd0;
        end else begin
            prev_in_writeback <= (dbg_state == S_WRITEBACK);

            // Latch on transition TO S_WRITEBACK
            if ((dbg_state == S_WRITEBACK) && !prev_in_writeback) begin
                latched_pc <= dbg_pc;
                latched_alu_result <= dbg_alu_result;
                latched_alu_a <= dbg_alu_a;
                latched_alu_b <= dbg_alu_b;
                latched_alu_carry <= dbg_alu_carry;
                latched_nibble_cnt <= dbg_nibble_cnt;
                latched_state <= dbg_state;
            end
        end
    end

    // Decode which display mode based on buttons
    // Button A: PC display
    // Button B: ALU signals
    // Button D: Pipeline state
    // Default: PC display
    reg [6:0] seg_mux_a, seg_mux_b, seg_mux_c, seg_mux_d;

    always @(*) begin
        if (btn_a) begin
            // Button A: PC[7:4] on seg_c, PC[3:0] on seg_b, {1'b0, nibble_cnt} on seg_a, blank seg_d
            seg_mux_d = 7'b0000000;
            seg_mux_c = 7'b0000000;  // Will fill with seg7 decoder
            seg_mux_b = 7'b0000000;  // Will fill with seg7 decoder
            seg_mux_a = 7'b0000000;  // Will fill with seg7 decoder
        end else if (btn_b) begin
            // Button B: ALU debug
            // seg_d = {3'b0, alu_carry}, seg_c = alu_result, seg_b = alu_a, seg_a = alu_b
            seg_mux_d = 7'b0000000;  // Will fill
            seg_mux_c = 7'b0000000;  // Will fill
            seg_mux_b = 7'b0000000;  // Will fill
            seg_mux_a = 7'b0000000;  // Will fill
        end else if (btn_d) begin
            // Button D: Pipeline state on seg_a, others blank
            seg_mux_d = 7'b0000000;
            seg_mux_c = 7'b0000000;
            seg_mux_b = 7'b0000000;
            seg_mux_a = 7'b0000000;  // Will fill with state
        end else begin
            // Default: PC display across all 4 digits
            seg_mux_d = 7'b0000000;  // Will fill with PC[15:12]
            seg_mux_c = 7'b0000000;  // Will fill with PC[11:8]
            seg_mux_b = 7'b0000000;  // Will fill with PC[7:4]
            seg_mux_a = 7'b0000000;  // Will fill with PC[3:0]
        end
    end

    wire [3:0] hex_a, hex_b, hex_c, hex_d;
    always @(*) begin
        if (btn_a) begin
            hex_d = 4'd0;  // Blank
            hex_c = latched_pc[7:4];
            hex_b = latched_pc[3:0];
            hex_a = {1'b0, latched_nibble_cnt[2:0]};
        end else if (btn_b) begin
            hex_d = {3'd0, latched_alu_carry};
            hex_c = latched_alu_result;
            hex_b = latched_alu_a;
            hex_a = latched_alu_b;
        end else if (btn_d) begin
            hex_d = 4'd0;  // Blank
            hex_c = 4'd0;  // Blank
            hex_b = 4'd0;  // Blank
            hex_a = {1'b0, latched_state[2:0]};
        end else begin
            // Default: PC across all 4 digits
            hex_d = latched_pc[15:12];
            hex_c = latched_pc[11:8];
            hex_b = latched_pc[7:4];
            hex_a = latched_pc[3:0];
        end
    end

    segment_display seg_a(.hex(hex_a), .seg(seg_a));
    segment_display seg_b(.hex(hex_b), .seg(seg_b));
    segment_display seg_c(.hex(hex_c), .seg(seg_c));
    segment_display seg_d(.hex(hex_d), .seg(seg_d));
endmodule
