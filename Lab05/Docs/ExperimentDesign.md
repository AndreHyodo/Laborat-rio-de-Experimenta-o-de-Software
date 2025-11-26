# Lab05 — Desenho e Preparação do Experimento (GraphQL vs REST)

Este documento descreve o desenho (Passo 1) e a preparação (Passo 2) do experimento controlado para comparar GraphQL e REST.

## 1. Desenho do Experimento

### A. Hipóteses

- H0-RQ1 (nula): A latência média das respostas GraphQL é igual à das respostas REST.
- H1-RQ1 (alternativa): A latência média das respostas GraphQL é menor que a das respostas REST.
- H0-RQ2 (nula): O tamanho médio das respostas GraphQL é igual ao das respostas REST.
- H1-RQ2 (alternativa): O tamanho médio das respostas GraphQL é menor que o das respostas REST.

### B. Variáveis Dependentes

- Latência por requisição (ms): tempo entre envio e recebimento da resposta.
- Tamanho do payload da resposta (bytes): tamanho bruto recebido por requisição.

### C. Variáveis Independentes

- Estilo da API: GraphQL vs REST (fator com 2 níveis).
- Consulta/endpoint avaliado: p.ex., detalhes de usuário, lista de usuários, etc.

### D. Tratamentos

- Tratamento 1: Requisições REST aos endpoints definidos.
- Tratamento 2: Requisições GraphQL às queries equivalentes (mesmo conteúdo semântico).

### E. Objetos Experimentais

- API de teste: Uma aplicação que oferece tanto endpoints REST quanto uma interface GraphQL com queries equivalentes.
- Cenários de teste:
  - REST: `/users/1` , `/users` , `/products` , `/products/1` , `/orders/1`
  - GraphQL: `user(id: 1) { id name email }` , `users { id name }` , `products { id name price }` , etc.

### F. Tipo de Projeto Experimental

- **Projeto intra-sujeitos (medidas repetidas):** o mesmo ambiente executa ambos os tratamentos.
- **Ordem de execução randômica** para reduzir viés de ordem (REST/GraphQL ou GraphQL/REST).
- **Número de medições por consulta:** 50 repetições por consulta/tratamento para garantir significância estatística.
- **Análise estatística planejada:** Teste t de Student para amostras pareadas (se os dados seguirem distribuição normal) ou teste de Wilcoxon (se não paramétrico).

### G. Ameaças à Validade

- Interna:
  - Ruído de rede, variação de carga do servidor/cliente
  - Cache aquecido vs frio
  - Mitigação: aquecer cache com requisições iniciais; intervalos fixos entre requisições; ordem aleatória; ambiente controlado
- Externa:
  - Generalização para outras APIs e cenários
  - Esquema/shape de dados diferentes
  - Mitigação: testar múltiplas consultas com perfis distintos (detalhe vs lista), registrar contexto da API
- Construto:
  - Equivalência semântica entre endpoint REST e query GraphQL
  - Mitigação: validar que os campos retornados são comparáveis em conteúdo
- Conclusão:
  - Tamanho amostral insuficiente
  - Pressupostos estatísticos violados
  - Mitigação: usar verificação de normalidade; aplicar testes não-paramétricos se necessário; aumentar repetições

---

## 2. Preparação do Experimento

### Ferramentas e Bibliotecas

- Python 3.10+.
- Requisições HTTP: `requests` (REST) e `gql` (GraphQL, com transport via `requests`).
- Manipulação/Análise: `pandas`, `numpy` (para etapas posteriores de análise).
- Configuração: `pyyaml` para definir endpoints/queries e parâmetros do benchmark.

### Organização dos Arquivos (Lab05)

- `Code/requirements.txt`: dependências do experimento.
- `Code/config.example.yaml`: exemplo de configuração editável.
- `Code/rest_client.py`: cliente REST que mede latência e tamanho do payload.
- `Code/graphql_client.py`: cliente GraphQL que mede latência e tamanho do payload.
- `Code/benchmark_runner.py`: orquestra os trials, grava CSVs em `Lab05/Data/`.

### Parametrização

- Número de repetições por consulta/tratamento (e.g., `trials: 30`).
- Pausa entre requisições (e.g., `sleep_between_ms: 100`).
- Aleatorização da ordem dos tratamentos.
- Timeouts e cabeçalhos opcionais (e.g., Authorization).

### Métricas Registradas por Requisição

- `trial_id`, `type` (REST|GraphQL), `label`/`name`, `url`/`query`, `latency_ms`, `payload_bytes`, `status_code`, `timestamp_start`, `timestamp_end`, `error`.

### Como Executar (após configurar URLs/queries)

1) Instale dependências: `pip install -r Lab05/Code/requirements.txt`
2) Copie `Code/config.example.yaml` para `Code/config.yaml` e ajuste os valores.
3) Rode: `python Lab05/Code/benchmark_runner.py --config Lab05/Code/config.yaml`
4) Saídas: `Lab05/Data/rest_results.csv` e `Lab05/Data/graphql_results.csv`.
