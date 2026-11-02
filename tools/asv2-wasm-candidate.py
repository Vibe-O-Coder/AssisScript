"""Bounded ASV2 -> wasm32 comparison candidate, not a shipped page runtime.

Only canonical output of this translator may be instantiated by the harness.
There are no Wasm imports, start function, tables, native recursion or grow.
Logical registers/frames and page bytes occupy disjoint fixed memory regions.
All costs are charged per ASV2 instruction, including backward edges/calls.
"""
import argparse
import base64
import json
from pathlib import Path
import struct
import sys


def leb(n, signed=False):
    out = bytearray()
    while True:
        b = n & 127
        n >>= 7
        done = (n == 0 and (not signed or b < 64)) or (signed and n == -1 and b >= 64)
        out.append(b if done else b | 128)
        if done:
            return bytes(out)


def section(kind, data):
    return bytes([kind]) + leb(len(data)) + data


def name(s):
    b = s.encode('ascii')
    return leb(len(b)) + b


def const(n): return b'\x41' + leb(n, True)
def wide(n): return b'\x42' + leb(n, True)
def get(n): return b'\x23' + leb(n)
def put(n): return b'\x24' + leb(n)
def local(n): return b'\x20' + leb(n)
def assign(n): return b'\x21' + leb(n)
def load64(address): return address + b'\x29\x03\x00'
def store64(address, value): return address + value + b'\x37\x03\x00'
def load32(address): return address + b'\x28\x02\x00'
def store32(address, value): return address + value + b'\x36\x02\x00'
def condition(test, yes, no=b''): return test + b'\x04\x40' + yes + (b'\x05' + no if no else b'') + b'\x0b'
def terminal(status): return const(status) + put(2) + const(status) + b'\x0f'
def address(register): return get(1) + const(128) + b'\x6c' + const(register * 8) + b'\x6a'
def reg(n): return load64(address(n))
def setreg(n, value): return store64(address(n), value)


def validate(data):
    if len(data) < 16 or len(data) > 131088 or data[:4] != b'ASV2':
        raise ValueError('asv2_header')
    count, entry, memory = struct.unpack_from('<III', data, 4)
    if not 1 <= count <= 16384 or entry >= count or memory > 65536 or len(data) != 16 + 8 * count:
        raise ValueError('asv2_size')
    ops = list(struct.iter_unpack('<BBBBi', data[16:]))
    for op, a, b, c, imm in ops:
        valid = op <= 26 and a < 16
        if op in (0, 11): valid &= b == c == imm == 0
        elif op == 1: valid &= b == c == 0
        elif op in (2, 3, 4, 5, 6, 7, 17, 18, 19, 20, 21, 22): valid &= b < 16 and c < 16 and imm == 0
        elif op == 8: valid &= a == b == c == 0 and 0 <= imm < count
        elif op == 9: valid &= b == c == 0 and 0 <= imm < count
        elif op == 10: valid &= b < 16 and c <= 3 and b + c < 16 and 0 <= imm < count
        elif op == 12: valid &= b < 16 and 1 <= imm <= 8 and ((imm == 4 and c < 16) or (imm != 4 and c == 0))
        elif op in (13, 14, 15, 16, 24, 25): valid &= b < 16 and c == imm == 0
        elif op == 23: valid &= b == c == 0
        elif op == 26: valid &= a == b == c == imm == 0
        else: valid = False
        if not valid:
            raise ValueError('asv2_operand')
    return count, entry, memory, ops


def translate(data, *, frames=16, fuel=10000, calls=100, memory_limit=65536):
    count, entry, memory, ops = validate(data)
    if not 1 <= frames <= 128 or not 1 <= fuel <= 1000000 or not 0 <= calls <= 10000 or not 0 <= memory_limit <= 65536 or memory > memory_limit:
        raise ValueError('host_limit')
    # Globals: pc, frame, state, steps, calls, grant, counter(i64), result(i64),
    # pending import, arg(i64), second(i64), pending register address.
    initial = [(0x7f, entry)] + [(0x7f, 0)] * 5 + [(0x7e, 0)] * 2 + [(0x7f, 0), (0x7e, 0), (0x7e, 0), (0x7f, 0)]
    globals_data = leb(len(initial)) + b''.join(bytes([ty, 1]) + (wide(v) if ty == 0x7e else const(v)) + b'\x0b' for ty, v in initial)

    def instruction(item):
        op, a, b, c, imm = item
        if op == 0: return reg(a) + put(7) + terminal(2)
        if op == 1: return setreg(a, wide(imm))
        if op in (2, 3, 4, 6, 7, 17, 18, 19, 20, 21):
            opcode = {2: 0x7c, 3: 0x7d, 4: 0x7e, 6: 0x51, 7: 0x53, 17: 0x83, 18: 0x84, 19: 0x85, 20: 0x86, 21: 0x87}[op]
            guard = b''
            if op in (20, 21): guard = condition(reg(c) + wide(0) + b'\x53' + reg(c) + wide(64) + b'\x59\x72', terminal(-11))
            return guard + setreg(a, reg(b) + reg(c) + bytes([opcode]) + (b'\xad' if op in (6, 7) else b''))
        if op in (5, 22):
            guard = condition(reg(c) + b'\x50', terminal(-7))
            expr = reg(b) + wide(-2**63) + b'\x51' + reg(c) + wide(-1) + b'\x51\x71\x04\x7e'
            expr += wide(-2**63 if op == 5 else 0) + b'\x05' + reg(b) + reg(c) + bytes([0x7f if op == 5 else 0x81]) + b'\x0b'
            return guard + setreg(a, expr)
        if op == 8: return const(imm) + put(0)
        if op == 9: return condition(reg(a) + b'\x50', const(imm) + put(0))
        if op == 10:
            out = condition(get(1) + const(frames - 1) + b'\x46', terminal(-6))
            # Save call arguments before zeroing the new frame (frames cannot alias).
            out += store32(const(16384) + get(1) + const(4) + b'\x6c\x6a', get(0))
            out += store32(const(16896) + get(1) + const(4) + b'\x6c\x6a', const(a))
            for n in range(16):
                dst = get(1) + const(1) + b'\x6a' + const(128) + b'\x6c' + const(8*n) + b'\x6a'
                out += store64(dst, reg(b+n) if n <= c else wide(0))
            return out + get(1) + const(1) + b'\x6a' + put(1) + const(imm) + put(0)
        if op == 11:
            out = reg(a) + assign(3) + condition(get(1) + b'\x45', local(3) + put(7) + terminal(2))
            out += get(1) + const(1) + b'\x6b' + put(1)
            out += load32(const(16384) + get(1) + const(4) + b'\x6c\x6a') + put(0)
            dst = get(1) + const(128) + b'\x6c' + load32(const(16896) + get(1) + const(4) + b'\x6c\x6a') + const(8) + b'\x6c\x6a'
            return out + store64(dst, local(3))
        if op == 12:
            out = b''
            if imm == 1: out += condition(get(5) + b'\x45', terminal(-2))
            out += condition(get(4) + const(calls) + b'\x46', terminal(-8))
            if imm != 1:
                return out + get(4) + const(1) + b'\x6a' + put(4) + const(imm) + put(8) + reg(b) + put(9) + reg(c) + put(10) + address(a) + put(11) + terminal(3)
            out += condition(reg(b) + wide(-1000000) + b'\x53' + reg(b) + wide(1000000) + b'\x55\x72', terminal(-10))
            return out + get(4) + const(1) + b'\x6a' + put(4) + get(6) + reg(b) + b'\x7c' + put(6) + setreg(a, get(6))
        if op in (13, 14):
            addr = reg(b if op == 13 else a)
            out = condition(addr + wide(0) + b'\x53' + addr + wide(memory) + b'\x59\x72', terminal(-5))
            ptr = addr + b'\xa7' + const(32768) + b'\x6a'
            return out + (setreg(a, ptr + b'\x2d\x00\x00\xad') if op == 13 else ptr + reg(b) + b'\xa7\x3a\x00\x00')
        if op == 15: return setreg(a, reg(b) + b'\x50\xad')
        if op == 16: return setreg(a, reg(b))
        if op == 23: return setreg(a, reg(a) + wide(4294967295) + b'\x83' + wide(imm * 4294967296) + b'\x7c')
        if op == 24: return setreg(a, reg(b) + wide(-1) + b'\x85')
        if op == 25: return setreg(a, wide(0) + reg(b) + b'\x7d')
        return terminal(-12)

    def dispatch(first, last):
        if last - first == 1: return instruction(ops[first])
        mid = (first + last) // 2
        return condition(local(2) + const(mid) + b'\x49', dispatch(first, mid), dispatch(mid, last))

    body = condition(get(2), get(2) + b'\x0f')
    body += condition(local(0) + const(1) + b'\x48' + local(0) + const(10000) + b'\x4a\x72', const(-1) + b'\x0f')
    body += b'\x03\x40'  # loop, bounded quantum and lifetime fuel
    body += condition(local(1) + local(0) + b'\x4f', const(1) + b'\x0f')
    body += condition(get(3) + const(fuel) + b'\x4f', terminal(-3))
    body += condition(get(0) + const(count) + b'\x4f', terminal(-5))
    body += get(0) + assign(2) + get(0) + const(1) + b'\x6a' + put(0)
    body += get(3) + const(1) + b'\x6a' + put(3) + local(1) + const(1) + b'\x6a' + assign(1)
    body += dispatch(0, count) + b'\x0c\x00\x0b' + const(1)
    # Params quantum:i32; locals work,old_pc:i32 and return_temp:i64.
    function = b'\x02\x02\x7f\x01\x7e' + body + b'\x0b'
    exports = [name('tick') + b'\x00\x00', name('memory') + b'\x02\x00']
    exports += [name(n) + b'\x03' + leb(i) for i, n in enumerate(('pc', 'frame', 'state', 'steps', 'calls', 'grant', 'counter', 'result', 'pending', 'arg', 'second', 'destination'))]
    module = b'\0asm\x01\0\0\0' + section(1, b'\x01\x60\x01\x7f\x01\x7f') + section(3, b'\x01\x00')
    module += section(5, b'\x01\x01\x02\x02') + section(6, globals_data) + section(7, leb(len(exports)) + b''.join(exports))
    module += section(10, b'\x01' + leb(len(function)) + function)
    if len(module) > 8 * 1024 * 1024:
        raise ValueError('wasm_size')
    return module


def canonical(data, wasm, **limits):
    if wasm != translate(data, **limits):
        raise ValueError('noncanonical_wasm')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path); p.add_argument('output', type=Path, nargs='?')
    p.add_argument('--verify', action='store_true')
    a = p.parse_args()
    if a.verify:
        if a.input.stat().st_size > 12 * 1024 * 1024:
            raise ValueError('envelope_size')
        envelope = json.loads(a.input.read_text(encoding='utf-8'))
        data = base64.b64decode(envelope['asv2'], validate=True)
        module = base64.b64decode(envelope['wasm'], validate=True)
        limits = envelope.get('limits', {})
        if set(limits) - {'frames', 'fuel', 'calls', 'memory_limit'} or any(type(v) is not int for v in limits.values()):
            raise ValueError('host_limit')
        canonical(data, module, **limits)
        print(base64.b64encode(module).decode())
        sys.exit(0)
    if a.output is None:
        p.error('output required')
    data = a.input.read_bytes(); module = translate(data)
    a.output.write_text(json.dumps({'asv2': base64.b64encode(data).decode(), 'wasm': base64.b64encode(module).decode()}), encoding='utf-8')
