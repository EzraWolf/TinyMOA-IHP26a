# Macros

## Scratchpad internal SRAM

IHP SG13G2 pre-generated 512x32 SRAM macro (`RM_IHPSG13_1P_512x32_c2_bm_bist`).

Setup is based on [Urish's SRAM test](https://github.com/urish/ttihp-sram-test/tree/main) - all credit goes to Urish.

Pre-generated IHP SRAM macros are found [here](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/main/ihp-sg13g2/libs.ref/sg13g2_sram).

When changing the folder structure here or at `src/memory/sram.v`, you must carefully update the [TinyMOA-IHP26a config.json](https://github.com/EzraWolf/TinyMOA-IHP26a/blob/main/src/config.json)

The PDN config (`pdn_cfg.tcl`)  is from [here](https://github.com/urish/ttihp-sram-test/blob/main/src/pdn_cfg.tcl). This *should* work with all IHP pre-generated SRAM macros, but has ONLY been verified with [his project](https://github.com/urish/ttihp-sram-test/tree/main). This file must be included in `src/pdn_cfg.tcl` for any TinyTapeout implementation repo which is why here, inside of `src/` we do not see it since this is NOT a TinyTapeout repo.

Due to an [issue](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/615) specifically with `RM_IHPSG13_1P_512x32_c2_bm_bist` using the Sky130 `235/4 prBndry` layer instead of a the `189/4` layer, we must configure and run `layer_convert.py` once - [adapted from this script](https://github.com/FPGA-Research/heichips25-tapeout/blob/main/scripts/convert_layers.py).

## Compute in memory cells

WIP
