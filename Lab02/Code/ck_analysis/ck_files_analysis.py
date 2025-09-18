import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Caminhos dos arquivos
class_csv = "./class.csv"
repos_csv = "../../Docs/repos_java_metrics.csv"

# Carregar datasets
df_class = pd.read_csv(class_csv)
df_repos = pd.read_csv(repos_csv)

# --- 1. Selecionar métricas relevantes do CK ---
metrics = df_class[["cbo", "dit", "lcom"]]

# Resumo estatístico geral
summary = metrics.agg(["mean", "median", "std"])
print("Resumo estatístico das métricas de qualidade:")
print(summary)

# --- 2. Agregar métricas por repositório ---
# O arquivo class.csv tem colunas: file, class, cbo, dit, lcom...
# geralmente o caminho do arquivo tem o nome do repositório
df_class["repo"] = df_class["file"].apply(lambda x: x.split("/")[0])  # ajusta conforme sua estrutura
repo_metrics = df_class.groupby("repo")[["cbo", "dit", "lcom"]].mean().reset_index()

# --- 3. Juntar com métricas de processo do repos_java_metrics.csv ---
df_merged = pd.merge(repo_metrics, df_repos, left_on="repo", right_on="Repo", how="inner")

# --- 4. Correlações ---
corr = df_merged[["Estrelas", "Idade (anos)", "Total releases", "cbo", "dit", "lcom"]].corr(method="spearman")
print("\nCorrelação (Spearman):")
print(corr)

# --- 5. Gráficos ---
sns.pairplot(df_merged[["Estrelas", "Idade (anos)", "Total releases", "cbo", "dit", "lcom"]])
plt.savefig("correlacoes.png", dpi=300)
plt.close()

# Exemplo de gráfico específico
plt.scatter(df_merged["Estrelas"], df_merged["cbo"], alpha=0.5)
plt.xlabel("Popularidade (Estrelas)")
plt.ylabel("CBO Médio")
plt.title("Popularidade vs CBO")
plt.savefig("popularidade_cbo.png", dpi=300)
plt.close()
