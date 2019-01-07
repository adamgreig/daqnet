.PHONY: all
all: build/switch.bin

build/switch.il: daqnet/__init__.py daqnet/top.py daqnet/platform.py
	mkdir -p build
	python3 -m daqnet switch

build/switch.json: build/switch.il
	yosys -q -p "synth_ice40 -json $@" build/switch.il

build/switch.asc: build/switch.json
	nextpnr-ice40 --hx8k --package bg121 --json $< --pcf build/switch.pcf --asc $@ --freq 100

build/switch.bin: build/switch.asc
	icepack $< $@

.PHONY: program
program: build/switch.bin
	/home/adam/Projects/amp_flashprog/prog.py --fpga $<

.PHONY: clean
clean:
	$(RM) -rf build
