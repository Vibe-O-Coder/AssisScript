"""Native process isolation, bounded pipes and process-tree termination."""
import importlib.util
import os
from pathlib import Path
import subprocess
import time
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Process(base.Evolution):
    def program(self,command,body,timeout=3000,limit=1024):
        data=command.encode('utf-8');assign=''.join(f'command[{i}]=byte({b});' for i,b in enumerate(data))
        return 'import "std/process.assis";\nsafe fn main():int{own command:*byte=alloc<byte>('+str(len(data)+1)+');'+assign+f'own output:process::Output=process::run_shell(command,{timeout},{limit});'+body+'return 0;}'

    def test_stdout_stderr_and_nonzero_exit(self):
        command='echo hello&echo error>&2&exit /b 7' if os.name=='nt' else 'printf "hello\\n";printf "error\\n" >&2;exit 7'
        body='print(output.error(),output.exit_code());borrow b:slice<byte>=output.body();for(let i:int=0;i<len(b);i+=1){if(b[i]!=byte(13)){print(b[i]);}}'
        expected='0 7\n'+''.join(str(b)+'\n' for b in b'hello\nerror\n')
        self.accepted(self.program(command,body),expected)

    def test_timeout_output_limit_and_recovery(self):
        sleeping='ping -n 6 127.0.0.1 >NUL' if os.name=='nt' else 'sleep 5'
        before=time.monotonic();self.accepted(self.program(sleeping,'print(output.error());',timeout=60),'-3\n');self.assertLess(time.monotonic()-before,8)
        noisy='for /L %i in (1,1,1000) do @echo abcdefghijklmnopqrstuvwxyz' if os.name=='nt' else 'yes abcdefghijklmnopqrstuvwxyz'
        self.accepted(self.program(noisy,'print(output.error());',limit=16),'-2\n')
        command='exit /b 0' if os.name=='nt' else 'exit 0'
        self.accepted(self.program(command,'print(output.error(),output.exit_code(),output.size());',limit=0),'0 0 0\n')

    def test_repeated_processes_release_runtime_resources(self):
        command='exit /b 3' if os.name=='nt' else 'exit 3'
        source=self.program(command,'')
        begin=source.index('own output:')
        source=source[:begin]+'for(let i:int=0;i<40;i+=1){'+source[begin:source.index('return 0;',begin)].replace('own output:','own output:',1)+'assert(output.error()==0&&output.exit_code()==3);}print(40);return 0;}'
        self.accepted(source,'40\n')

    def test_embedded_nul_and_limits_rejected_without_spawning(self):
        self.accepted(self.program('echo first\x00echo second','print(output.error());'),'-1\n')
        self.accepted(self.program('echo unused','print(output.error());',timeout=0),'-1\n')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
