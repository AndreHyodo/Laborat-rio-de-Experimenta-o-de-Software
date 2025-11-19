# Lab05 — Resultados do Experimento (GraphQL vs REST)

Este relatório resume os resultados coletados para responder:

- RQ1: Respostas GraphQL são mais rápidas que respostas REST?
- RQ2: Respostas GraphQL têm tamanho menor que respostas REST?

## Cenário e Configuração

- API: GitHub (REST e GraphQL) para consultas equivalentes.
- Consultas/Endpoints:
  - Detalhe de usuário
    - REST: `/users/octocat`
    - GraphQL: `user(login: "octocat") { login name id }`
  - Repositórios do usuário (até 100)
    - REST: `/users/octocat/repos?per_page=100`
    - GraphQL: `user(login: "octocat") { repositories(first: 100, privacy: PUBLIC) { nodes { name id } } }`
- Execução: 5 trials por consulta/tratamento, pausa ~100 ms entre requisições.
- Métricas: `latency_ms`, `payload_bytes` e `status_code`.
- Arquivos: `Lab05/Data/rest_results.csv` e `Lab05/Data/graphql_results.csv` (apenas status 200 considerados).

## Resumo dos Resultados (medianas)

- Detalhe de usuário (`user_detail`):
  - Latência: REST ≈ 822.5 ms | GraphQL ≈ 875.5 ms → REST mais rápido (~6%).
  - Tamanho do payload: REST ≈ 1,232 bytes | GraphQL ≈ 83 bytes → GraphQL menor (~93%).
- Lista de repositórios (`user_repos`):
  - Latência: REST ≈ 913.1 ms | GraphQL ≈ 2,047.6 ms → REST mais rápido (~55%).
  - Tamanho do payload: REST ≈ 41,289 bytes | GraphQL ≈ 6,837 bytes → GraphQL menor (~83%).

## Interpretação

- RQ1 (latência): neste dataset, REST foi mais rápido em ambas as consultas.
  - user_detail: diferença pequena (≈ 53 ms em mediana).
  - user_repos: diferença grande (≈ 1.13 s), com REST mais rápido.
- RQ2 (tamanho): GraphQL retornou respostas substancialmente menores em ambos os casos (≈ 93% e ≈ 83% menores).

## Conclusão (amostra atual)

- RQ1: Não suporte à hipótese de GraphQL ser mais rápido; REST foi mais rápido aqui.
- RQ2: Suporte à hipótese; GraphQL entregou payloads menores que REST.

## Limitações e Ameaças à Validade

- Amostra pequena (5 repetições por consulta) e rede pública (variação de latência).
- Possível influência de cache (cliente/servidor/CDN) e rate limiting (exigiu token e cabeçalhos adequados).
- Equivalência semântica: as consultas foram mantidas comparáveis, mas a estrutura de resposta difere por natureza (GraphQL retorna apenas os campos solicitados).

## Próximos Passos

- Aumentar `trials` (ex.: 30–50) e repetir em horários diferentes; considerar warm-up e backoff.
- Verificar normalidade; aplicar testes estatísticos adequados (ex.: Mann–Whitney) por consulta.
- Gerar gráficos (boxplot/violin) para latência e payload por tratamento e por consulta.
- Avaliar cenários com paginação/tamanhos de resposta diferentes e concorrência controlada.

## Reprodutibilidade

- Reexecutar com:
  - `python Lab05/Code/benchmark_runner.py --config Lab05/Code/config.yaml`
- Arquivos de saída: `Lab05/Data/rest_results.csv`, `Lab05/Data/graphql_results.csv`.
- O runner adiciona `User-Agent` e aceita variáveis de ambiente no `config.yaml` (ex.: `${GITHUB_TOKEN}`).
