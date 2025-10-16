# Laboratório 03 - Caracterizando a Atividade de Code Review no GitHub

**Disciplina:** Laboratório de Experimentação de Software  
**Data:** Outubro 2025  
**Objetivo:** Analisar a atividade de code review em repositórios populares do GitHub

---

## 1. Introdução

### 1.1 Contextualização

A prática de code review tornou-se fundamental nos processos de desenvolvimento ágil moderno. Esta atividade consiste na interação sistemática entre desenvolvedores e revisores com o objetivo de inspecionar o código produzido antes de sua integração à base principal do projeto. Através desta prática, busca-se garantir a qualidade do código integrado, prevenir a inclusão de defeitos e promover o compartilhamento de conhecimento entre os membros da equipe.

No contexto de sistemas open source, particularmente aqueles desenvolvidos através da plataforma GitHub, as atividades de code review ocorrem mediante a avaliação de contribuições submetidas através de Pull Requests (PRs). Este mecanismo requer que, para integrar código na branch principal, seja realizada uma solicitação de pull que será avaliada, discutida e, ao final, aprovada ou rejeitada por colaboradores do projeto.

### 1.2 Motivação

Compreender os fatores que influenciam o sucesso ou fracasso de um Pull Request é crucial para desenvolvedores que contribuem para projetos open source. Além disso, identificar padrões nas atividades de code review pode fornecer insights valiosos sobre melhores práticas de desenvolvimento colaborativo e fatores que promovem uma colaboração mais efetiva.

### 1.3 Objetivo

O objetivo deste laboratório é analisar sistematicamente a atividade de code review desenvolvida em repositórios populares do GitHub, identificando variáveis que influenciam no merge de um PR, sob a perspectiva de desenvolvedores que submetem código aos repositórios selecionados.

## 2. Hipóteses Iniciais

Com base na literatura existente e na experiência prática em desenvolvimento de software, formulamos as seguintes hipóteses informais para orientar nossa análise:

### 2.1 Hipóteses sobre o Feedback Final (Status do PR)

**H1 - Tamanho dos PRs:** Esperamos que PRs menores (menos arquivos modificados e menos linhas alteradas) tenham maior probabilidade de serem aceitos (merged). PRs grandes podem ser mais difíceis de revisar e compreender, resultando em maior taxa de rejeição.

**H2 - Tempo de Análise:** Antecipamos que PRs que levam muito tempo para serem analisados podem ter maior probabilidade de serem fechados sem merge, possivelmente devido a conflitos que surgem ao longo do tempo ou perda de interesse dos mantenedores.

**H3 - Qualidade da Descrição:** Esperamos que PRs com descrições mais detalhadas e bem estruturadas tenham maior probabilidade de serem aceitos, pois facilitam a compreensão do revisor sobre as mudanças propostas.

**H4 - Nível de Interação:** Acreditamos que um número moderado de interações (comentários e participantes) pode estar associado a maior taxa de aceitação, indicando engajamento construtivo. No entanto, muitas interações podem indicar problemas ou controvérsias que dificultam a aceitação.

### 2.2 Hipóteses sobre o Número de Revisões

**H5 - Tamanho vs Revisões:** Esperamos uma correlação positiva entre o tamanho dos PRs e o número de revisões necessárias, uma vez que mudanças maiores tendem a requerer mais ciclos de revisão.

**H6 - Tempo vs Revisões:** Antecipamos que PRs com mais revisões tendem a levar mais tempo para serem finalizados, devido aos ciclos iterativos de feedback e correção.

**H7 - Descrição vs Revisões:** Esperamos que PRs com descrições mais detalhadas possam necessitar de menos revisões, pois fornecem contexto suficiente para uma avaliação mais eficiente.

**H8 - Interações vs Revisões:** Prevemos uma correlação positiva forte entre o número de revisões e outras formas de interação (comentários, participantes), uma vez que revisões frequentemente geram discussões.

## 3. Metodologia

### 3.1 Coleta de Dados

#### 3.1.1 Critérios de Seleção de Repositórios

O dataset utilizado neste laboratório é composto por Pull Requests submetidos a repositórios que atendem aos seguintes critérios:

- **Popularidade:** Selecionamos os 200 repositórios mais populares do GitHub (baseado em número de estrelas)
- **Linguagem:** Focamos em repositórios Python para homogeneidade da análise
- **Atividade:** Repositórios devem possuir pelo menos 100 PRs no estado MERGED ou CLOSED

#### 3.1.2 Critérios de Seleção de Pull Requests

Para garantir que analisamos PRs que passaram por processo genuíno de code review, aplicamos os seguintes filtros:

- **Status:** Apenas PRs com status MERGED ou CLOSED
- **Revisões:** PRs devem possuir pelo menos uma revisão formal
- **Tempo mínimo:** Diferença entre criação e finalização (merge/close) deve ser superior a 1 hora, para excluir PRs processados automaticamente por bots ou CI/CD

#### 3.1.3 Processo de Coleta

A coleta de dados é realizada através da API REST do GitHub, utilizando as seguintes estratégias:

1. **Busca de Repositórios:** Utilização da API de busca para identificar repositórios populares
2. **Extração de PRs:** Para cada repositório, coleta de PRs fechados ordenados por data de atualização
3. **Detalhamento:** Para cada PR válido, coleta de informações detalhadas incluindo:
   - Dados básicos (título, descrição, datas, autor)
   - Métricas de código (arquivos modificados, linhas adicionadas/removidas)
   - Informações de interação (revisões, comentários, participantes)

### 3.2 Definição de Métricas

Para cada dimensão de análise, definimos métricas específicas conforme especificado no laboratório:

#### 3.2.1 Tamanho dos PRs
- **Número de arquivos modificados:** Total de arquivos alterados no PR
- **Linhas adicionadas:** Quantidade de linhas de código adicionadas
- **Linhas removidas:** Quantidade de linhas de código removidas
- **Total de mudanças:** Soma de linhas adicionadas e removidas

#### 3.2.2 Tempo de Análise
- **Tempo em horas:** Intervalo entre criação do PR e última atividade (fechamento ou merge)
- **Tempo em dias:** Conversão do tempo em horas para dias para melhor interpretação

#### 3.2.3 Descrição dos PRs
- **Comprimento da descrição:** Número de caracteres no corpo da descrição (markdown)
- **Número de palavras:** Contagem de palavras na descrição
- **Comprimento do título:** Número de caracteres no título do PR

#### 3.2.4 Interações
- **Número de participantes:** Contagem de usuários únicos que interagiram no PR
- **Número de comentários:** Total de comentários (review comments + issue comments)
- **Número de revisões:** Quantidade de revisões formais realizadas

### 3.3 Questões de Pesquisa

As análises são organizadas em duas dimensões principais:

#### 3.3.1 Feedback Final das Revisões (Status do PR)
- **RQ01:** Qual a relação entre o tamanho dos PRs e o feedback final das revisões?
- **RQ02:** Qual a relação entre o tempo de análise dos PRs e o feedback final das revisões?
- **RQ03:** Qual a relação entre a descrição dos PRs e o feedback final das revisões?
- **RQ04:** Qual a relação entre as interações nos PRs e o feedback final das revisões?

#### 3.3.2 Número de Revisões
- **RQ05:** Qual a relação entre o tamanho dos PRs e o número de revisões realizadas?
- **RQ06:** Qual a relação entre o tempo de análise dos PRs e o número de revisões realizadas?
- **RQ07:** Qual a relação entre a descrição dos PRs e o número de revisões realizadas?
- **RQ08:** Qual a relação entre as interações nos PRs e o número de revisões realizadas?

### 3.4 Análise Estatística

#### 3.4.1 Testes para Comparação de Grupos (RQ01-RQ04)

Para analisar as relações entre as métricas e o feedback final (MERGED vs CLOSED), utilizamos:

- **Teste t de Student:** Aplicado quando os dados seguem distribuição normal
- **Teste Mann-Whitney U:** Utilizado quando os dados não seguem distribuição normal (teste não-paramétrico)

A escolha entre os testes é feita com base na verificação de normalidade através do teste de Shapiro-Wilk.

#### 3.4.2 Testes de Correlação (RQ05-RQ08)

Para analisar as correlações entre métricas e número de revisões, utilizamos:

- **Correlação de Pearson:** Mede correlação linear, assumindo normalidade e homocedasticidade
- **Correlação de Spearman:** Mede correlação monotônica, não assumindo distribuição específica

A escolha do teste recomendado é baseada na comparação entre os coeficientes obtidos e características dos dados.

#### 3.4.3 Nível de Significância

- **Alpha = 0.05:** Nível de significância adotado para todos os testes estatísticos
- **Interpretação do p-valor:** p < 0.05 indica resultado estatisticamente significativo

#### 3.4.4 Tamanho do Efeito

Para contextualizar a significância estatística, calculamos o tamanho do efeito:

- **Cohen's d:** Para testes t (< 0.2 pequeno, 0.2-0.5 médio, > 0.5 grande)
- **r de efeito:** Para Mann-Whitney U (< 0.1 pequeno, 0.1-0.3 médio, > 0.3 grande)
- **Coeficientes de correlação:** Interpretação padrão (< 0.3 fraca, 0.3-0.7 moderada, > 0.7 forte)

### 3.5 Justificativa da Escolha dos Testes Estatísticos

#### 3.5.1 Comparação de Grupos (MERGED vs CLOSED)

A escolha entre teste t e Mann-Whitney U é fundamentada em:

1. **Robustez:** Testes não-paramétricos são mais robustos para dados que não seguem distribuição normal
2. **Natureza dos dados:** Métricas de software frequentemente apresentam distribuições assimétricas
3. **Tamanho da amostra:** Para amostras grandes, testes não-paramétricos são preferíveis

#### 3.5.2 Análise de Correlação

A utilização de ambos os testes de correlação permite:

1. **Pearson:** Detectar relações lineares diretas
2. **Spearman:** Identificar relações monotônicas que podem não ser lineares
3. **Comparação:** A diferença entre os coeficientes indica o tipo de relação presente

## 4. Implementação

### 4.1 Arquitetura do Sistema

O sistema foi implementado em Python utilizando uma arquitetura modular:

```
Lab03/
├── Code/
│   ├── main.py                    # Orquestração principal
│   ├── github_collector.py        # Coleta de dados via API GitHub
│   ├── metrics_calculator.py      # Cálculo de métricas
│   ├── statistical_analyzer.py    # Análises estatísticas
│   ├── data_visualizer.py        # Geração de visualizações
│   └── requirements.txt           # Dependências
├── Data/                          # Dados coletados
└── Results/                       # Resultados e relatórios
```

### 4.2 Tecnologias Utilizadas

- **Python 3.8+:** Linguagem principal
- **Pandas:** Manipulação e análise de dados
- **SciPy:** Testes estatísticos
- **Matplotlib/Seaborn:** Visualizações
- **Requests:** Comunicação com API GitHub

### 4.3 Configuração e Execução

Para executar o laboratório:

1. **Configurar token GitHub:** `export GIT_TOKEN=your_token_here`
2. **Instalar dependências:** `pip install -r requirements.txt`
3. **Executar coleta:** `python main.py --phase collect --repos-limit 50 --min-prs 50`
4. **Executar análise:** `python main.py --phase analyze`
5. **Gerar visualizações:** `python main.py --phase visualize`

## 5. Resultados Esperados

### 5.1 Estrutura dos Resultados

Os resultados serão organizados da seguinte forma:

1. **Análises Descritivas:** Estatísticas resumidas do dataset coletado
2. **Questões de Pesquisa:** Resultados detalhados para cada RQ
3. **Visualizações:** Gráficos e plots para suporte às análises
4. **Interpretações:** Discussão dos resultados em relação às hipóteses

### 5.2 Métricas de Validação

- **Qualidade dos dados:** Percentual de dados faltantes e outliers
- **Representatividade:** Distribuição dos repositórios e PRs coletados
- **Confiabilidade:** Intervalos de confiança e significância estatística

## 6. Discussão Preliminar

### 6.1 Limitações Esperadas

1. **Rate Limiting:** Limitações da API GitHub podem afetar a coleta
2. **Viés de seleção:** Foco em repositórios Python pode não ser generalizable
3. **Temporal:** Análise limitada a um período específico

### 6.2 Validade dos Resultados

- **Validade interna:** Controle de variáveis confundidoras através de critérios rigorosos
- **Validade externa:** Generalização limitada aos contextos similares
- **Validade estatística:** Uso de testes apropriados e correção para múltiplas comparações

## 7. Cronograma de Execução

1. **Semana 1:** Implementação e teste dos coletores de dados
2. **Semana 2:** Coleta de dados dos repositórios selecionados
3. **Semana 3:** Cálculo de métricas e análises estatísticas
4. **Semana 4:** Geração de visualizações e finalização do relatório

## 8. Próximos Passos

1. **Execução da coleta de dados** com um subset pequeno para validação
2. **Refinamento dos critérios** baseado nos resultados iniciais
3. **Coleta completa** dos dados conforme metodologia definida
4. **Análise estatística** e geração dos resultados finais
5. **Discussão e interpretação** dos resultados obtidos

---

**Nota:** Este documento representa a primeira versão do relatório, contendo as hipóteses iniciais e metodologia. Os resultados empíricos serão adicionados após a coleta e análise dos dados.