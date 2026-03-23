`default_nettype none
`timescale 1ns / 1ps

// Instruction loader for Phase 1 FPGA bring-up
// Accumulates 8 nibbles from DIP switch (sw[3:0]) on button E presses.
// After 8 nibbles, asserts mem_ready for one cycle with full instruction.
module instr_loader (
    input wire        clk,
    input wire        nrst,

    input wire        mem_read,
    output wire       mem_ready,
    output wire [31:0] mem_rdata,

    input wire [3:0] sw,
    input wire       btn_e
);

    localparam STATE_IDLE    = 2'd0;
    localparam STATE_LOADING = 2'd1;
    localparam STATE_READY   = 2'd2;

    reg [1:0] state;
    reg [2:0] nibble_idx;
    reg [31:0] instr_accum;

    // Button E debounce filter (~5ms at 50 MHz)
    reg [18:0] btn_e_filter;
    wire btn_e_debounced = &btn_e_filter;
    reg btn_e_prev;
    wire btn_e_press = btn_e_debounced && !btn_e_prev;

    always @(posedge clk) begin
        if (!nrst) begin
            btn_e_filter <= 19'b0;
            btn_e_prev <= 1'b0;
        end else begin
            btn_e_filter <= {btn_e_filter[17:0], btn_e};
            btn_e_prev <= btn_e_debounced;
        end
    end

    assign mem_rdata = instr_accum;
    assign mem_ready = (state == STATE_READY) && mem_read;

    always @(posedge clk) begin
        if (!nrst) begin
            state <= STATE_IDLE;
            nibble_idx <= 3'd0;
            instr_accum <= 32'd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    if (mem_read) begin
                        state <= STATE_LOADING;
                        nibble_idx <= 3'd0;
                        instr_accum <= 32'd0;
                    end
                end

                STATE_LOADING: begin
                    if (btn_e_press) begin
                        // Latch sw[3:0] into instr_accum[nibble_idx*4 +: 4]
                        instr_accum[{nibble_idx, 2'b00} +: 4] <= sw;
                        if (nibble_idx == 3'd7) begin
                            state <= STATE_READY;
                        end else begin
                            nibble_idx <= nibble_idx + 3'd1;
                        end
                    end
                end

                STATE_READY: begin
                    if (mem_read) begin
                        // Hold ready for one cycle
                        state <= STATE_IDLE;
                    end
                end
            endcase
        end
    end
endmodule
