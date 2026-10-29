# M0 parcial — referências públicas e contratos de fundação

Data: **29/10/2026**. IDs **E00-01/E00-03**, preparação de **E04-01/E06-01**.
Base `d842f98702a3321bf33f649eb300b2466f7b2009` (microformato, PR #6).
Branch `work/m0-contracts-2026-10-29`, remoto Vibe-O-Coder/AssisScript.

## Problema e antes/depois

As referências HTDL/FS/SSC exigidas pelo planejamento existiam somente no
workspace irmão; interfaces de visualizador/plataforma e estratégia de escolha
do executor ainda não tinham contrato operacional próprio. Agora há snapshot
rastreado de 57 fontes textuais, corpus completo com 16 cenários e hashes,
perfil bootstrap, ABI escalar da ponte, ADR e fila de tarefas verificáveis.

Os rascunhos continuam rascunhos: a captura não ratifica a linguagem nem
publica resultados de runtime. Cada arquivo tem hash dos bytes originais e
hash da cópia normalizada UTF-8/LF. Não havia commit Git identificado na pasta
irmã; o manifesto registra revisão ausente, sem inventá-la. Simulador, binários
e arquivos compactados não foram importados. Os recursos diretos do corpus
de conformidade estão presentes. Validações históricas copiadas são referência
da origem e não evidência nova desta unidade.

## Decisões e arquivos

- `docs/ecossistema/PERFIL-VISUALIZADOR-V1.md`: subconjunto explícito de HTDL
  0.1 para parser real, atributos/entidades/estrutura, diagnósticos e limites.
  Janela inicial sem script/rede; o perfil completo e G1 conservam seu escopo.
- `docs/ecossistema/ABI-PLATAFORMA-V1.md`: funções C escalares, buffers com
  comprimento, ownership/cópia, thread principal, tokens revogáveis, filas,
  erros e inventário de provider ainda pendente. Loader obrigatório ausente
  continua podendo falhar antes de main; não é mascarado por erro recuperável.
- `docs/ecossistema/ADR-0001-EXECUCAO-PAGINA.md`: dois spikes comparáveis antes
  da escolha VM/Wasm, com provas de semântica e autoridade. Formato/runtime
  ainda não escolhido; sandbox por OS é obrigação separada.
- `docs/ecossistema/FILA-M0-M1.md`: entradas/saídas, dependências, aceites,
  riscos e estimativas de sessões explicitamente provisórias.
- `docs/ecossistema/referencias/htdl-drafts-2026-10-29/`: snapshot/proveniência.
- `tools/check-ecosystem-references.py`: integridade e inventário declarativo.
  Retorna status de integridade separado de conformidade/integração not-run.
- Evidência em `docs/ecossistema/evidencias/m0-contratos-2026-10-29/`, progresso
  e manifesto do instalador sincronizados. Nenhum binário é alterado.

O núcleo/motor continuam destinados a AssisScript. A ponte é pequena e serve
código confiável; páginas não a importam. A ABI evita agregados por valor e
callbacks estrangeiros que a fronteira atual não suporta. Providers só serão
anunciados após build com versão/licença/falhas/execução nativa registradas.

## Validação e limites

Plataforma: Windows/PowerShell/Python 3.14. Apenas inspeção documental e
execução do verificador de integridade, sem compilação/runtime novos.

```powershell
python tools/check-ecosystem-references.py --output docs/ecossistema/evidencias/m0-contratos-2026-10-29/integrity.json
python tools/report-ecosystem-progress.py
python tools/report-ecosystem-progress.py --check
python tools/generate-install-manifest.py
python tools/generate-install-manifest.py --check
git diff --check
```

Integridade: **57/57 arquivos** conferidos, recursos de **16/16 cenários**
inventariados, todos os cenários com **not-run**, sem convertê-los em pass.
Casos adversos do verificador em cópias isoladas: arquivo adulterado, caminho
fora da raiz e cenário duplicado são recusados; resultados em negative.json.

Não foram executados parser HTDL real, FS/SSC, janela, ABI nativa, provider,
runtime restrito, sandbox, integração ou corpus de produto em qualquer OS.
Nenhuma aceitação de ABI/layout é alegada por escrever assinaturas C.
M0 ainda exige os spikes/builds/perfis executáveis; M1 exige arena, alocação
fallível e fronteira nativa demonstradas. Hipóteses de esforço serão revistas
com as primeiras medidas de cada spike.

## Régua, publicação e próxima tarefa

**20,10% → 20,10%; 0/5 → 0/5 gates.** E00-01/E00-03 conservam nível 1, com
referências rastreadas e contratos iniciais. Pesos, baseline e trilha antiga
preservados; histórico completo acrescentado sem promoção documental de runtime.

Publicação normal por commit/push e PR sobre a branch do microformato, com
conferência do SHA remoto. Consulte o commit que introduz este relatório por
`git log --follow -- docs/relatorios/2026-10-29-m0-contratos.md`.
Push não significa CI aprovada, merge ou release.

Próxima unidade funcional: arena genérica com categoria/instância/geração,
reciclagem sem replay, geração esgotada, encerramento e teste por modelo
independente, conservando OOM e integração como obrigações abertas.
