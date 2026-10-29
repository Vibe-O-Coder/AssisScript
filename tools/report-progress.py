"""Generate the completion estimate from an explicit, weighted roadmap checklist."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true', help='Fail when the saved report differs from the checklist')
args = parser.parse_args()
data = json.loads((ROOT / 'docs/PROGRESSO.json').read_text(encoding='utf-8'))
credit = {'pending': Decimal(0), 'partial': Decimal('0.5'), 'complete': Decimal(1)}
labels = {'pending': 'Pendente', 'partial': 'Parcial (50%)', 'complete': 'Concluído no escopo do critério'}
assert [p['id'] for p in data['phases']] == list(range(7))
assert sum(p['weight'] for p in data['phases']) == 100
identities = [item['id'] for p in data['phases'] for item in p['items']]
assert len(identities) == len(set(identities)) == 35
assert all(item['status'] in credit for p in data['phases'] for item in p['items'])
assert data['version'] == json.loads((ROOT / 'vscode-assisscript/package.json').read_text(encoding='utf-8'))['version']
assert data['history'][-1]['version'] == data['version']
assert data['history'][-1]['overrides'] == {item['id']: item['status'] for p in data['phases'] for item in p['items']}


def score(overrides=None):
    overrides = overrides or {}
    assert set(overrides) <= set(identities)
    points = []
    for phase in data['phases']:
        fraction = sum(credit[overrides.get(item['id'], item['status'])] for item in phase['items']) / len(phase['items'])
        points.append((fraction, fraction * phase['weight']))
    return sum(value for _, value in points), points


def rounded(value):
    return str(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


total, phases = score()
text = (f'# Estimativa de conclusão — {data["version"]}\n\n'
        f'Data: {data["date"]}. **Conclusão estimada: {rounded(total)}%** '
        f'({str(total).replace(".", ",")} pontos de 100).\n\n'
        f'Escopo: {data["scope"]}\n\n'
        'É uma estimativa de engenharia baseada nas entregas do plano, não uma medição de horas restantes, '
        'prazo, probabilidade de sucesso ou garantia de produção. Uma linguagem pode continuar evoluindo após '
        'este escopo. Os pesos representam importância relativa e são uma convenção explícita, revisável.\n\n'
        '## Método\n\n'
        'São 35 critérios, cinco por fase. Cada critério divide igualmente o peso de sua fase. '
        'Concluído recebe 100% desse crédito; parcial recebe 50%; pendente recebe 0%. '
        'A soma ponderada é arredondada ao inteiro mais próximo, com meio ponto para cima. '
        'Parcial indica uma implementação útil com parte relevante da aceitação ainda aberta. '
        'Mudanças de escopo/peso devem ser registradas antes de comparar versões.\n\n'
        'As etapas F0–F4 estão incorporadas aos critérios: efeitos/ordem superior na fase 1, '
        'vidas/dados/capturas na fase 2, iteradores na fase 3 e efeitos externos/TCO nas fases 4/5; '
        'não recebem pontos em duplicidade. O crédito de ownership das APIs funcionais pertence à fase 2; '
        'a alpha.6 integra F1 para coleções escalares/funções pure. Uma fase com mecanismos completos não certifica produção.\n\n'
        '| Fase | Peso | Atendimento dos critérios | Pontos obtidos |\n'
        '| --- | ---: | ---: | ---: |\n')
for phase, (fraction, points) in zip(data['phases'], phases):
    text += f'| {phase["id"]} — {phase["name"]} | {phase["weight"]} | {rounded(fraction*100)}% | {str(points).replace(".", ",")} |\n'
text += f'| **Total** | **100** | **{rounded(total)}% estimados** | **{str(total).replace(".", ",")}** |\n'
text += '\n## Histórico pela mesma régua\n\n| Versão | Estimativa | Observação |\n| --- | ---: | --- |\n'
for record in data['history']:
    assert set(record['overrides']) == set(identities), 'Cada histórico deve congelar os 35 estados'
    old, _ = score(record['overrides'])
    note = 'Reconstrução retrospectiva; não era um número publicado na entrega' if record['retrospective'] else 'Avaliação desta entrega'
    label = record['version'] + (' — ' + record['milestone'] if record.get('milestone') else '')
    text += f'| {label} | {rounded(old)}% ({str(old).replace(".", ",")} pontos) | {note} |\n'
text += '\nCada registro histórico congela seus 35 estados; atualizações futuras não alteram retroativamente esses estados.\n\n## Evidência por critério\n'
for phase in data['phases']:
    text += f'\n### Fase {phase["id"]} — {phase["name"]}\n\n| Critério | Estado | Evidência e limites |\n| --- | --- | --- |\n'
    for item in phase['items']:
        assert (ROOT / 'docs' / item['evidence']).is_file(), item['evidence']
        note = (' — ' + item['notes']) if item.get('notes') else ''
        text += f'| {item["id"]} — {item["name"]} | {labels[item["status"]]} | [Documento]({item["evidence"]}){note} |\n'
text += ('\nA evidência vinculada também descreve limites, inclusive para critérios pendentes. '
         'A base de bibliotecas, distribuição, vidas explícitas, recursos compostos, fatias/texto gerenciado, valores Copy/variantes e a aplicação A delimitada já existe; '
         'a emissão integral por IR e o aceite independente foram concluídos nesta continuação; os novos alvos concentram o restante técnico. As 24 horas reais Windows/Linux da alpha.15 estão registradas no handoff e na validação JSON. Variantes Move/capturas verificadas e pipelines com ambientes foram acrescentados na alpha.13. As aplicações B/C delimitadas e a ABI C escalar foram acrescentadas na alpha.11; a alpha.12 torna safe padrão, acrescenta rede cooperativa e inventário por ligação real. '
         'A licença foi escolhida pelo responsável; direitos de imagens e revisão de distribuição permanecem abertos; o inventário técnico dos binários está documentado.\n\n'
         'Fonte auditável: [PROGRESSO.json](PROGRESSO.json). Gerar com `python tools/report-progress.py`; '
         'verificar com `python tools/report-progress.py --check`. Relatórios históricos de versões anteriores '
         'permanecem preservados; a porcentagem começa a ser publicada na alpha.5.\n')
output = ROOT / 'docs/PROGRESSO.md'
if args.check:
    assert output.read_text(encoding='utf-8') == text, 'Regere docs/PROGRESSO.md a partir de PROGRESSO.json'
else:
    output.write_text(text, encoding='utf-8', newline='\n')
print(f'AssisScript {data["version"]}: conclusão estimada {rounded(total)}% ({total}/100 pontos)')
