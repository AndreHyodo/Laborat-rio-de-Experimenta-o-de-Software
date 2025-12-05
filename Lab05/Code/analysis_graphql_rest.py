#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

# Config
DATA_DIR = "../Data"
GRAPHQL_CSV = os.path.join(DATA_DIR, "graphql_results.csv")
REST_CSV = os.path.join(DATA_DIR, "rest_results.csv")
OUTPUT_DIR = "../analysis_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set(style="whitegrid", context="talk")

def load_and_label(path, expected_type=None):
    df = pd.read_csv(path)
    if 'type' not in df.columns and expected_type is not None:
        df['type'] = expected_type
    df.columns = [c.strip() for c in df.columns]
    return df

print("Carregando arquivos...")
df_gql = load_and_label(GRAPHQL_CSV)
df_rest = load_and_label(REST_CSV)

# Garantir coluna 'type' correta
if 'type' not in df_rest.columns or df_rest['type'].isnull().all():
    df_rest['type'] = 'REST'
df_gql['type'] = df_gql['type'].fillna('GraphQL')
df_rest['type'] = df_rest['type'].fillna('REST')

df = pd.concat([df_gql, df_rest], ignore_index=True, sort=False)
print(f"Total de linhas carregadas (GraphQL + REST): {len(df)}")

# Limpeza básica: remove linhas com erro ou status_code != 200
def clean(df):
    df = df.copy()
    if 'error' in df.columns:
        df['error'] = df['error'].replace({np.nan: ""})
    else:
        df['error'] = ""
    if 'status_code' in df.columns:
        df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
    else:
        df['status_code'] = np.nan
    df_clean = df[(df['status_code'] == 200) & (df['error'].astype(str) == "")]
    return df_clean

df_clean = clean(df)
print(f"Linhas após remoção de erros/status != 200: {len(df_clean)}")

# Colunas essenciais
required_cols = ['trial_id', 'name', 'latency_ms', 'payload_bytes', 'type', 'url']
for col in ['trial_id', 'latency_ms', 'payload_bytes', 'type']:
    if col not in df_clean.columns:
        raise RuntimeError(f"Coluna esperada '{col}' não encontrada no CSV limpo.")
# 'name' ou 'url' podem faltar; se 'name' faltar, criamos com NaN -> 'UNKNOWN'
if 'name' not in df_clean.columns:
    df_clean['name'] = np.nan
if 'url' not in df_clean.columns:
    df_clean['url'] = np.nan

# Normaliza colunas
df_clean['name'] = df_clean['name'].fillna('UNKNOWN').astype(str)
df_clean['latency_ms'] = pd.to_numeric(df_clean['latency_ms'], errors='coerce')
df_clean['payload_bytes'] = pd.to_numeric(df_clean['payload_bytes'], errors='coerce')
df_clean['trial_id'] = df_clean['trial_id'].astype(str)

# Informações iniciais
counts = df_clean.groupby(['name', 'type']).size().reset_index(name='n')
print("\nContagem por (name, type):")
print(counts.to_string(index=False))

unknown_mask = (df_clean['name'] == 'UNKNOWN') & (df_clean['type'] == 'REST')
n_unknown = unknown_mask.sum()
print(f"\nNúmero de linhas REST com name == 'UNKNOWN': {n_unknown}")

# Mostra alguns exemplos para inspeção (até 10)
print("\nAmostra de linhas UNKNOWN (até 10) para inspeção:")
print(df_clean[unknown_mask].head(10).to_string(index=False))

# Heurística de inferência:
# 1) pela URL (se contém 'repos' -> user_repos; se contém '/users/' e não 'repos' -> user_detail)
# 2) se URL não ajudar, compara payload_bytes com medianas conhecidas do GraphQL e atribui o nome mais próximo
gql_stats = df_clean[(df_clean['type'] == 'GraphQL') & (df_clean['name'] != 'UNKNOWN')].groupby('name')['payload_bytes'].median().to_dict()
print("\nMedianna de payload dos endpoints GraphQL (usadas para inferência por payload):")
print(gql_stats)

def infer_name_from_url(url):
    if not isinstance(url, str) or url.strip() == "" or pd.isna(url):
        return None
    u = url.lower()
    if 'repos' in u:
        return 'user_repos'
    # busca '/users/' ou '/user/' (heurística comum para REST GitHub)
    if '/users/' in u or '/user/' in u or '/users?' in u:
        return 'user_detail'
    # outras heurísticas simples
    if '/followers' in u or '/following' in u:
        return 'user_detail'
    return None

def infer_by_payload(pb):
    if np.isnan(pb):
        return None
    if len(gql_stats) == 0:
        return None
    # escolhe o nome cujo mediana está mais próxima (valor absoluto)
    candidates = list(gql_stats.items())
    diffs = [(name, abs(pb - med)) for name, med in candidates]
    best_name, best_diff = min(diffs, key=lambda x: x[1])
    # calcula quão distante está relativamente: se payload de referencia for zero cautela
    ref = gql_stats[best_name] if gql_stats[best_name] not in (0, None, np.nan) else 1.0
    rel = best_diff / float(ref)
    # threshold: aceita se relative difference <= 1.0 (ou seja, dentro de um fator ~2)
    if rel <= 1.0:
        return best_name
    return None

# Aplica inferência
df_fix = df_clean.copy()
assigned = 0
assigned_details = {'url':0, 'payload':0}
for idx, row in df_fix[unknown_mask].iterrows():
    name_inf = infer_name_from_url(row.get('url', ''))
    if name_inf is not None:
        df_fix.at[idx, 'name'] = name_inf
        assigned += 1
        assigned_details['url'] += 1
        continue
    # fallback payload
    pb = row.get('payload_bytes', np.nan)
    name_inf = infer_by_payload(pb)
    if name_inf is not None:
        df_fix.at[idx, 'name'] = name_inf
        assigned += 1
        assigned_details['payload'] += 1

print(f"\nForam inferidos {assigned} nomes para linhas UNKNOWN (url: {assigned_details['url']}, payload: {assigned_details['payload']}).")
n_unknown_after = (df_fix['name'] == 'UNKNOWN').sum()
print(f"UNKNOWN restantes após inferência: {n_unknown_after}")

if n_unknown_after > 0:
    print("\nAmostra das UNKNOWN restantes (até 10):")
    print(df_fix[df_fix['name'] == 'UNKNOWN'].head(10).to_string(index=False))
    print("\nSe quiser que eu force uma atribuição automática mais agressiva, diga (por ex.) 'atribuír por payload com factor 3' e eu ajusto.")

# Recalcula contagens
counts2 = df_fix.groupby(['name', 'type']).size().reset_index(name='n')
print("\nNova contagem por (name, type) após inferência:")
print(counts2.to_string(index=False))

# Funções de análise (pivot, testes, plots)
def make_pivot(df_sub, value_col):
    pivot = df_sub.pivot_table(
        index=['trial_id', 'name'],
        columns='type',
        values=value_col,
        aggfunc='first'
    )
    if 'GraphQL' in pivot.columns and 'REST' in pivot.columns:
        pivot = pivot.dropna(subset=['GraphQL', 'REST'], how='any')
    else:
        pivot = pd.DataFrame()
    return pivot

# Plots globais (box + points). Retiramos edgecolor para evitar futurewarning.
plt.figure(figsize=(12, 6))
ax = sns.boxplot(data=df_fix, x='name', y='latency_ms', hue='type', showfliers=False)
sns.stripplot(data=df_fix, x='name', y='latency_ms', hue='type', dodge=True, jitter=True, alpha=0.5)
handles, labels = ax.get_legend_handles_labels()
if len(handles) >= 2:
    plt.legend(handles[:2], labels[:2], title='type')
plt.ylabel("Latency (ms)")
plt.title("Distribuição de latência por endpoint e protocolo (boxplot + pontos)")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "latency_boxplot_by_endpoint_inferred.png"))
plt.close()

plt.figure(figsize=(12, 6))
ax = sns.boxplot(data=df_fix, x='name', y='payload_bytes', hue='type', showfliers=False)
sns.stripplot(data=df_fix, x='name', y='payload_bytes', hue='type', dodge=True, jitter=True, alpha=0.5)
handles, labels = ax.get_legend_handles_labels()
if len(handles) >= 2:
    plt.legend(handles[:2], labels[:2], title='type')
plt.ylabel("Payload (bytes)")
plt.title("Distribuição de payload por endpoint e protocolo (boxplot + pontos)")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "payload_boxplot_by_endpoint_inferred.png"))
plt.close()

# Estatísticas e testes pareados por endpoint
endpoints = sorted(df_fix['name'].unique(), key=str)
stat_results = []
for endpoint in endpoints:
    df_ep = df_fix[df_fix['name'] == endpoint]
    pivot_latency = make_pivot(df_ep, 'latency_ms')
    pivot_payload = make_pivot(df_ep, 'payload_bytes')
    result = {'endpoint': endpoint, 'n_paired_latency': len(pivot_latency), 'n_paired_payload': len(pivot_payload)}

    # Latency
    if len(pivot_latency) >= 2:
        g = pivot_latency['GraphQL'].values
        r = pivot_latency['REST'].values
        diff = g - r
        try:
            shapiro_p = stats.shapiro(diff)[1] if len(diff) >= 3 else np.nan
        except Exception:
            shapiro_p = np.nan
        if (not np.isnan(shapiro_p) and shapiro_p > 0.05 and len(diff) >= 3):
            t_stat, t_p = stats.ttest_rel(g, r)
            test_used = 'paired t-test'
            test_stat = t_stat
            p_val = t_p
        else:
            try:
                w_stat, w_p = stats.wilcoxon(g, r)
            except Exception:
                w_stat, w_p = np.nan, np.nan
            test_used = 'wilcoxon'
            test_stat = w_stat
            p_val = w_p
        result.update({'latency_test': test_used, 'latency_stat': float(test_stat) if not pd.isna(test_stat) else None, 'latency_p': float(p_val) if not pd.isna(p_val) else None})
    else:
        result.update({'latency_test': None, 'latency_stat': None, 'latency_p': None})

    # Payload
    if len(pivot_payload) >= 2:
        g = pivot_payload['GraphQL'].values
        r = pivot_payload['REST'].values
        diff = g - r
        try:
            shapiro_p = stats.shapiro(diff)[1] if len(diff) >= 3 else np.nan
        except Exception:
            shapiro_p = np.nan
        if (not np.isnan(shapiro_p) and shapiro_p > 0.05 and len(diff) >= 3):
            t_stat, t_p = stats.ttest_rel(g, r)
            test_used = 'paired t-test'
            test_stat = t_stat
            p_val = t_p
        else:
            try:
                w_stat, w_p = stats.wilcoxon(g, r)
            except Exception:
                w_stat, w_p = np.nan, np.nan
            test_used = 'wilcoxon'
            test_stat = w_stat
            p_val = w_p
        result.update({'payload_test': test_used, 'payload_stat': float(test_stat) if not pd.isna(test_stat) else None, 'payload_p': float(p_val) if not pd.isna(p_val) else None})
    else:
        result.update({'payload_test': None, 'payload_stat': None, 'payload_p': None})

    stat_results.append(result)

    # Plots pareados de latência (se existirem)
    if len(pivot_latency) > 0:
        plt.figure(figsize=(8, 6))
        x = [0, 1]
        for idx, row in pivot_latency.iterrows():
            plt.plot(x, [row['GraphQL'], row['REST']], color='gray', alpha=0.35)
        plt.scatter([0]*len(pivot_latency), pivot_latency['GraphQL'], color='C0', label='GraphQL', s=60)
        plt.scatter([1]*len(pivot_latency), pivot_latency['REST'], color='C1', label='REST', s=60)
        plt.xticks([0, 1], ['GraphQL', 'REST'])
        plt.ylabel("Latency (ms)")
        plt.title(f"Latência pareada por trial - {endpoint}\n(n={len(pivot_latency)})")
        plt.legend()
        plt.tight_layout()
        fname = os.path.join(OUTPUT_DIR, f"latency_paired_{endpoint}.png".replace(" ", "_"))
        plt.savefig(fname)
        plt.close()

    # Plots pareados de payload
    if len(pivot_payload) > 0:
        plt.figure(figsize=(8, 6))
        x = [0, 1]
        for idx, row in pivot_payload.iterrows():
            plt.plot(x, [row['GraphQL'], row['REST']], color='gray', alpha=0.35)
        plt.scatter([0]*len(pivot_payload), pivot_payload['GraphQL'], color='C0', label='GraphQL', s=60)
        plt.scatter([1]*len(pivot_payload), pivot_payload['REST'], color='C1', label='REST', s=60)
        plt.xticks([0, 1], ['GraphQL', 'REST'])
        plt.ylabel("Payload (bytes)")
        plt.title(f"Payload pareado por trial - {endpoint}\n(n={len(pivot_payload)})")
        plt.legend()
        plt.tight_layout()
        fname = os.path.join(OUTPUT_DIR, f"payload_paired_{endpoint}.png".replace(" ", "_"))
        plt.savefig(fname)
        plt.close()

# Imprime resultados estatísticos
print("\nResultados dos testes estatísticos por endpoint (apenas comparações pareadas):")
for r in stat_results:
    print(f"- Endpoint: {r['endpoint']}")
    if r['latency_test'] is not None:
        print(f"  Latency: test={r['latency_test']}, stat={r['latency_stat']}, p={r['latency_p']}, n_paired={r['n_paired_latency']}")
    else:
        print("  Latency: dados pareados insuficientes para teste.")
    if r['payload_test'] is not None:
        print(f"  Payload: test={r['payload_test']}, stat={r['payload_stat']}, p={r['payload_p']}, n_paired={r['n_paired_payload']}")
    else:
        print("  Payload: dados pareados insuficientes para teste.")
    print()

# Salva sumário
summary = df_fix.groupby(['name', 'type']).agg(
    n=('latency_ms', 'count'),
    latency_median=('latency_ms', 'median'),
    latency_mean=('latency_ms', 'mean'),
    payload_median=('payload_bytes', 'median'),
    payload_mean=('payload_bytes', 'mean')
).reset_index()
summary.to_csv(os.path.join(OUTPUT_DIR, "summary_by_endpoint_and_type_inferred.csv"), index=False)
print("Sumário salvo em:", os.path.join(OUTPUT_DIR, "summary_by_endpoint_and_type_inferred.csv"))
print("Todos os gráficos salvos em:", OUTPUT_DIR)