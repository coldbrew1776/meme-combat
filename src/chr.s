; Pulls the generated graphics bank (see tools/gen_chr.py) into the CHR ROM.
.segment "TILES"
.incbin "build/chr.bin"
