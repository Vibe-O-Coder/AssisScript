# window — janela nativa confiável, prova Windows x64

29/10/2026. M1-SHIM, E04-01/E04-02; fontes de desenvolvimento após alpha.15.
O módulo e o provider não estão nos pacotes anteriores. O loop, o estado e as
decisões da aplicação de exemplo são AssisScript; o shim C adapta User32/GDI.
Não há alteração do compilador, sintaxe, ownership ou ABI da linguagem.

## Construção e exemplo

Na raiz do repositório, com Python e GCC MinGW-w64 (MSYS2 UCRT64):

```powershell
python tools/build-platform.py --output build/platform/assis_platform_v1.dll
bin/assis.exe build exemplos/35_native_window.assis --debug -o build/platform/window.exe
./build/platform/window.exe
```

ASSIS_TOOLCHAIN_BIN ou --cc selecionam o GCC. O script recusa hosts diferentes
de Windows. Coloque a DLL construída e confiável junto do executável; ela usa
User32, GDI e UCRT do Windows. Não baixe uma DLL desconhecida para executá-lo.
O programa mostra texto em português, altera uma mensagem com Espaço, redesenha
ao redimensionar e fecha com Escape ou o botão da janela. Seu código não faz
parsing HTDL, rede ou execução de página.

```assis
import "std/window.assis";
safe fn main():int {
    own view:window::Window=new window::Window(1,640,240,"Ação — AssisScript");
    if(!view.opened()){print(view.error());return 1;}
    assert(view.clear(u32(0x182334ff))==0);
    assert(view.draw_text(24,24,"Olá, coração!",u32(0xffffffff))==0);
    assert(view.present()==0);
    while(true){
        val event:window::Event=view.poll(16);
        if(event.status<0){return 2;}
        if(event.status==0&&event.kind==1){break;}
    }
    return int(view.close()!=0);
}
```

## API e ownership

Window recebe instance positiva, width/height e um slice UTF-8 de título.
opened indica criação; error informa o último resultado de provider/abertura.
clear(rgba), draw_text(x,y,slice,rgba), present e close retornam o código da
[ABI](ecossistema/ABI-PLATAFORMA-V1.md). O título e os bytes de texto são
copiados durante a chamada; nenhum ponteiro emprestado fica retido no provider.
O buffer temporário e a classe AssisScript usam a alocação atual do runtime:
OOM nesse lado **ainda é fatal**. OOM recuperável do shim não encerra E02-03.

close no adaptador é idempotente e zera o token após sucesso ou revogação.
drop chama close; empréstimos impedem consumo concorrente. O token é privado,
não é HWND e não pode ser passado entre processos. Chamadas de C permanecem
unsafe internamente. Todas as operações pertencem à thread da primeira chamada
à ABI; não mova a instância para outra thread. Nenhum callback AssisScript é
registrado no Windows. Falha fatal do runtime não garante execução de drop.

poll aceita 0..50 ms e retorna um Event Copy com status, kind, instance,
generation, arg0, arg1, request_id. status 1 significa ausência de evento,
0 significa evento; negativos são erros. O adaptador valida versão, token,
instância, geração e sequência antes de devolver eventos. Campos sem evento
são zero. O programa controla a resposta a close; o pedido não destrói a
janela até o fechamento explícito/drop.

Eventos iniciais: close=1; resize=2, largura/altura; key=3, virtual key e
pressionado; pointer=4, posição do movimento; focus=5; scale=6, milésimos.
Tab/Enter/Escape/Espaço têm códigos 9/13/27/32. Ainda não há evento separado
de botão do ponteiro, roda/touch, texto composto, IME ou API assistiva.

## Provider Windows e limites

O provider tem 32 slots de janela, geração de 48 bits sem wrap, instâncias
estritamente crescentes, fila de 256 eventos e sequência de 63 bits sem wrap.
Tokens têm categoria e registro privado. Reciclagem não revalida o token antigo;
geração esgotada aposenta o slot. Essa identidade não é uma concessão de página.

Movimentos/redimensionamentos adjacentes coalescem sem atravessar eventos de
tecla/close. Saturação falha a janela com -6, oculta sua área e exige close;
outra janela continua utilizável. Esgotar a sequência destrói a janela nativa,
retendo somente os recursos necessários ao fechamento explícito. poll drena
até 512 mensagens nativas por rodada e aguarda com MsgWaitForMultipleObjectsEx,
em vez de espera ocupada. Uma chamada ainda pode sofrer atraso do scheduler/OS;
não há garantia de tempo real nem interrupção de código hostil.

Dimensões: 1..16384 por eixo, com quota adicional de 4.194.304 pixels por janela
e 16.777.216 entre superfícies vivas. São dois DIBs de 32 bits por superfície;
resize constrói antes de trocar (pico adicional de uma superfície), preservando
a anterior em falha e devolvendo -4 no próximo poll. Bytes, GDI e demais custos
não são uma quota geral da instância. Texto: até 1 MiB; título: até 4096 bytes,
sem NUL. Texto com NUL continua pelo comprimento explícito. UTF-8 malformado
retorna -1. Limites são conferidos antes de converter/copiar/alocar.

clear e texto fazem source-over inteiro sobre superfície opaca inicialmente
preta, em RGBA R nos bits altos/A nos baixos. Texto usa máscara GDI e fonte
DEFAULT_GUI_FONT do sistema; não redistribui fonte. Não implementa o motor de
fontes/shaping/bidi/seleção/IME exigido por E04-04. Pintura nativa usa o último
buffer mesmo após exposição. Resize reinicia o buffer preto e agenda redesenho.
Criação usa contexto DPI por monitor sem alterar permanentemente o contexto do
host; migração entre monitores, escala 200% e acessibilidade não foram aceitas.

Linux/macOS: available retorna false e abertura retorna -3, sem importar DLL.
No Windows, DLL/símbolo ausente é falha do loader **antes de main**; não retorna
-3. Uma ABI diferente é recusada pelo adaptador antes de open. O provider é
opcional e não é instalado silenciosamente pelos scripts existentes.

## Evidência e suporte

[Relatório](relatorios/2026-10-29-m1-plataforma-windows.md) e
[resultados rastreados](ecossistema/evidencias/m1-plataforma-2026-10-29/windows-x64.json).
Testes usam janelas nativas ocultas e uma DLL de teste com injeção de falhas;
essa DLL não é a DLL de produção. As exportações de diagnóstico são recusadas
na build de produção. Oráculo C independente, modelo Python de composição,
eventos/ordem, buffers com canários, empréstimos, drop, OOM e 1.000 ciclos
estão em tests/test-platform-window.py.

```powershell
$env:ASSIS_BIN=(Resolve-Path build/assis-platform.exe).Path
python tools/validate-platform.py --output build/platform-validation/windows-x64.json
```

Somente execução Windows x64 do provider é anunciada como prova parcial.
Geração dos cinco formatos não certifica provider Linux/macOS/ARM64.
G1, G2 e a integração do visualizador continuam abertos. safe não é sandbox;
esta biblioteca pertence exclusivamente ao shell/motor confiáveis.
