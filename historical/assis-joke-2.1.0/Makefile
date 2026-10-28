CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation
LDFLAGS ?= -static -s

.PHONY: all windows test test-pe clean runtime
all: bin/assis

bin/assis: src/assisc.c src/runtime_blob.h src/runtime_win_blob.h src/pe_writer.h src/elf_format.h
	mkdir -p bin
	$(CC) $(CFLAGS) src/assisc.c $(LDFLAGS) -o bin/assis

MINGW_CC ?= x86_64-w64-mingw32-gcc
windows: bin/assis.exe bin/assis-setup.exe

bin/assis.exe: src/assisc.c src/runtime_blob.h src/runtime_win_blob.h src/pe_writer.h src/elf_format.h
	mkdir -p bin
	$(MINGW_CC) $(CFLAGS) -municode -static -static-libgcc -s src/assisc.c -o bin/assis.exe

bin/assis-setup.exe: src/windows_setup.c
	mkdir -p bin
	$(MINGW_CC) $(CFLAGS) -municode -static -static-libgcc -s src/windows_setup.c -lshell32 -ladvapi32 -luser32 -o bin/assis-setup.exe

runtime:
	sh tools/embed-runtime.sh

test: bin/assis
	sh tests/test.sh

build/pe_probe: tests/pe_probe.c
	mkdir -p build
	$(CC) -O2 -std=c11 -Wall -Wextra -Wno-misleading-indentation tests/pe_probe.c -o build/pe_probe

test-pe: bin/assis build/pe_probe
	sh tests/test-pe.sh

clean:
	rm -f bin/assis bin/assis.exe bin/assis-setup.exe
	rm -rf build
