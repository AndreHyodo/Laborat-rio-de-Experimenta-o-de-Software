# Análise dos Dados de Repositórios Populares do GitHub

## 1. Introdução e Hipóteses

Neste estudo, analisamos repositórios populares do GitHub para responder questões relacionadas à contribuição externa, número de releases e frequência de atualização, especialmente em relação às linguagens de programação utilizadas. Hipotetizamos que repositórios escritos em linguagens populares tendem a receber mais contribuições externas, lançar mais releases e serem atualizados com maior frequência do que repositórios em outras linguagens.

## 2. Metodologia

- Coletamos dados de 1000 repositórios mais populares do GitHub (com mais de 10.000 estrelas) usando a API REST e GraphQL.
- Para cada repositório, extraímos: idade, PRs aceitos, total de releases, tempo desde a última atualização, linguagem primária e percentual de issues fechadas.
- Os dados foram processados e sumarizados por linguagem, com foco nas linguagens populares (Python, JavaScript, TypeScript, Java, C#, C++, PHP, Shell, C, Go).
- Para cada métrica, calculamos valores medianos, além de contagem de repositórios por linguagem.

## 3. Resultados

### 3.1. Contagem por Categoria (Linguagem de Programação)

- Python: 187 repositórios
- JavaScript: 130
- TypeScript: 156
- Java: 50
- C#: 12
- C++: 48
- PHP: 7
- Shell: 19
- C: 25
- Go: 73
- Outras linguagens: 293

### 3.2. Valores Medianos por Linguagem Popular

| Linguagem   | PRs Aceitos (Mediana) | Releases (Mediana) | Última Atualização (Mediana) |
|-------------|-----------------------|--------------------|------------------------------|
| Python      | 548                   | 22                 | 1.0 horas                    |
| JavaScript  | 533.5                 | 33                 | 3.0 horas                    |
| TypeScript  | 2103.5                | 146.5              | 1.0 horas                    |
| Java        | 645                   | 42.5               | 3.0 horas                    |
| C#          | 2780.5                | 100                | 0.5 horas                    |
| C++         | 932                   | 58                 | 1.0 horas                    |
| PHP         | 2944                  | 346                | 0.0 horas                    |
| Shell       | 437                   | 2                  | 4.0 horas                    |
| C           | 113                   | 32                 | 0.0 horas                    |
| Go          | 1677                  | 124                | 2.0 horas                    |

### 3.3. Valores Medianos Gerais

- Mediana de PRs aceitos (todas as linguagens populares): varia de 113 (C) a 2944 (PHP).
- Mediana de releases: varia de 2 (Shell) a 346 (PHP).
- Mediana do tempo desde a última atualização: a maioria das linguagens populares tem valores baixos (0 a 4 horas), indicando alta frequência de atualização.

## 4. Discussão

### Hipóteses e Expectativas

Esperávamos que repositórios em linguagens populares apresentassem:
- Mais contribuições externas (PRs aceitos)
- Mais releases
- Atualizações mais frequentes

### Análise dos Resultados

- As linguagens populares realmente concentram a maior parte dos repositórios analisados.
- PHP, TypeScript, C# e Go apresentam valores medianos de PRs aceitos e releases bastante elevados, sugerindo que grandes projetos nessas linguagens recebem muitas contribuições e lançam releases com frequência.
- O tempo mediano desde a última atualização é baixo para quase todas as linguagens populares, indicando que esses projetos são mantidos ativamente.
- Linguagens menos populares ou "outras" tendem a ter menos repositórios e, em geral, valores medianos menores para PRs aceitos e releases.

### Considerações

- Os resultados confirmam parcialmente as hipóteses: linguagens populares concentram projetos com mais atividade e manutenção.
- Entretanto, há variação significativa entre as linguagens populares (ex: Shell e C têm valores medianos bem menores).
- A amostra pode ser enviesada por projetos muito grandes em certas linguagens (ex: PHP com poucos, mas enormes projetos).
- O tempo desde a última atualização é baixo para quase todos, pois os repositórios populares tendem a ser muito ativos.
