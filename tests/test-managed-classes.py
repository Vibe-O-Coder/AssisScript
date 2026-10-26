"""Receiver effects and dynamic destruction of managed class hierarchies."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
main=base.main

CLASS='''ASSIS Base {
    private own data:*int;
    assis assis_fodase(borrow mut self):void{self.data=alloc<int>(2);self.data[0]=40;}
    assis read(borrow self):int{return self.data[0];}
    assis set(borrow mut self,n:int):void{self.data[0]=n;}
}
ASSIS Child extends Base {
    private own extra:*byte;
    assis assis_fodase(borrow mut self):void{self.extra=alloc<byte>(3);}
    assis read(borrow self):int{return 42;}
}'''

class ManagedClasses(base.Evolution):
    def test_final_classes_preserve_library_invariants(self):
        self.rejected('#yuri <std/unicode.assis>\nASSIS Evil extends unicode::Texto{assis assis_fodase(borrow mut self):void{}}'+main(''),'classe final')
        self.rejected('#yuri <std/proprios.assis>\nASSIS Evil extends proprios::Lista<Arquivo>{}'+main(''),'classe final')
        self.rejected('final ASSIS C<T>{}ASSIS D extends C<int>{}'+main(''),'classe final')
    def test_utf8_validity_agrees_with_independent_decoder(self):
        cases=[bytes([i]) for i in range(256)]
        cases += [b'',b'\0',b'\xc2\x80',b'\xdf\xbf',b'\xe0\xa0\x80',b'\xed\x9f\xbf',b'\xef\xbf\xbf',b'\xf0\x90\x80\x80',b'\xf4\x8f\xbf\xbf',b'\xc0\x80',b'\xe0\x9f\xbf',b'\xed\xa0\x80',b'\xf0\x8f\xbf\xbf',b'\xf4\x90\x80\x80']
        body='own b:*byte=alloc<byte>(4);'
        for data in cases:
            try:data.decode('utf-8');valid=True
            except UnicodeDecodeError:valid=False
            body+=''.join(f'b[{i}]=byte({c});' for i,c in enumerate(data))
            body+=f'assert((unicode::erro(fatia(b,0,{len(data)}))<0)=='+('true' if valid else 'false')+');'
        self.accepted('#yuri <std/unicode.assis>\nsafe '+main(body))

    def test_class_cleanup_on_break_continue_and_early_return(self):
        self.accepted(CLASS+'safe assis early(n:int):int{own c:Base=new Base();if(n==1){return c.read();}return 42;}'
            +'safe '+main('let total:int=0;for(let i:int=0;i<100;i+=1){own c:Base=new Child();if(i==0){continue;}if(i==50){break;}total+=c.read();}print(total,early(1),early(0));'),'2058 40 42\n')

    def test_owning_collection_move_borrow_pop_and_drop(self):
        self.accepted('#yuri <std/proprios.assis>\n'+CLASS+'safe '+main(
            'own lista:proprios::Lista<Base>=new proprios::Lista<Base>();'
            'lista.inserir(new Base());lista.inserir(new Child());'
            '{borrow b:Base=lista.obter(1);print(lista.tamanho(),b.read());}'
            'own ultimo:Base=lista.retirar();print(ultimo.read(),lista.tamanho());'), '2 40\n42 1\n')
        self.rejected('#yuri <std/proprios.assis>\n'+CLASS+main(
            'own lista:proprios::Lista<Base>=new proprios::Lista<Base>();lista.inserir(new Base());'
            'borrow b:Base=lista.obter(0);lista.retirar();'),'exclusivo')

    def test_utf8_text_embedded_zero_copy_and_borrow(self):
        code='#yuri <std/unicode.assis>\nsafe '+main(
            'own dados:*byte=alloc<byte>(4);dados[0]=byte(65);dados[1]=byte(0);dados[2]=byte(195);dados[3]=byte(169);'
            'own t:unicode::Texto=new unicode::Texto();assert(t.carregar(fatia(dados,0,4)));'
            '{borrow s:slice<byte>=t.visualizar();print(len(s),int(s[1]),unicode::proximo(s,2));}'
            'dados[2]=byte(255);assert(!t.carregar(fatia(dados,0,4)));'
            'borrow r:slice<byte>=t.recortar(2,2);print(int(r[0]),len(r));')
        self.accepted(code,'4 0 4\n195 2\n')
        self.rejected('#yuri <std/unicode.assis>\n'+main('own t:unicode::Texto=new unicode::Texto();borrow s:slice<byte>=t.visualizar();free(t);'),'borrow ativo')
    def test_constructor_mutation_borrow_and_dynamic_drop(self):
        self.accepted(CLASS+'safe '+main('own b:Base=new Base();print(b.read());b.set(42);'
            '{borrow r:Base=b;print(r.read());}own c:Base=new Child();print(c.read(),b.read());'), '40\n42\n42 42\n')

    def test_move_upcast_composition_and_early_return(self):
        prefix=CLASS+'struct Holder{own obj:Base;}safe assis consume(own b:Base):int{return b.read();}'
        self.accepted(prefix+'safe '+main('own c:Child=new Child();own h:Holder=new Holder(move(c));'
            'print(consume(move(h.obj)));own b:Base=new Base();free(b);'), '42\n')

    def test_generic_class_and_repeated_replacement(self):
        self.accepted('ASSIS Box<T>{private own data:*T;'
            'assis assis_fodase(borrow mut self,n:T):void{self.data=alloc<T>(1);self.data[0]=n;}'
            'assis get(borrow self):T{return self.data[0];}'
            'assis reset(borrow mut self,n:T):void{self.data=alloc<T>(1);self.data[0]=n;}}'
            +'safe '+main('own b:Box<int>=new Box<int>(7);print(b.get());b.reset(42);print(b.get());'), '7\n42\n')

    def test_receiver_exclusivity_and_legacy_rejections(self):
        for body,message in [
            ('own b:Base=new Base();borrow r:Base=b;r.set(1);','exclusivo'),
            ('own b:Base=new Base();borrow r:Base=b;b.set(1);','exclusivo'),
            ('own b:Base=new Base();borrow mut r:Base=b;b.read();','borrow incompatível'),
            ('own b:Base=new Base();borrow r:Base=b;free(b);','borrow ativo'),
        ]: self.rejected(CLASS+main(body),message)
        self.rejected('ASSIS Legacy{assis read():int{return 42;}}'+main('own b:Legacy=new Legacy();'),'contrato de receptor')
        self.rejected('ASSIS Bad{let n:int;assis set(borrow self):void{self.n=1;}}'+main(''),'exclusivo')
        self.rejected('ASSIS Bad{assis escape(borrow self):Bad{return self;}}'+main(''),'não pode escapar')
        self.rejected('ASSIS B{assis f(borrow self):void{}}ASSIS C extends B{assis f(borrow mut self):void{}}'+main(''),'contrato de receptor')
        self.rejected('ASSIS B{assis f(borrow mut self):void{free(self);}}'+main(''),'somente own')


if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
