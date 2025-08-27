import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Carregar dados
df = pd.read_csv("../resultado.csv", delimiter=",", encoding="utf-8")

# Preparo dos dados

# Extrai valor numérico (dias ou horas) da coluna de atualização
def extrai_dias_ou_horas(valor):
    if isinstance(valor, str):
        if 'dias' in valor:
            return float(valor.split()[0])
        elif 'horas' in valor:
            return float(valor.split()[0]) / 24  # converte horas para dias
    return np.nan

df['Dias desde última atualização (dias)'] = df['Dias desde última atualização'].apply(extrai_dias_ou_horas)

# ----------------------------
# RQ01: Sistemas populares são maduros/antigos?
plt.figure(figsize=(9,6))
sns.boxplot(y=df['Idade (anos)'], color="skyblue")
plt.title('RQ01: Sistemas populares são maduros/antigos?\nDistribuição da idade dos 1000 repositórios populares')
plt.ylabel('Idade (anos)')
plt.xlabel('Repositórios')
plt.grid(axis='y', linestyle='--', alpha=0.5)
median_idade = df['Idade (anos)'].median()
plt.legend([f"Mediana: {median_idade:.2f} anos"], loc="upper right")
plt.tight_layout()
plt.savefig("RQ01_idade_boxplot.png")
plt.clf()

# ----------------------------
# RQ02: Sistemas populares recebem muita contribuição externa?
plt.figure(figsize=(9,6))
sns.violinplot(y=df['PRs aceitos'], color="lightgreen")
plt.title('RQ02: Sistemas populares recebem muita contribuição externa?\nDistribuição do total de pull requests aceitas')
plt.ylabel('Total de PRs aceitas')
plt.xlabel('Repositórios')
plt.grid(axis='y', linestyle='--', alpha=0.5)
median_prs = df['PRs aceitos'].median()
plt.legend([f"Mediana: {median_prs:.0f} PRs"], loc="upper right")
plt.tight_layout()
plt.savefig("RQ02_prs_violinplot.png")
plt.clf()

# ----------------------------
# RQ03: Sistemas populares lançam releases com frequência?
plt.figure(figsize=(9,6))
sns.boxplot(y=df['Total releases'], color="salmon")
plt.title('RQ03: Sistemas populares lançam releases com frequência?\nDistribuição do total de releases')
plt.ylabel('Total de releases')
plt.xlabel('Repositórios')
plt.grid(axis='y', linestyle='--', alpha=0.5)
median_releases = df['Total releases'].median()
plt.legend([f"Mediana: {median_releases:.0f} releases"], loc="upper right")
plt.tight_layout()
plt.savefig("RQ03_releases_boxplot.png")
plt.clf()

# ----------------------------
# RQ04: Sistemas populares são atualizados com frequência?
plt.figure(figsize=(9,6))
sns.histplot(df['Dias desde última atualização (dias)'].dropna(), bins=30, color="orange")
plt.title('RQ04: Sistemas populares são atualizados com frequência?\nHistograma do tempo desde última atualização')
plt.xlabel('Dias desde última atualização')
plt.ylabel('Quantidade de repositórios')
plt.grid(axis='y', linestyle='--', alpha=0.5)
median_update = df['Dias desde última atualização (dias)'].median()
plt.legend([f"Mediana: {median_update:.1f} dias"], loc="upper right")
plt.tight_layout()
plt.savefig("RQ04_atualizacao_hist.png")
plt.clf()

# ----------------------------
# RQ05: Sistemas populares são escritos nas linguagens mais populares?
lang_counts = df['Linguagem primária'].value_counts()
plt.figure(figsize=(12,7))
sns.barplot(x=lang_counts.index, y=lang_counts.values, palette="viridis")
plt.title('RQ05: Sistemas populares são escritos nas linguagens mais populares?\nDistribuição das linguagens primárias dos repositórios')
plt.xlabel('Linguagem primária')
plt.ylabel('Número de repositórios')
plt.xticks(rotation=45)
for i, v in enumerate(lang_counts.values):
    plt.text(i, v + max(lang_counts.values)*0.01, str(v), ha='center', fontsize=10)
plt.legend([f"Líder: {lang_counts.idxmax()} ({lang_counts.max()} repositórios)"], loc="upper right")
plt.tight_layout()
plt.savefig("RQ05_linguagens_barplot.png")
plt.clf()

# ----------------------------
# RQ06: Sistemas populares possuem um alto percentual de issues fechadas?
plt.figure(figsize=(9,6))
sns.boxplot(y=df['Percentual issues fechadas'], color="purple")
plt.title('RQ06: Sistemas populares possuem um alto percentual de issues fechadas?\nDistribuição do percentual de issues fechadas')
plt.ylabel('Percentual de issues fechadas')
plt.xlabel('Repositórios')
plt.grid(axis='y', linestyle='--', alpha=0.5)
median_issues = df['Percentual issues fechadas'].median()
plt.legend([f"Mediana: {median_issues:.2f}"], loc="upper right")
plt.tight_layout()
plt.savefig("RQ06_issues_boxplot.png")
plt.clf()

# ----------------------------
# RQ07: Bônus - análise por linguagem (PRs, releases, atualização)
top_langs = lang_counts.index[:5]  # Top 5 linguagens
metrics = {
    "PRs aceitos": "Total de PRs aceitas por linguagem",
    "Total releases": "Total de releases por linguagem",
    "Dias desde última atualização (dias)": "Dias desde última atualização por linguagem"
}
for metric, title in metrics.items():
    plt.figure(figsize=(12,7))
    sns.boxplot(x=df['Linguagem primária'], y=df[metric], order=top_langs)
    plt.title(f"RQ07: {title}")
    plt.xlabel('Linguagem primária')
    plt.ylabel(metric)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.legend([f"Comparação das Top 5 linguagens"], loc="upper right")
    plt.tight_layout()
    plt.savefig(f"RQ07_{metric.replace(' ', '_')}_por_linguagem.png")
    plt.clf()

