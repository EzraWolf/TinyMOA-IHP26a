// TinyMOA Register File
//
// 14 storage registers (x0 hardwired 0, gp/tp pseudo-hardcoded via combinational logic).
// Each register is a 32-bit rotating shift register. Every clock cycle, 4 bits rotate
// out for read, and 4 bits can be written in. Read is one nibble ahead of write.
//
// gp (x3) = 0x000400 — TCM globals midpoint, generated combinationally per nibble.
// tp (x4) = 0x400000 — DCIM MMIO base, generated combinationally per nibble.
//
// IHP SG13G2: no output buffer needed (direct assign). On Sky130A, use buffered output.
//
// Credit:
// https://github.com/MichaelBell/tinyQV/blob/858986b72975157ebf27042779b6caaed164c57b/cpu/register.v

`default_nettype none
`timescale 1ns / 1ps

module tinymoa_registers (
    input clk,
    input nrst,

    input  [2:0] nibble_ct,

    input  [3:0] rs1_sel,
    output [3:0] rs1_nibble,

    input  [3:0] rs2_sel,
    output [3:0] rs2_nibble,

    input        rd_wen,
    input  [3:0] rd_sel,
    input  [3:0] rd_nibble
);
    wire [3:0] reg_nibble [0:15];
    assign reg_nibble[0] = 4'h0; // x0 = always zero.

    // x3 (gp): pseudo-hardcoded 0x000400
    // Nibble breakdown: nibble 0=0x0, 1=0x0, 2=0x4, 3=0x0, 4=0x0, 5=0x0
    assign reg_nibble[3] = (nibble_ct == 3'd2) ? 4'h4 : 4'h0;

    // x4 (tp): pseudo-hardcoded 0x400000
    // Nibble breakdown: nibble 0=0x0, 1=0x0, 2=0x0, 3=0x0, 4=0x0, 5=0x4
    assign reg_nibble[4] = (nibble_ct == 3'd5) ? 4'h4 : 4'h0;

    genvar i;
    generate
        for (i = 1; i < 16; i = i + 1) begin : gen_reg
            if (i != 3 && i != 4) begin : gen_storage
                reg [31:0] register;

                // Rotate: bottom nibble shifts out, top nibble shifts down
                // Write: if selected, inject rd_nibble instead of rotating
                always @(posedge clk) begin
                    if (!nrst) begin
                        register <= 32'd0;
                    end else if (rd_wen && rd_sel == i) begin
                        register <= {register[3:0], register[31:8], rd_nibble};
                    end else begin
                        register <= {register[3:0], register[31:8], register[7:4]};
                    end
                end
                
                assign reg_nibble[i] = register[7:4]; // Output the nibble currently rotated to the pos
            end
        end
    endgenerate

    assign rs1_nibble = reg_nibble[rs1_sel];
    assign rs2_nibble = reg_nibble[rs2_sel];

endmodule
