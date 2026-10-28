"""Real clocks, cooperative timers, binary IO and atomic persistence failures."""
import importlib.util
import os
import subprocess
import time
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
main=base.main

class System(base.Evolution):
    def test_clocks_sleep_error_and_elapsed_time(self):
        source=self.source('safe '+main('val civil:int=civil_ms();val a:int=monotonic_ms();assert(sleep_ms(15)==0);val b:int=monotonic_ms();print(civil,b-a);assert(sleep_ms(-1)==-1);assert(io_error()>0);assert(sleep_ms(0)==0);'))
        for flags in [[],['--no-opt']]:
            before=time.time()*1000;r=self.invoke('run',source,*flags);after=time.time()*1000
            self.assertEqual(r.returncode,0,r.stderr);civil,elapsed=map(int,r.stdout.split());self.assertTrue(before-1000<=civil<=after+1000);self.assertGreaterEqual(elapsed,10);self.assertLess(elapsed,3000)

    def test_event_order_cancel_reschedule_stop_and_reentrancy(self):
        code='import "std/events.assis";\n'
        code+='safe fn action(borrow mut l:events::Loop,n:int):void{print(n);if(n==1){assert(events::cancel(l,2));assert(events::schedule(l,0,4,action)>0);assert(events::run(l,1)==-2);}if(n==4){events::stop(l);}}'
        self.accepted(code+'safe '+main('own l:events::Loop=events::create(4);assert(events::schedule(l,0,1,action)==1);assert(events::schedule(l,100,2,action)==2);assert(events::schedule(l,1,3,action)==3);'
                                      'assert(events::run(l,10)>=2);assert(!events::cancel(l,2));print(events::run(l,10));'),
                      '1\n4\n3\n1\n')

    def test_event_capacity_limits_and_finite_budget(self):
        code='import "std/events.assis";\nsafe fn again(borrow mut l:events::Loop,n:int):void{assert(events::schedule(l,0,n+1,again)>0);}'
        self.accepted(code+'safe '+main('own vazio:events::Loop=new events::Loop();assert(events::run(vazio,1)==-1);'
                                      'own l:events::Loop=events::create(1);assert(events::schedule(l,-1,0,again)==0);assert(events::schedule(l,0,0,again)>0);assert(events::schedule(l,0,1,again)==0);print(events::run(l,1000));'),'1000\n')

    def test_tempo_iterator_pipeline_and_overflow_boundary(self):
        code='import "std/time.assis";\nimport "std/iterators.assis";\n'
        code+='pure fn twice(x:int):int{return x*2;}pure fn yes(x:int):bool{return x%4==0;}pure fn sum(a:int,b:int):int{return a+b;}'
        self.accepted(code+'safe '+main('assert(time::wait_until(time::after(1)));assert(!time::after(-1).valid);print(iterators::reduce::<int>(new iterators::Range(1,11,1),0,twice,yes,sum));'
                                      'match(iterators::next(new iterators::Range(9223372036854775806,9223372036854775807,2))){End{print(0);}Item(n,next){print(n);match(iterators::next(next)){End{print(42);}Item(a,b){print(9);}}}}'),
                      '60\n9223372036854775806\n42\n')

    def test_binary_stdout_stderr_and_filtered_log(self):
        code='import "std/cli.assis";\nimport "std/log.assis";\nsafe '+main('own b:*byte=alloc<byte>(3);b[0]=byte(65);b[1]=byte(0);b[2]=byte(255);assert(cli::saida(1,b,3)==3);assert(cli::saida(2,b,3)==3);assert(log::write(1,2,b,3)==0);assert(cli::saida(8,b,3)==-1);')
        source=self.source(code)
        for flags in [[],['--no-opt']]:
            r=subprocess.run([base.COMPILER,'run',source,'--safe','--debug',*flags],capture_output=True,timeout=30)
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,b'A\0\xff',b'A\0\xff'))

    def test_atomic_config_persistence_restart_and_preservation(self):
        for flags in [[],['--no-opt']]:
            binary=self.temp/('config.exe' if os.name=='nt' else 'config');r=self.invoke('build',base.ROOT/'exemplos/24_config_json.assis','--safe','--debug','-o',binary,*flags);self.assertEqual(r.returncode,0,r.stderr)
            entry=self.temp/'entrada á 日本.json';output=self.temp/'saída 😀.json';temp=self.temp/'transação 😀.json'
            def run(data):
                entry.write_bytes(data);return subprocess.run([binary,entry,output,temp],capture_output=True,timeout=30)
            output.write_bytes(b'preservado')
            for invalid in [b'{',b'null null',b'"\xff"',b'['*65+b'0'+b']'*65,b' '*1048577]:
                r=run(invalid);self.assertNotEqual(r.returncode,0,(r.stdout,r.stderr));self.assertEqual(output.read_bytes(),b'preservado');self.assertFalse(temp.exists());self.assertEqual(r.stderr,b'')
            data='{"value":42,"ação":[true,null,"\\u0000"]}'.encode();r=run(data);self.assertEqual(r.returncode,0,(r.stdout,r.stderr));self.assertEqual(output.read_bytes(),data);self.assertFalse(temp.exists());self.assertEqual(r.stderr,b'')
            # A fresh process reads the persisted result and commits another copy.
            second=self.temp/'segundo.json';r=subprocess.run([binary,output,second,temp],capture_output=True,timeout=30);self.assertEqual(r.returncode,0,(r.stdout,r.stderr));self.assertEqual(second.read_bytes(),data)
            temp.write_bytes(b'nao sobrescrever');r=run(b'42');self.assertNotEqual(r.returncode,0);self.assertEqual(temp.read_bytes(),b'nao sobrescrever');self.assertEqual(output.read_bytes(),data);temp.unlink()
            # Rename onto a directory fails; the original target and input survive.
            directory=self.temp/'diretório';directory.mkdir(exist_ok=True);r=subprocess.run([binary,entry,directory,temp],capture_output=True,timeout=30);self.assertNotEqual(r.returncode,0);self.assertTrue(directory.is_dir());self.assertFalse(temp.exists());self.assertEqual(r.stderr,b'')

    def test_sync_closed_and_remove_missing_are_recoverable(self):
        target=str(self.temp/'persistente.bin').replace('\\','/');missing=str(self.temp/'ausente').replace('\\','/')
        self.accepted('safe '+main(f'own f:File=file_open("{target}",3);assert(f!=null);assert(file_sync(f)==0);assert(file_close(f)==0);assert(file_sync(f)==-1);assert(io_error()>0);assert(file_remove("{target}")==0);assert(file_remove("{missing}")==-1);assert(io_error()>0);'))

    def test_event_callbacks_obey_effect_and_borrow_contracts(self):
        prefix='import "std/events.assis";\nfn bad(borrow mut l:events::Loop,n:int):void{}'
        self.rejected(prefix+main('own l:events::Loop=events::create(1);events::schedule(l,0,1,bad);'),'não é possível usar')
        self.rejected('import "std/events.assis";\n'+main('own l:events::Loop=events::create(1);borrow r:events::Loop=l;events::run(l,1);'),'borrow incompatível')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
