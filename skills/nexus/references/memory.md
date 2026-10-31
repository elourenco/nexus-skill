# Memória com proveniência

Memória é contexto recuperável, não fonte de verdade automática. Confira contratos e código atuais antes de usar informação histórica para uma decisão relevante.

| Camada | Conteúdo | Local proposto no consumidor |
| --- | --- | --- |
| Working | Próxima ação e impedimentos da tarefa | `.nexus/local/` ou estado nativo do host |
| Project | Decisões e conhecimento validado | `docs/nexus/decisions/` e `docs/nexus/memory/` |
| Shared | Padrões sanitizados aprovados para reutilização | Local explicitamente escolhido pelo usuário |

Antes de usar `.nexus/local/`, assegure sua exclusão do controle de versão no projeto consumidor. Não crie memória global nem copie conteúdo entre projetos sem autorização. Respeite a política do host sobre quando gravar memória.

Use [registro de memória](../assets/templates/memory.md) com fonte, data, escopo, confiança, condição de revalidação e status. Preserve distinção entre decisão, hipótese e observação. Se informação for contradita, marque-a como substituída e referencie a nova evidência.

Recupere apenas registros relevantes. Não registre credenciais, dados pessoais desnecessários ou logs integrais. Sem mecanismo de persistência disponível, apresente o registro ao usuário e declare que não foi salvo. Não há índice, busca semântica ou expiração automática nesta fase.
