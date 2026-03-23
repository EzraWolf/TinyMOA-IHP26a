# Phase 1 TinyMOA FPGA bring-up build
# Targets: Alchitry Cu V2 (iCE40-HX8K)
# Toolchain: yosys + nextpnr-ice40 + iceprog

OUT = bin

# Source files (all synthesis-safe)
SOURCES = \
	top.v \
	pll.v \
	../src/core.v \
	../src/decoder.v \
	../src/registers.v \
	../src/alu/alu.v \
	../src/alu/shifter.v \
	../src/alu/multiplier.v \
	../src/csr.v \
	instr_loader.v \
	debug_display.v \
	segment_display.v

.PHONY: synth pnr bin flash clean

all: bin

synth: $(OUT)/top.json
pnr: $(OUT)/top.asc
bin: $(OUT)/top.bin

$(OUT)/top.json: $(SOURCES) | $(OUT)
	yosys '-p "synth_ice40 -top top -json $(OUT)/top.json"' $(SOURCES) \
		-L $(OUT)/yosys.log -q

$(OUT)/top.asc: $(OUT)/top.json AlchitryCuV2.pcf | $(OUT)
	nextpnr-ice40 --hx8k --package cb132 --pcf AlchitryCuV2.pcf \
		--json $(OUT)/top.json --asc $@ \
		-l $(OUT)/nextpnr.log -q

$(OUT)/top.bin: $(OUT)/top.asc
	icepack $< $@

flash: $(OUT)/top.bin
	iceprog -X $<

$(OUT):
	mkdir -p $@

clean:
	@rm -rf $(OUT)