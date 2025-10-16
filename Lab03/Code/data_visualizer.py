import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.ticker import FuncFormatter
import warnings
warnings.filterwarnings('ignore')

# Configurações de visualização profissional
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18
})

# Função para formatar eixos de tempo
def time_formatter(x, pos):
    if x < 1:
        return f"{x*60:.0f} min"
    elif x < 24:
        return f"{x:.1f} h"
    else:
        return f"{x/24:.1f} d"

# Carregar todos os dados
def load_all_data():
    data = {}
    
    # RQ01: Tamanho vs Status
    data['RQ01'] = pd.DataFrame({
        'status': ['closed', 'merged'],
        'count': [0, 0],
        'files_changed_mean': [0, 0],
        'additions_mean': [0, 0],
        'deletions_mean': [0, 0]
    })
    
    # RQ02: Tempo vs Status
    data['RQ02'] = pd.DataFrame({
        'status': ['closed', 'merged'],
        'count': [7047.0, 11308.0],
        'mean': [2669.363984989672, 371.71495003537314],
        'std': [7128.124256405442, 1704.8345115163647],
        'min': [0.0002777777777777778, 0.0008333333333333334],
        '25%': [0.9886111111111111, 0.9116666666666666],
        '50%': [90.26527777777778, 14.39611111111111],
        '75%': [1646.7151388888888, 100.53215277777778],
        'max': [83542.63972222223, 35778.8525]
    })
    
    # RQ03: Descrição vs Status
    data['RQ03'] = pd.DataFrame({
        'status': ['closed', 'merged'],
        'count': [7047.0, 11308.0],
        'mean': [0.0, 0.0],
        'std': [0.0, 0.0],
        'min': [0.0, 0.0],
        '25%': [0.0, 0.0],
        '50%': [0.0, 0.0],
        '75%': [0.0, 0.0],
        'max': [0.0, 0.0]
    })
    
    # RQ04: Interações vs Status
    data['RQ04'] = pd.DataFrame({
        'status': ['closed', 'merged'],
        'count': [7047.0, 11308.0],
        'participants_mean': [1.0, 1.0],
        'comments_mean': [0.0, 0.0]
    })
    
    # RQ05: Tamanho vs Revisões
    data['RQ05'] = pd.DataFrame({
        'reviews_count': [0],
        'count': [0],
        'files_changed_mean': [0],
        'additions_mean': [0],
        'deletions_mean': [0]
    })
    
    # RQ06: Tempo vs Revisões
    data['RQ06'] = pd.DataFrame({
        'reviews_count': [0],
        'count': [18355.0],
        'mean': [1253.8469440055692],
        'std': [4748.158494659857],
        'min': [0.0002777777777777778],
        '25%': [0.9270833333333333],
        '50%': [21.834444444444443],
        '75%': [288.3113888888889],
        'max': [83542.63972222223]
    })
    
    # RQ07: Descrição vs Revisões
    data['RQ07'] = pd.DataFrame({
        'reviews_count': [0],
        'count': [18355.0],
        'mean': [0.0],
        'std': [0.0],
        'min': [0.0],
        '25%': [0.0],
        '50%': [0.0],
        '75%': [0.0],
        'max': [0.0]
    })
    
    # RQ08: Interações vs Revisões
    data['RQ08'] = pd.DataFrame({
        'reviews_count': [0],
        'count': [18355.0],
        'participants_mean': [1.0],
        'comments_mean': [0.0]
    })
    
    return data

# Função para verificar se há dados válidos
def has_valid_data(df):
    if 'count' in df.columns:
        return df['count'].sum() > 0
    return False

# Função para gráficos sem dados
def plot_no_data(rq_name):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, 'SEM DADOS VÁLIDOS\nPARA ANÁLISE', 
            ha='center', va='center', fontsize=16, color='red',
            bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="red", alpha=0.8))
    ax.set_title(f'{rq_name}: Análise Não Disponível', fontsize=18, color='red')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(f'{rq_name}_Analise.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ01: Tamanho vs Status
def plot_rq01(data):
    if not has_valid_data(data['RQ01']):
        plot_no_data('RQ01')
        return
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Preparar dados
    df = data['RQ01']
    metrics = ['files_changed_mean', 'additions_mean', 'deletions_mean']
    x = np.arange(len(df['status']))
    width = 0.25
    
    # Gráfico de barras agrupadas
    for i, metric in enumerate(metrics):
        ax.bar(x + i*width, df[metric], width, 
               label=metric.replace('_mean', '').replace('_', ' ').title())
    
    ax.set_title('RQ01: Relação entre Tamanho dos PRs e Feedback Final', fontsize=18, pad=20)
    ax.set_xlabel('Status do PR', fontsize=14)
    ax.set_ylabel('Contagem Média', fontsize=14)
    ax.set_xticks(x + width)
    ax.set_xticklabels(df['status'])
    ax.legend(fontsize=12)
    
    plt.tight_layout()
    plt.savefig('RQ01_Tamanho_vs_Status.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ02: Tempo vs Status
def plot_rq02(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    df = data['RQ02']
    
    # Gráfico 1: Comparação de médias
    bars = ax1.bar(df['status'], df['mean'], yerr=df['std'], 
                  capsize=10, color=['#ff6b6b', '#4ecdc4'], alpha=0.8)
    
    ax1.set_title('RQ02: Tempo Médio por Status', fontsize=16)
    ax1.set_ylabel('Tempo Médio (horas)', fontsize=14)
    ax1.yaxis.set_major_formatter(FuncFormatter(time_formatter))
    
    # Adicionar anotações
    for bar, row in zip(bars, df.itertuples()):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + row.std*0.05, 
                f"{height:.1f} h\n({height/24:.1f} dias)",
                ha='center', va='bottom', fontsize=11)
    
    # Gráfico 2: Boxplot
    box_data = []
    for _, row in df.iterrows():
        box_data.append([row['min'], row['25%'], row['50%'], row['75%'], row['max']])
    
    bp = ax2.boxplot(box_data, labels=df['status'], patch_artist=True)
    colors = ['#ff6b6b', '#4ecdc4']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    ax2.set_title('RQ02: Distribuição do Tempo de Análise', fontsize=16)
    ax2.set_ylabel('Tempo (horas - escala log)', fontsize=14)
    ax2.set_yscale('log')
    ax2.yaxis.set_major_formatter(FuncFormatter(time_formatter))
    
    plt.suptitle('RQ02: Relação entre Tempo de Análise e Feedback Final', fontsize=18, y=0.98)
    plt.tight_layout()
    plt.savefig('RQ02_Tempo_vs_Status.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ03: Descrição vs Status
def plot_rq03(data):
    if not has_valid_data(data['RQ03']) or data['RQ03']['mean'].sum() == 0:
        plot_no_data('RQ03')
        return
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    df = data['RQ03']
    ax.bar(df['status'], df['mean'], color=['#ff6b6b', '#4ecdc4'])
    ax.set_title('RQ03: Relação entre Descrição dos PRs e Feedback Final', fontsize=18, pad=20)
    ax.set_ylabel('Caracteres Médios', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('RQ03_Descricao_vs_Status.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ04: Interações vs Status
def plot_rq04(data):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    df = data['RQ04']
    x = np.arange(len(df['status']))
    width = 0.35
    metrics = ['participants_mean', 'comments_mean']
    
    # Gráfico de barras agrupadas
    for i, metric in enumerate(metrics):
        ax.bar(x + i*width, df[metric], width, 
               label=metric.replace('_mean', '').replace('_', ' ').title())
    
    ax.set_title('RQ04: Relação entre Interações nos PRs e Feedback Final', fontsize=18, pad=20)
    ax.set_xlabel('Status do PR', fontsize=14)
    ax.set_ylabel('Contagem Média', fontsize=14)
    ax.set_xticks(x + width/2)
    ax.set_xticklabels(df['status'])
    ax.legend(fontsize=12)
    
    plt.tight_layout()
    plt.savefig('RQ04_Interacoes_vs_Status.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ05: Tamanho vs Revisões
def plot_rq05(data):
    if not has_valid_data(data['RQ05']):
        plot_no_data('RQ05')
        return
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    df = data['RQ05']
    metrics = ['files_changed_mean', 'additions_mean', 'deletions_mean']
    
    # Gráfico de barras
    bars = ax.bar(metrics, [df[metric].iloc[0] for metric in metrics])
    
    ax.set_title('RQ05: Relação entre Tamanho dos PRs e Número de Revisões', fontsize=18, pad=20)
    ax.set_ylabel('Contagem Média', fontsize=14)
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f"{height:.1f}", ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('RQ05_Tamanho_vs_Revisoes.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ06: Tempo vs Revisões
def plot_rq06(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    df = data['RQ06']
    
    # Gráfico 1: Distribuição completa
    stats = ['min', '25%', '50%', '75%', 'max']
    values = [df[stat].iloc[0] for stat in stats]
    colors = ['#2c7fb8', '#7fcdbb', '#edf8b1', '#fdcc87', '#d94701']
    
    bars = ax1.bar(stats, values, color=colors)
    ax1.set_title('RQ06: Distribuição do Tempo de Análise', fontsize=16)
    ax1.set_ylabel('Tempo (horas)', fontsize=14)
    ax1.yaxis.set_major_formatter(FuncFormatter(time_formatter))
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f"{height:.1f}", ha='center', va='bottom')
    
    # Gráfico 2: Média vs Mediana
    mean_val = df['mean'].iloc[0]
    median_val = df['50%'].iloc[0]
    
    ax2.bar(['Média', 'Mediana'], [mean_val, median_val], 
            color=['#d94701', '#2c7fb8'])
    ax2.set_title('RQ06: Média vs Mediana', fontsize=16)
    ax2.set_ylabel('Tempo (horas)', fontsize=14)
    ax2.yaxis.set_major_formatter(FuncFormatter(time_formatter))
    
    # Adicionar anotações
    for i, v in enumerate([mean_val, median_val]):
        ax2.text(i, v + max(mean_val, median_val)*0.05, 
                f"{v:.1f} h\n({v/24:.1f} dias)",
                ha='center', va='bottom', fontsize=11)
    
    plt.suptitle('RQ06: Relação entre Tempo de Análise e Número de Revisões', fontsize=18, y=0.98)
    plt.tight_layout()
    plt.savefig('RQ06_Tempo_vs_Revisoes.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ07: Descrição vs Revisões
def plot_rq07(data):
    if not has_valid_data(data['RQ07']) or data['RQ07']['mean'].sum() == 0:
        plot_no_data('RQ07')
        return
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    df = data['RQ07']
    ax.bar(['Descrição Média'], df['mean'])
    ax.set_title('RQ07: Relação entre Descrição dos PRs e Número de Revisões', fontsize=18, pad=20)
    ax.set_ylabel('Caracteres Médios', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('RQ07_Descricao_vs_Revisoes.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gráfico para RQ08: Interações vs Revisões
def plot_rq08(data):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    df = data['RQ08']
    metrics = ['participants_mean', 'comments_mean']
    
    # Gráfico de barras
    bars = ax.bar(metrics, [df[metric].iloc[0] for metric in metrics])
    
    ax.set_title('RQ08: Relação entre Interações nos PRs e Número de Revisões', fontsize=18, pad=20)
    ax.set_ylabel('Contagem Média', fontsize=14)
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f"{height:.1f}", ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('RQ08_Interacoes_vs_Revisoes.png', dpi=300, bbox_inches='tight')
    plt.close()

# Gerar todos os gráficos separados
def generate_all_separated_plots():
    data = load_all_data()
    
    print("Gerando gráficos individuais para cada RQ...")
    
    # Gerar gráficos para cada RQ
    plot_rq01(data)
    print("Gráfico gerado: RQ01_Tamanho_vs_Status.png")
    
    plot_rq02(data)
    print("Gráfico gerado: RQ02_Tempo_vs_Status.png")
    
    plot_rq03(data)
    print("Gráfico gerado: RQ03_Descricao_vs_Status.png")
    
    plot_rq04(data)
    print("Gráfico gerado: RQ04_Interacoes_vs_Status.png")
    
    plot_rq05(data)
    print("Gráfico gerado: RQ05_Tamanho_vs_Revisoes.png")
    
    plot_rq06(data)
    print("Gráfico gerado: RQ06_Tempo_vs_Revisoes.png")
    
    plot_rq07(data)
    print("Gráfico gerado: RQ07_Descricao_vs_Revisoes.png")
    
    plot_rq08(data)
    print("Gráfico gerado: RQ08_Interacoes_vs_Revisoes.png")
    
    print("\nTodos os gráficos foram gerados com sucesso!")
    print("\nArquivos disponíveis para download:")
    print("- RQ01_Tamanho_vs_Status.png")
    print("- RQ02_Tempo_vs_Status.png")
    print("- RQ03_Descricao_vs_Status.png")
    print("- RQ04_Interacoes_vs_Status.png")
    print("- RQ05_Tamanho_vs_Revisoes.png")
    print("- RQ06_Tempo_vs_Revisoes.png")
    print("- RQ07_Descricao_vs_Revisoes.png")
    print("- RQ08_Interacoes_vs_Revisoes.png")

# Executar
if __name__ == "__main__":
    generate_all_separated_plots()