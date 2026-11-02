# Diagnóstico — Explore; correção autorizada — Build

Use para investigar bug, falha de teste, timeout ou comportamento inesperado.
Aplica-se o [contrato de invocação](invocation.md). Diferencie “diagnostique” de
“corrija”: o segundo inclui implementação e validação no escopo solicitado.

## Procedimento

**Entrada:** sintoma, esperado e fontes. **Decisão:** próxima observação que distingue
as causas. **Evidência:** reprodução ou limite explícito. **Saída:** causa sustentada,
hipóteses restantes e próxima ação; correção somente no escopo autorizado.

1. Delimite sintoma, resultado esperado, versão/ambiente, frequência e impacto.
   Consulte código, testes, logs sanitizados e mudanças relevantes antes de
   solicitar informações ausentes. Não exponha segredos ou transcrições privadas.
2. Busque reprodução mínima nas ferramentas autorizadas. Se não puder reproduzir,
   registre a limitação; evidência estática pode sustentar uma hipótese sem provar
   causalidade em produção. Separe fatos, hipóteses e tentativas descartadas.
3. Use [Cognitive Principles](cognitive.md) para hipótese ambígua ou decisão
   material. Escolha a próxima observação que distingue as hipóteses; não aplique
   sucessivas mudanças especulativas. Considere carga, ordem concorrente, timeout,
   saturação e falha parcial quando o caminho afetado justificar.
4. Após mutação de resultado incerto, consulte estado por identidade estável antes
   de repetir qualquer efeito. Timeout não prova falha remota; cancelamento local
   não prova rollback. Sem observação suficiente, reporte resultado incerto e
   bloqueie somente a operação dependente, conforme [Workflows](workflow.md).
5. Se a correção estiver autorizada e houver evidência suficiente, use
   [Build](build.md) para mudança mínima e regressão que distinga antes/depois.
   Caso contrário, entregue diagnóstico e proposta delimitada. Após duas
   tentativas sem progresso, reúna reprodução, evidências e hipóteses descartadas
   antes de aplicar recuperação/escalada conforme a política efetiva do host.

## Entrega e limite

Entregue sintoma, causa sustentada ou hipóteses restantes, evidência discriminante,
resultado das verificações e próxima ação. Se corrigido, inclua arquivos e regressão
validada. Se apenas diagnosticado, declare que o código não foi alterado. Um
diagnóstico inconclusivo com evidência útil não deve virar alegação de bug resolvido.

Exemplo: “NEXUS debug: timeout após enviar job; só diagnostique.” Correlacione envio
e aceite remoto; mantenha incerteza onde faltar evidência, sem reenviar o job.
