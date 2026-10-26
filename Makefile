CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Wno-misleading-indentation
LDFLAGS ?= -static -s

.PHONY: all windows test test-pe test-dev test-evolution test-generics test-functions test-generic-classes test-collections-ast test-ownership-functions test-values test-files test-text-bytes test-cli test-alpha8 bench clean runtime
all: bin/assis

bin/assis: src/assisc.c $(wildcard src/*.h src/*.inc)
	mkdir -p bin
	$(CC) $(CFLAGS) src/assisc.c $(LDFLAGS) -o bin/assis

MINGW_CC ?= x86_64-w64-mingw32-gcc
windows: bin/assis.exe bin/assis-setup.exe

bin/assis.exe: src/assisc.c $(wildcard src/*.h src/*.inc)
	mkdir -p bin
	$(MINGW_CC) $(CFLAGS) -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/assisc.c -o bin/assis.exe

bin/assis-setup.exe: src/windows_setup.c src/version.h src/install_files.inc src/install_optional.inc
	mkdir -p bin
	$(MINGW_CC) $(CFLAGS) -municode -static -static-libgcc -s -Wl,--no-insert-timestamp src/windows_setup.c -lshell32 -ladvapi32 -luser32 -o bin/assis-setup.exe

runtime:
	sh tools/embed-runtime.sh

test: bin/assis
	sh tests/test.sh
	sh tests/test-modules.sh

build/pe_probe: tests/pe_probe.c
	mkdir -p build
	$(CC) -O2 -std=c11 -Wall -Wextra -Wno-misleading-indentation tests/pe_probe.c -o build/pe_probe

test-pe: bin/assis build/pe_probe
	sh tests/test-pe.sh

test-dev:
	node --test --test-isolation=none tests/test-development.js tests/test-v3.js tests/test-v31.js tests/test-v32.js tests/test-lsp.js vscode-assisscript/test/language.test.js vscode-assisscript/test/extension.test.js

test-evolution: bin/assis
	python3 tests/test-evolution.py

test-generics: bin/assis
	python3 tests/test-generics.py

test-functions: bin/assis
	python3 tests/test-functions.py

test-generic-classes: bin/assis
	python3 tests/test-generic-classes.py

test-collections-ast: bin/assis
	python3 tests/test-collections-ast.py

test-ownership-functions: bin/assis
	python3 tests/test-ownership-functions.py

test-values: bin/assis
	python3 tests/test-values.py

test-files: bin/assis
	python3 tests/test-files.py

test-text-bytes: bin/assis
	python3 tests/test-text-bytes.py

test-cli: bin/assis
	python3 tests/test-cli.py

test-alpha8: bin/assis
	python3 tests/test-numbers.py
	python3 tests/test-packages.py
	python3 tests/test-json.py
	python3 tests/test-system.py
	python3 tests/test-tooling.py

.PHONY: test-alpha9
test-alpha9: bin/assis
	python3 tests/test-slices.py
	python3 tests/test-managed-classes.py
	python3 tests/test-backend-alpha9.py

.PHONY: test-alpha10
test-alpha10: bin/assis
	python3 tests/test-optimization.py
	python3 tests/test-english-api.py
	python3 tests/test-release-policy.py

bench:
	node tools/benchmark.js

clean:
	rm -f bin/assis bin/assis.exe bin/assis-setup.exe
	rm -rf build
