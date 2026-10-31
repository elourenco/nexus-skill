# Testes, modelos e contexto

## Testes adaptativos

| Mudança | Verificação proporcional |
| --- | --- |
| Texto, documentação ou estilo reversível | Revisão e validação estrutural/visual pertinente |
| Bug de comportamento | Reprodução e regressão que distinga antes/depois |
| Regra de negócio ou contrato | Casos de sucesso, fronteira e erro observável |
| Concorrência, autorização, pagamentos ou perda de dados | Testes das invariantes afetadas antes da implementação, quando viável; recuperação e idempotência conforme o risco real |

TDD é uma técnica preferencial para invariantes críticas, não uma exigência universal. Políticas mais específicas do projeto prevalecem. Não escreva testes que apenas espelhem a implementação. Não amplie a suíte sem mudança, falha ou dúvida concreta que justifique o custo.

Para alterações de performance, compare cargas equivalentes e registre ambiente, tamanho da amostra, latência e throughput observados. Sem medição, descreva a hipótese. Quando aplicável, cubra saturação, timeout, cancelamento e backpressure.

## Roteamento

Separe papel, provider, modelo e esforço. Use a política explícita do usuário/projeto; na ausência dela, selecione pela capacidade requerida e disponibilidade verificada, sem assumir que preço acompanha qualidade.

| Trabalho | Critério |
| --- | --- |
| Mecânico e inteiramente especificado | Modelo suficiente com baixo custo/latência |
| Implementação e plano comuns | Capacidade de código e raciocínio intermediária |
| Integração, migração ou incerteza relevante | Mais capacidade e contexto delimitado |
| Mudança difícil de reverter ou risco material | Review independente e capacidade adequada ao risco |

Escalar não resolve credencial inválida, ambiente quebrado ou contexto ausente. Não simule troca de modelo do agente principal. Informe modelo/esforço efetivos quando houver escalada ou fallback relevante. Acesso por assinatura não implica acesso por API.

## Economia de contexto

- Procure símbolos, contratos e arquivos relevantes antes de ler módulos inteiros.
- Delegue objetivo, fontes, ownership, restrições e aceite; evite reenviar histórico completo.
- Reutilize evidências ainda válidas; revalide estado mutável antes de ações relevantes.
- Defina limites de tentativas e concorrência; respeite budgets fornecidos. Não invente orçamento numérico.
- Registre tokens/custos apenas quando medidos pelo host/provider, com unidade e origem. Dado indisponível não é zero.
- Sem medição ou controle de consumo no host, declare que não consegue garantir um teto monetário; não prometa execução dentro desse teto.
