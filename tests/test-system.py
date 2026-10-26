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
        source=self.source('safe '+main('val civil:int=relogio_civil();val a:int=agora();assert(dormir(15)==0);val b:int=agora();print(civil,b-a);assert(dormir(-1)==-1);assert(erro_io()>0);assert(dormir(0)==0);'))
        for flags in [[],['--no-opt']]:
            before=time.time()*1000;r=self.invoke('run',source,*flags);after=time.time()*1000
            self.assertEqual(r.returncode,0,r.stderr);civil,elapsed=map(int,r.stdout.split());self.assertTrue(before-1000<=civil<=after+1000);self.assertGreaterEqual(elapsed,10);self.assertLess(elapsed,3000)

    def test_event_order_cancel_reschedule_stop_and_reentrancy(self):
        code='#yuri <std/eventos.assis>\n'
        code+='safe assis action(borrow mut l:eventos::Loop,n:int):void{print(n);if(n==1){assert(eventos::cancelar(l,2));assert(eventos::agendar(l,0,4,action)>0);assert(eventos::executar(l,1)==-2);}if(n==4){eventos::parar(l);}}'
        self.accepted(code+'safe '+main('own l:eventos::Loop=eventos::criar(4);assert(eventos::agendar(l,0,1,action)==1);assert(eventos::agendar(l,100,2,action)==2);assert(eventos::agendar(l,1,3,action)==3);'
                                      'assert(eventos::executar(l,10)>=2);assert(!eventos::cancelar(l,2));print(eventos::executar(l,10));'),
                      '1\n4\n3\n1\n')

    def test_event_capacity_limits_and_finite_budget(self):
        code='#yuri <std/eventos.assis>\nsafe assis again(borrow mut l:eventos::Loop,n:int):void{assert(eventos::agendar(l,0,n+1,again)>0);}'
        self.accepted(code+'safe '+main('own vazio:eventos::Loop=new eventos::Loop();assert(eventos::executar(vazio,1)==-1);'
                                      'own l:eventos::Loop=eventos::criar(1);assert(eventos::agendar(l,-1,0,again)==0);assert(eventos::agendar(l,0,0,again)>0);assert(eventos::agendar(l,0,1,again)==0);print(eventos::executar(l,1000));'),'1000\n')

    def test_tempo_iterator_pipeline_and_overflow_boundary(self):
        code='#yuri <std/tempo.assis>\n#yuri <std/iteradores.assis>\n'
        code+='pure assis twice(x:int):int{return x*2;}pure assis yes(x:int):bool{return x%4==0;}pure assis sum(a:int,b:int):int{return a+b;}'
        self.accepted(code+'safe '+main('assert(tempo::esperar(tempo::apos(1)));assert(!tempo::apos(-1).valido);print(iteradores::reduzir::<int>(new iteradores::Intervalo(1,11,1),0,twice,yes,sum));'
                                      'match(iteradores::proximo(new iteradores::Intervalo(9223372036854775806,9223372036854775807,2))){Fim{print(0);}Item(n,next){print(n);match(iteradores::proximo(next)){Fim{print(42);}Item(a,b){print(9);}}}}'),
                      '60\n9223372036854775806\n42\n')

    def test_binary_stdout_stderr_and_filtered_log(self):
        code='#yuri <std/cli.assis>\n#yuri <std/log.assis>\nsafe '+main('own b:*byte=alloc<byte>(3);b[0]=byte(65);b[1]=byte(0);b[2]=byte(255);assert(cli::saida(1,b,3)==3);assert(cli::saida(2,b,3)==3);assert(log::escrever(1,2,b,3)==0);assert(cli::saida(8,b,3)==-1);')
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
            data='{"valor":42,"ação":[true,null,"\\u0000"]}'.encode();r=run(data);self.assertEqual(r.returncode,0,(r.stdout,r.stderr));self.assertEqual(output.read_bytes(),data);self.assertFalse(temp.exists());self.assertEqual(r.stderr,b'')
            # A fresh process reads the persisted result and commits another copy.
            second=self.temp/'segundo.json';r=subprocess.run([binary,output,second,temp],capture_output=True,timeout=30);self.assertEqual(r.returncode,0,(r.stdout,r.stderr));self.assertEqual(second.read_bytes(),data)
            temp.write_bytes(b'nao sobrescrever');r=run(b'42');self.assertNotEqual(r.returncode,0);self.assertEqual(temp.read_bytes(),b'nao sobrescrever');self.assertEqual(output.read_bytes(),data);temp.unlink()
            # Rename onto a directory fails; the original target and input survive.
            directory=self.temp/'diretório';directory.mkdir(exist_ok=True);r=subprocess.run([binary,entry,directory,temp],capture_output=True,timeout=30);self.assertNotEqual(r.returncode,0);self.assertTrue(directory.is_dir());self.assertFalse(temp.exists());self.assertEqual(r.stderr,b'')

    def test_sync_closed_and_remove_missing_are_recoverable(self):
        target=str(self.temp/'persistente.bin').replace('\\','/');missing=str(self.temp/'ausente').replace('\\','/')
        self.accepted('safe '+main(f'own f:Arquivo=arquivo_abrir("{target}",3);assert(f!=null);assert(arquivo_sincronizar(f)==0);assert(arquivo_fechar(f)==0);assert(arquivo_sincronizar(f)==-1);assert(erro_io()>0);assert(arquivo_remover("{target}")==0);assert(arquivo_remover("{missing}")==-1);assert(erro_io()>0);'))

    def test_event_callbacks_obey_effect_and_borrow_contracts(self):
        prefix='#yuri <std/eventos.assis>\nassis bad(borrow mut l:eventos::Loop,n:int):void{}'
        self.rejected(prefix+main('own l:eventos::Loop=eventos::criar(1);eventos::agendar(l,0,1,bad);'),'não é possível usar')
        self.rejected('#yuri <std/eventos.assis>\n'+main('own l:eventos::Loop=eventos::criar(1);borrow r:eventos::Loop=l;eventos::executar(l,1);'),'borrow incompatível')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
