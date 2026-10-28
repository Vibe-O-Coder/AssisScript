"""Numeric ABI and arithmetic against independent Python integer/IEEE oracles."""
import importlib.util
import math
import random
import struct
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
main = base.main


class Numbers(base.Evolution):
    def test_integer_to_f32_uses_one_rounding_and_value_equality_is_numeric(self):
        self.accepted('value struct P{let x:f64;}enum E{A(P);B(f32);}' + main(
            'print(f32(4611686293305294849),f32(u64(9223372586610589697)));'
            'val a:P=new P(0.0);val b:P=new P(-0.0);val c:P=new P(0.0/0.0);'
            'print(a==b,c==c,new E.A(a)==new E.A(b),new E.A(a)!=new E.B(f32(0.0)));'),
            '0x1.0000020000000p+62 0x1.0000020000000p+63\ntrue false true true\n')

    def test_mixed_virtual_abi_and_float_tail_recursion(self):
        code='class A{let v:f64;fn init(v:f64):void{self.v=v;}fn f(a:i16,b:f32,c:u64):f64{return self.v+f64(a)+f64(b)+f64(c);}}'
        code+='class B extends A{fn f(a:i16,b:f32,c:u64):f64{return self.v+f64(a)+f64(b)+f64(c)+1.0;}}'
        code+='pure fn sum(n:int,a:f64):f64{if(n==0){return a;}return sum(n-1,a+0.5);}'
        self.accepted(code+main('let b:B=new B(20.0);let a:A=b;print(a.f(i16(10),f32(10.0),u64(1)),sum(84,0.0));free(b);'),
                      '0x1.5000000000000p+5 0x1.5000000000000p+5\n')
        result=self.invoke('run',self.source(code+main('print(sum(1000000,0.0));')),'--debug')
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,float(500000).hex()+'\n',''))

    def test_integer_widths_modular_and_signed_loads(self):
        self.accepted(main('let a:i8=i8(127);a+=i8(1);let b:i16=i16(32767);b+=i16(1);'
                           'let c:i32=i32(2147483647);c+=i32(1);let d:u16=u16(65535);d+=u16(1);'
                           'let e:u32=u32(0xffffffff);e+=u32(1);let f:u64=u64(0xffffffffffffffff);f+=u64(1);'
                           'print(a,b,c,d,e,f,u64(0xffffffffffffffff));'),
                      '-128 -32768 -2147483648 0 0 0 18446744073709551615\n')

    def test_random_integer_operations_and_unsigned_comparisons(self):
        rng = random.Random(8128)
        body, expected = [], []
        for ty, bits, signed in [('i8',8,True),('i16',16,True),('i32',32,True),('u16',16,False),('u32',32,False),('u64',64,False)]:
            for i in range(8):
                a, b = rng.randrange(1 << bits), rng.randrange(1 << bits)
                norm = lambda n: (n + (1 << (bits-1))) % (1 << bits) - (1 << (bits-1)) if signed else n % (1 << bits)
                av, bv = norm(a), norm(b)
                body.append(f'{{let a:{ty}={ty}(0x{a:x});let b:{ty}={ty}(0x{b:x});print(a+b,a-b,a*b,a<b,a>=b);}}')
                expected.append(f'{norm(av+bv)} {norm(av-bv)} {norm(av*bv)} '+('true' if av<bv else 'false')+' '+('true' if av>=bv else 'false')+'\n')
        self.accepted(main(''.join(body)), ''.join(expected))

    def test_unsigned_division_shifts_and_wrap(self):
        self.accepted(main('let x:u64=u64(0xffffffffffffffff);print(x/u64(3),x%u64(3),x>>63);'
                           'let y:i8=i8(-128);print(y/i8(-1),y%i8(-1),y>>2);'
                           'let z:u16=u16(65535);print(z>>8,z<<8);'),
                      '6148914691236517205 0 1\n-128 0 -32\n255 65280\n')
        for flags in [[], ['--no-opt']]:
            result=self.invoke('run', self.source(main('let x:u16=u16(1);print(x<<16);')), *flags)
            self.assertEqual(result.returncode,70,result.stderr)

    def test_float_arithmetic_ieee_and_exact_output(self):
        self.accepted(main('val a:f64=1.5;val b:f64=2.0;print(a+b,a-b,a*b,a/b,-a);'
                           'val x:f32=f32(0.1);print(x);'),
                      '0x1.c000000000000p+1 -0x1.0000000000000p-1 0x1.8000000000000p+1 0x1.8000000000000p-1 -0x1.8000000000000p+0\n'
                      +float(struct.unpack('<f',struct.pack('<f',0.1))[0]).hex()+'\n')

    def test_nan_infinity_zero_and_ordered_comparisons(self):
        self.accepted(main('val z:f64=0.0;val nan:f64=z/z;val inf:f64=1.0/z;'
                           'print(nan==nan,nan!=nan,nan<z,nan<=z,nan>z,nan>=z);'
                           'print(inf>1.0,-inf<z,z==-z,bool(-z),bool(nan));'
                           'if(nan<z){print(9);}else{print(42);}print(z,-z,inf,-inf);'),
                      'false true false false false false\ntrue true true false true\n42\n'
                      '0x0.0000000000000p+0 -0x0.0000000000000p+0 inf -inf\n')

    def test_saturating_float_conversions_and_unsigned_64(self):
        self.accepted(main('print(i8(200.0),i8(-200.0),u16(-1.0),u16(70000.0),int(0.0/0.0),int(1.0/0.0),int(-1.0/0.0));'
                           'print(u64(18446744073709551616.0),u64(9223372036854775808.0),u64(-1.0),f64(u64(0xffffffffffffffff)));'
                           'print(int(42.9),int(-42.9),byte(300.0));'),
                      '127 -128 0 65535 0 9223372036854775807 -9223372036854775808\n'
                      '18446744073709551615 9223372036854775808 0 0x1.0000000000000p+64\n42 -42 255\n')

    def test_buffers_records_callbacks_generics_and_abi(self):
        code='value struct P{let x:f32;let y:i16;}pure fn id<T>(x:T):T{return x;}pure fn f(x:f64):f64{return x*2.0;}'
        self.accepted(code+main('own a:*i16=alloc<i16>(2);a[0]=i16(-42);a[1]=i16(42);'
                               'own b:*f32=alloc<f32>(2);b[1]=f32(1.5);print(a[0],a[1],len(a),b[1]);'
                               'val cb:pure fn(f64):f64=f;print(cb(id::<f64>(21.0)));'
                               'val p:P=id::<P>(new P(f32(1.5),i16(-42)));print(p.x,p.y);'
                               'own v:Array<f64>=[1.5,2.0];v.push(3.0);print(v[0]+v.pop());'),
                      '-42 42 2 0x1.8000000000000p+0\n0x1.5000000000000p+5\n0x1.8000000000000p+0 -42\n0x1.2000000000000p+2\n')

    def test_decimal_literals_roundtrip_extremes_and_random(self):
        rng=random.Random(933)
        values=[5e-324,2.2250738585072014e-308,1.7976931348623157e308,1e-200,1e200]
        values += [struct.unpack('<d',rng.randbytes(8))[0] for _ in range(48)]
        values=[v for v in values if math.isfinite(v)]
        code=main(''.join(f'print({repr(v)});' for v in values))
        source=self.source(code)
        for flags in [[],['--no-opt']]:
            result=self.invoke('run',source,*flags)
            self.assertEqual(result.returncode,0,result.stderr)
            actual=[float.fromhex(line) for line in result.stdout.splitlines()]
            self.assertEqual([struct.pack('<d',x) for x in actual],[struct.pack('<d',x) for x in values])

    def test_numeric_rejections_and_output_preservation(self):
        for body,message in [
            ('val x:f32=1.0;', 'não é possível usar'),
            ('print(f32(1.0)+2.0);', 'tipos iguais'),
            ('print(i16(1)+i32(2));', 'conversão explícita'),
            ('print(1.0%2.0);', 'operador aritmético'),
            ('print(1e9999);', 'literal real'),
            ('print(1e+);', 'expoente'),
            ('print(1.2__3);', 'separador'),
        ]:
            self.rejected(main(body),message)


if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
