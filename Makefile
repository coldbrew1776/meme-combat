# Meme Blitz - NES game built with cc65 (https://cc65.github.io)
ROM := build/memeblitz.nes
RELEASE_ROM := release/memeblitz.nes

# A normal build leaves a playable ROM in the release location as well as the
# intermediate build directory, so it is immediately ready for an emulator.
all: $(RELEASE_ROM)

build/chr.bin: tools/gen_chr.py assets/sprites.png
	@mkdir -p build
	python3 tools/gen_chr.py $@

$(ROM): src/main.c src/chr.s build/chr.bin
	cl65 -t nes -O -C src/nes.cfg -o $@ src/main.c src/chr.s

# Produce a local distributable ROM under release/.
$(RELEASE_ROM): $(ROM)
	@mkdir -p release
	cp $< $@

release: $(RELEASE_ROM)

# Launch in Mesen
run: $(ROM)
	/Applications/Mesen.app/Contents/MacOS/Mesen "$(abspath $(ROM))"

clean:
	rm -rf build release

.PHONY: all release run clean
