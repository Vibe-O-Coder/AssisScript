"""Validate and render the versioned AssisScript ecosystem capability rubric."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / 'docs/ecossistema'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local_file(name):
    path = (ROOT / name).resolve()
    require(path.is_relative_to(ROOT), f'Path outside repository: {name}')
    require(path.is_file(), f'Missing evidence file: {name}')
    return path


def validate(data):
    require(data['schema'] == 'assisscript-ecosystem-progress-v1', 'Unknown schema')
    require(data['rubric_version'] == 1, 'Update validator for a new rubric version')
    groups = data['groups']
    require([g['id'] for g in groups] == [f'E{i:02}' for i in range(12)], 'Expected E00-E11')
    require(all(type(g['weight']) is int and g['weight'] > 0 for g in groups), 'Invalid weights')
    require(sum(g['weight'] for g in groups) == 100, 'Weights must sum to 100')
    group_ids = {g['id'] for g in groups}
    items = [i for g in groups for i in g['items']]
    identities = {i['id'] for i in items}
    require(len(items) == len(identities) == 60, 'Expected 60 unique criteria')
    baseline = json.loads((DIRECTORY / 'BASELINE-2026-10-29.json').read_text(encoding='utf-8'))
    local_sources = {
        ('assis' if s['scope'] == 'AssisScript' else 'htdl', s['path'])
        for s in baseline['source_files']
    }
    for group in groups:
        require([i['id'] for i in group['items']] == [f'{group["id"]}-{n:02}' for n in range(1, 6)],
                f'Invalid criterion IDs: {group["id"]}')
        require(set(group['dependencies']) <= group_ids, 'Unknown group dependency')
        for item in group['items']:
            require(type(item['level']) is int and 0 <= item['level'] <= 4, f'Invalid level: {item["id"]}')
            require(all(item.get(k) for k in ('name', 'acceptance', 'baseline', 'evidence')), f'Incomplete criterion: {item["id"]}')
            for source in item['evidence']:
                if source.startswith('local:'):
                    namespace, path = source[6:].split('/', 1)
                    require((namespace, path) in local_sources, f'Local source missing from frozen baseline: {source}')
                else:
                    local_file(source)
            if item['level'] == 4:
                proof = item.get('verification', {})
                require(all(proof.get(k) for k in ('report', 'revision', 'platforms', 'commands', 'publication')),
                        f'Level 4 requires report/revision/platforms/commands/publication: {item["id"]}')
                local_file(proof['report'])
                require(re.fullmatch(r'[0-9a-f]{40}', proof['revision']) is not None, 'Expected full evidence revision')
                require(proof['publication'].startswith('https://github.com/Vibe-O-Coder/AssisScript/'), 'Publication must identify AssisScript on GitHub')
    visiting, visited = set(), set()
    dependencies = {g['id']: g['dependencies'] for g in groups}

    def visit(identity):
        require(identity not in visiting, f'Circular dependency: {identity}')
        if identity in visited:
            return
        visiting.add(identity)
        for parent in dependencies[identity]:
            visit(parent)
        visiting.remove(identity)
        visited.add(identity)

    for identity in group_ids:
        visit(identity)
    gates = data['gates']
    gate_ids = {g['id'] for g in gates}
    require(len(gates) == 5 and gate_ids == {f'G{i}' for i in range(1, 6)}, 'Expected G1-G5')
    for gate in gates:
        require(type(gate['passed']) is bool, 'Gate approval must be boolean')
        require(set(gate['required']) <= group_ids, 'Unknown gate dependency')
        if gate['passed']:
            require(gate.get('evidence'), f'Approved gate requires evidence: {gate["id"]}')
            for path in gate['evidence']:
                local_file(path)
    require(data['history'], 'History cannot be empty')
    for record in data['history']:
        require(record['rubric_version'] == data['rubric_version'], 'History rubric version mismatch')
        require(set(record['levels']) == identities, 'History must freeze all 60 levels')
        require(all(type(v) is int and 0 <= v <= 4 for v in record['levels'].values()), 'Invalid historical level')
        require(set(record['gates']) == gate_ids and all(type(v) is bool for v in record['gates'].values()), 'History must freeze five gate states')
        require(score(data, record['levels']) < 100 or all(record['gates'].values()), 'Historical 100% requires all gates')
    latest = data['history'][-1]
    require(latest['levels'] == {i['id']: i['level'] for i in items}, 'Append a complete history snapshot after changing levels')
    require(latest['gates'] == {g['id']: g['passed'] for g in gates}, 'Append history after changing gates')
    require(latest['date'] == data['date'], 'Current date must match latest history')
    require(score(data) < 100 or all(g['passed'] for g in gates), '100% requires all five gates')


def score(data, levels=None):
    levels = levels if levels is not None else {i['id']: i['level'] for g in data['groups'] for i in g['items']}
    return sum(Decimal(g['weight']) * sum(levels[i['id']] for i in g['items']) / (4 * len(g['items'])) for g in data['groups'])


def number(value):
    return str(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)).replace('.', ',')


def evidence_link(source):
    if source.startswith('local:'):
        return f'`{source}`'
    return f'[{Path(source).name}](../../{source})'


def render(data):
    total = score(data)
    passed = sum(g['passed'] for g in data['gates'])
    assessment_note = data.get('assessment_note', 'A baseline inicial é uma estimativa documental provisória das fundações aproveitáveis. Não foram reexecutados testes do compilador/runtime nesta sessão.')
    text = f'''# Progresso — capacidade do AssisScript para o ecossistema web

Data: {data['date']}. Régua v{data['rubric_version']}. **{number(total)}/100 pontos ({number(total)}%)**, com **{passed}/5 gates aprovados**.

Estado da avaliação: `{data['assessment']}`. Escopo: {data['scope']}

{assessment_note} O número não mede prazo, esforço restante ou prontidão para produção. Casas decimais tornam a soma auditável; não significam precisão de previsão.

Os 100/100 das antigas fases 0–6 medem outro escopo e permanecem preservados. Esta régua tem 60 critérios em 12 frentes; cinco critérios dividem igualmente o peso de cada frente. Níveis 0–4 rendem 0%, 25%, 50%, 75% e 100% do crédito. Fórmula: `Σ peso × soma(níveis) / 20`. Só há conclusão com todos os critérios em 4 e os cinco gates aprovados.

[Plano completo](PLANO-MESTRE.md) · [Fonte dos estados](PROGRESSO.json) · [Baseline e hashes](BASELINE-2026-10-29.json) · [Masterprompt](MASTERPROMPT.md)

## Pontuação por frente

| Frente | Peso | Níveis dos cinco critérios | Pontos |
| --- | ---: | --- | ---: |
'''
    for group in data['groups']:
        points = Decimal(group['weight']) * sum(i['level'] for i in group['items']) / 20
        levels = ', '.join(str(i['level']) for i in group['items'])
        text += f'| {group["id"]} — {group["name"]} | {group["weight"]} | {levels} | {number(points)} |\n'
    text += f'| **Total** | **100** | **60 critérios** | **{number(total)}** |\n'
    text += '\n## Gates de integração\n\n| Gate | Aceitação | Estado |\n| --- | --- | --- |\n'
    for gate in data['gates']:
        state = 'Aprovado com evidência registrada' if gate['passed'] else 'Não aprovado'
        text += f'| {gate["id"]} | {gate["name"]} | {state} |\n'
    text += '\nG2 aberto impede anunciar execução segura de páginas remotas. Pontuação alta não dispensa nenhum gate. A aprovação exige relatório do marco, testes e revisão exata.\n'
    text += '\n## Histórico congelado\n\n| Data | Retrato | Pontos | Gates |\n| --- | --- | ---: | ---: |\n'
    for record in data['history']:
        text += f'| {record["date"]} | {record["label"]} | {number(score(data, record["levels"]))} | {sum(record["gates"].values())}/5 |\n'
    text += '\n## Estado e evidência dos 60 critérios\n'
    for group in data['groups']:
        text += f'\n### {group["id"]} — {group["name"]}\n\n| Critério | Nível | Justificativa e fontes |\n| --- | ---: | --- |\n'
        for item in group['items']:
            sources = '; '.join(evidence_link(s) for s in item['evidence'])
            text += f'| {item["id"]} — {item["name"]} | {item["level"]}/4 | {item["baseline"]} {sources} |\n'
    text += '''
Fontes `local:assis/...` e `local:htdl/...` são referências locais inventariadas por hash na baseline, não links para arquivos publicados por esta mudança. Documentos históricos atestam somente seus candidatos. A primeira sessão de implementação confirma ou corrige o crédito da tarefa com resultados próprios.

Para atualizar: alterar o JSON com justificativa/evidência, acrescentar histórico completo e executar `python tools/report-ecosystem-progress.py`. Verificar com `python tools/report-ecosystem-progress.py --check`. O validador confere a estrutura e a aritmética, sem executar nem certificar os testes citados.
'''
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the saved report is stale')
    args = parser.parse_args()
    try:
        data = json.loads((DIRECTORY / 'PROGRESSO.json').read_text(encoding='utf-8'))
        validate(data)
        content = render(data)
        output = DIRECTORY / 'PROGRESSO.md'
        if args.check:
            require(output.read_text(encoding='utf-8') == content, 'Regenerate docs/ecossistema/PROGRESSO.md')
        else:
            output.write_text(content, encoding='utf-8', newline='\n')
        print(f'Ecosystem rubric v{data["rubric_version"]}: {score(data):.2f}/100 points; {sum(g["passed"] for g in data["gates"])}/5 gates')
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'Invalid ecosystem progress: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
