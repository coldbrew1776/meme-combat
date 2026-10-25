# Meme Blitz - NES game built with cc65 (https://cc65.github.io)
ROM := build/memeblitz.nes

all: $(ROM)

build/chr.bin: tools/gen_chr.py
	@mkdir -p build
	python3 tools/gen_chr.py $@

$(ROM): src/main.c src/chr.s build/chr.bin
	cl65 -t nes -O -C src/nes.cfg -o $@ src/main.c src/chr.s

# Launch in FCEUX
run: $(ROM)
	fceux $(ROM)

clean:
	rm -rf build

.PHONY: all run clean
