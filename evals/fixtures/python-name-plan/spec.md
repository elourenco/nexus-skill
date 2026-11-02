# SPEC-NAMES — revisão 1 — aprovada

Preservar normalize_name(value): value.strip(), somente strings.
Adicionar normalize_names(values): aceitar somente list de strings e retornar
nova list com os valores normalizados, na mesma ordem. Não mutar a entrada.
Lista vazia retorna []; coleção inválida ou item não string lança TypeError.
Não há retorno parcial em caso de erro. Não adicionar dependências.
