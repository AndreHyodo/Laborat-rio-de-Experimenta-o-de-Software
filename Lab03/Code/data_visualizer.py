import os
import pandas as pd
import matplotlib.pyplot as plt

class DataVisualizer:
    """
    Cria visualizações das métricas e resultados estatísticos dos PRs.
    """

    def create_all_visualizations(self, metrics_df: pd.DataFrame, results: dict, results_dir: str):
        # Exemplo: Histograma do tempo de análise dos PRs
        self._plot_histogram(metrics_df["analysis_time_hours"], "Tempo de análise dos PRs (horas)", "analysis_time_hist", results_dir)
        
        # Exemplo: Boxplot de adições por status
        self._plot_box(metrics_df, "additions", "Adições por Status", "additions_boxplot", results_dir)
        
        # Exemplo: Boxplot de número de revisões
        self._plot_box(metrics_df, "reviews_count", "Número de revisões por Status", "reviews_count_boxplot", results_dir)
        
        # Você pode expandir criando visualizações dos resultados das pesquisas (results dict)

    def _plot_histogram(self, series, title, filename, out_dir):
        plt.figure()
        series.dropna().hist(bins=30)
        plt.title(title)
        plt.xlabel("Valor")
        plt.ylabel("Frequência")
        plt.tight_layout()
        path = os.path.join(out_dir, f"{filename}.png")
        plt.savefig(path)
        plt.close()

    def _plot_box(self, df, column, title, filename, out_dir):
        plt.figure()
        df.boxplot(column=column, by="status")
        plt.title(title)
        plt.xlabel("Status")
        plt.ylabel(column)
        plt.tight_layout()
        path = os.path.join(out_dir, f"{filename}.png")
        plt.savefig(path)
        plt.close()