# Desenvolvimento do NEXUS

- Esta fase entrega uma skill documental. Runtime, dashboard e adapters exigem escopo próprio.
- A fonte de verdade do pacote é `skills/nexus/`. Mantenha o ponto de entrada curto e referências sob demanda.
- Não adicionar frameworks, serviços, dependências ou diretórios vazios sem consumidor real.
- Mudanças devem considerar latência, throughput, concorrência e recuperação proporcionalmente ao comportamento alterado; não inventar medições.
- Preserve instruções do host e autorizações do usuário. A skill não concede permissão para commit, push, merge, deploy ou ações externas.
- Não fixar modelos e preços globais no conteúdo portátil. Respeitar a política do usuário e as capacidades verificadas do runtime.
- Executar `python3 scripts/validate.py` antes de concluir alterações. Para alterações comportamentais, registrar cenários e resultados; validação estrutural não substitui avaliação prática.
- Nunca registrar segredos, transcrições privadas ou dados de projetos consumidores em exemplos versionados.
