# Fluxo guiado do nexus-brainstorming

**Objetivo e escopo aprovado:** iniciar por brainstorming e continuar por aceites
em linguagem natural, sem novas invocações. Antes de implementar, oferecer
subagentes (sessão ativa orquestra, contexto novo por tarefa quando disponível)
ou agente único. Não criar runtime, chats visíveis, stores ou permissões externas.

**Arquitetura:** contratos textuais em `skills/nexus/references/`; a entrada irmã
apenas seleciona o procedimento. Sem alteração de schemas, helpers ou dependências.
O pedido explícito de somente explorar/planejar e autorizações existentes prevalecem.

**Validação:** aplicação por agentes consumidores em cenários sintéticos antes e
depois, inspeção das respostas e review independente. Checks estruturais e suíte
Python complementam a avaliação; não provam aderência geral nem integração em hosts.

## Tarefas

- [x] Registrar baseline: entrada genérica e continuidade após aceite de plano.
- [x] Alterar brainstorming/invocação/plan/build/agentes e alinhar núcleo/entrada:
  solução → aceite para planejar → plano e escolha de execução → aceite para
  implementar → validação/review → entrega. Um aceite só vale para alvo/efeitos
  apresentados; mudança material reabre somente a decisão afetada.
- [x] Documentar uso no README preservando alterações pré-existentes de release.
- [x] Avaliar início, aceites, restrições explícitas, métodos, fallback, dúvidas
  entre worker/orquestrador e recuperação sem despacho duplicado; registrar
  cenários, respostas observadas e limitações em documento de validação.
- [x] Executar `python3 scripts/validate.py` e a suíte `unittest` do projeto;
  obter review independente do diff e corrigir achados pertinentes.

## Recursos e falhas

O agente principal edita os contratos; avaliadores e reviewer são somente leitura.
No comportamento orientado pela skill, paralelismo exige ownership e recursos
isolados; contexto novo não isola filesystem, banco ou portas. Dúvidas dos workers
voltam ao orquestrador; decisão material do usuário bloqueia só a ação dependente.
Agente único não satisfaz por si só gate de review independente. Sem suporte real,
informar a limitação e obter escolha do fallback antes do despacho dependente.

## Progresso

Plano registrado após aprovação do comportamento e autorização de implementação
e validação pelo usuário. Execução local pelo agente principal, com avaliações e
review delegados; sem commit, push ou instalação em caches.

Resultado: baseline de dois consumidores, avaliação pós-edição de três consumidores
e review independente APPROVED. Suíte de 202 testes aprovada. Cenários observados,
ajustes de clareza e limites em [validação](../../guided-brainstorming-validation.md).
