
// IHP SG13G2 512x32 SRAM macro wrapper with BIST
// Functional: behavioral model with BIST for simulation
// Synthesis: macro stub
module RM_IHPSG13_1P_512x32_c2_bm_bist (
    input A_CLK,
    input A_MEN,
    input A_WEN,
    input A_REN,
    input [8:0] A_ADDR,
    input [31:0] A_DIN,
    input A_DLY,
    output [31:0] A_DOUT,
    input [31:0] A_BM,
    input A_BIST_CLK,
    input A_BIST_EN,
    input A_BIST_MEN,
    input A_BIST_WEN,
    input A_BIST_REN,
    input [8:0] A_BIST_ADDR,
    input [31:0] A_BIST_DIN,
    input [31:0] A_BIST_BM
);

`ifdef FUNCTIONAL
    // Behavioral SRAM with BIST for simulation
    reg [31:0] memory [0:511];
    reg [31:0] dr_r;

    wire [8:0] ADDR_MUX = (A_BIST_EN) ? A_BIST_ADDR : A_ADDR;
    wire [31:0] DIN_MUX = (A_BIST_EN) ? A_BIST_DIN : A_DIN;
    wire [31:0] BM_MUX = (A_BIST_EN) ? A_BIST_BM : A_BM;
    wire MEN_MUX = (A_BIST_EN) ? A_BIST_MEN : A_MEN;
    wire WEN_MUX = (A_BIST_EN) ? A_BIST_WEN : A_WEN;
    wire REN_MUX = (A_BIST_EN) ? A_BIST_REN : A_REN;
    wire CLK_MUX = (A_BIST_EN) ? A_BIST_CLK : A_CLK;

    always @(posedge CLK_MUX) begin
        if (MEN_MUX && WEN_MUX) begin
            memory[ADDR_MUX] <= (memory[ADDR_MUX] & ~BM_MUX) | (DIN_MUX & BM_MUX);
            if (REN_MUX) begin
                dr_r <= (memory[ADDR_MUX] & ~BM_MUX) | (DIN_MUX & BM_MUX);
            end
        end else if (MEN_MUX && REN_MUX) begin
            dr_r <= memory[ADDR_MUX];
        end
    end

    assign A_DOUT = dr_r;

`else
    // Macro stub for synthesis
`endif
endmodule
