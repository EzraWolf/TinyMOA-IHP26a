// Boot FSM copies flash to TCM on reset, then releases CPU.
// CPU (cpu_nrst) is held in reset until boot_done goes high.
// We use Port A of TCM.
// No watchdog - if QSPI stalls, CPU stays in reset.

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_bootloader (
    input clk,
    input nrst,

    output reg boot_done,

    input             rom_ready,
    output reg        rom_read,
    input      [31:0] rom_rdata,
    output reg [23:0] rom_addr,

    output reg        tcm_wen,
    output reg [31:0] tcm_din,
    output reg [9:0]  tcm_addr
);

    // Flash image starts at 0x001000 (word-aligned, after SRAM address space).
    // Copy 512 words (2 KB) for 512x32 SRAM, or 1024 words for 1024x32.
    localparam FLASH_BASE  = 24'h001000;
    localparam WORD_COUNT  = 10'd512;

    localparam IDLE        = 2'd0;
    localparam FETCH       = 2'd1;
    localparam WRITE_TCM   = 2'd2;
    localparam DONE        = 2'd3;

    reg [1:0] state;
    reg [9:0] word_idx;

    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            state     <= IDLE;
            boot_done <= 1'b0;
            word_idx  <= 10'd0;
            rom_addr  <= FLASH_BASE;
            rom_read  <= 1'b0;
            tcm_addr  <= 10'd0;
            tcm_din  <= 32'd0;
            tcm_wen   <= 1'b0;
        end else begin
            rom_read  <= 1'b0;
            tcm_wen   <= 1'b0;

            case (state)
                IDLE: begin
                    state <= FETCH; // Start immediately on reset
                end

                FETCH: begin
                    // Assert QSPI read for current word. Wait for rom_ready.
                    // rom_addr = FLASH_BASE + (word_idx << 2)
                    rom_addr <= FLASH_BASE + {word_idx, 2'b00};
                    rom_read <= 1'b1;
                    if (rom_ready) begin
                        tcm_din <= rom_rdata;
                        tcm_addr  <= word_idx;
                        rom_read <= 1'b0;
                        state      <= WRITE_TCM;
                    end
                end

                WRITE_TCM: begin
                    tcm_wen <= 1'b1;
                    if (word_idx == WORD_COUNT - 1)
                        state <= DONE;
                    else begin
                        word_idx <= word_idx + 10'd1;
                        state    <= FETCH;
                    end
                end

                DONE: begin
                    boot_done <= 1'b1;
                end
            endcase
        end
    end

endmodule
