// CPU core testbench with behavioral memory.
//
// Word-addressed: 1 address = 1 word (32 bits).
// mem[0:2047] = 2048 words of storage.
//
// TCM region:  addr < 256  -> combinational ready (same-cycle)
// QSPI region: addr >= 256 -> ready after LATENCY cycles
//
// TCM ready/rdata are driven by a combinational always block
// so the CPU sees them within the same clock edge. No race.
// Writes are clocked (posedge).

`default_nettype none
`timescale 1ns / 1ps

module tb_cpu (
    input clk,
    input nrst
);
    `ifdef COCOTB_SIM
    initial begin
        $dumpfile("tb_cpu.fst");
        $dumpvars(0, tb_cpu);
        #1;
    end
    `endif

    localparam LATENCY = 12;

    reg  [31:0] mem [0:2047];
    wire [23:0] cpu_mem_addr;
    wire        cpu_mem_read;
    wire        cpu_mem_write;
    wire [31:0] cpu_mem_wdata;
    wire [1:0]  cpu_mem_size;
    reg  [31:0] cpu_mem_rdata;
    reg         cpu_mem_ready;

    reg [3:0]  qspi_delay;
    reg        qspi_ready;
    reg [31:0] qspi_rdata;

    wire [2:0]  dbg_state;
    wire        dbg_done;
    wire [23:0] dbg_pc;
    wire [31:0] dbg_instr;
    wire [31:0] dbg_alu_result;

    // Combinational TCM (ready + rdata) to prevent races
    wire tcm_hit = (cpu_mem_addr < 24'd256);
    wire bus_active = cpu_mem_read || cpu_mem_write;

    always @(*) begin
        if (bus_active && tcm_hit) begin
            cpu_mem_ready = 1'b1;
            cpu_mem_rdata = cpu_mem_read ? mem[cpu_mem_addr] : 32'b0;
        end else if (bus_active && !tcm_hit) begin
            cpu_mem_ready = qspi_ready;
            cpu_mem_rdata = qspi_rdata;
        end else begin
            cpu_mem_ready = 1'b0;
            cpu_mem_rdata = 32'b0;
        end
    end

    // Clocked TCM writes + simulated QSPI delay
    always @(posedge clk or negedge nrst) begin
        if (!nrst) begin
            qspi_delay <= 4'd0;
            qspi_ready <= 1'b0;
            qspi_rdata <= 32'b0;
        end else begin
            qspi_ready <= 1'b0;
            qspi_rdata <= 32'b0;

            // TCM write (clocked)
            if (bus_active && tcm_hit && cpu_mem_write)
                mem[cpu_mem_addr] <= cpu_mem_wdata;

            // QSPI delay logic
            if (bus_active && !tcm_hit) begin
                if (qspi_delay == LATENCY - 1) begin
                    qspi_ready <= 1'b1;
                    qspi_delay   <= 4'd0;
                    if (cpu_mem_read)
                        qspi_rdata <= mem[cpu_mem_addr];
                    if (cpu_mem_write)
                        mem[cpu_mem_addr] <= cpu_mem_wdata;
                end else begin
                    qspi_delay <= qspi_delay + 4'd1;
                end
            end else begin
                qspi_delay <= 4'd0;
            end
        end
    end

    tinymoa_cpu cpu (
        .clk       (clk),
        .nrst      (nrst),
        .mem_addr  (cpu_mem_addr),
        .mem_read  (cpu_mem_read),
        .mem_write (cpu_mem_write),
        .mem_wdata (cpu_mem_wdata),
        .mem_size  (cpu_mem_size),
        .mem_rdata (cpu_mem_rdata),
        .mem_ready (cpu_mem_ready),
        .dbg_state          (dbg_state),
        .dbg_done           (dbg_done),
        .dbg_pc             (dbg_pc),
        .dbg_instr          (dbg_instr),
        .dbg_alu_result     (dbg_alu_result),
        .dbg_dec_alu_opcode (),
        .dbg_dec_mem_opcode (),
        .dbg_dec_rs1        (),
        .dbg_dec_rs2        (),
        .dbg_dec_rd         (),
        .dbg_dec_flags      (),
        .dbg_branch_taken   ()
    );
endmodule
