import pandas as pd
import os

class StatisticalAnalyzer:
    """
    Realiza análises estatísticas para responder às questões de pesquisa do laboratório.
    """

    def analyze_research_questions(self, metrics_df: pd.DataFrame) -> dict:
        """
        Executa as análises para responder às questões de pesquisa.
        Retorna resultados como dict.
        """
        results = {}

        # RQ01: Relação entre tamanho dos PRs e feedback final
        results["RQ01"] = metrics_df.groupby("status")[["files_changed", "additions", "deletions"]].describe()

        # RQ02: Relação entre tempo de análise e feedback final
        results["RQ02"] = metrics_df.groupby("status")["analysis_time_hours"].describe()

        # RQ03: Relação entre descrição e feedback final
        results["RQ03"] = metrics_df.groupby("status")["description_length"].describe()

        # RQ04: Relação entre interações e feedback final
        results["RQ04"] = metrics_df.groupby("status")[["participants", "comments_count"]].describe()

        # RQ05: Relação entre tamanho dos PRs e número de revisões
        results["RQ05"] = metrics_df.groupby("reviews_count")[["files_changed", "additions", "deletions"]].describe()

        # RQ06: Relação entre tempo de análise e número de revisões
        results["RQ06"] = metrics_df.groupby("reviews_count")["analysis_time_hours"].describe()

        # RQ07: Relação entre descrição e número de revisões
        results["RQ07"] = metrics_df.groupby("reviews_count")["description_length"].describe()

        # RQ08: Relação entre interações e número de revisões
        results["RQ08"] = metrics_df.groupby("reviews_count")[["participants", "comments_count"]].describe()

        return results

    def save_results(self, results: dict, results_dir: str):
        """
        Salva os resultados das análises estatísticas em arquivos CSV.
        """
        os.makedirs(results_dir, exist_ok=True)
        for rq, result in results.items():
            if hasattr(result, "to_csv"):
                result.to_csv(os.path.join(results_dir, f"{rq}_results.csv"))
            else:
                # Se for dict ou outro tipo, salva como .txt
                with open(os.path.join(results_dir, f"{rq}_results.txt"), "w", encoding="utf-8") as f:
                    f.write(str(result))

    @staticmethod
    def load_results(results_dir: str) -> dict:
        """
        Carrega resultados previamente salvos.
        """
        results = {}
        for filename in os.listdir(results_dir):
            if filename.endswith("_results.csv"):
                rq = filename.replace("_results.csv", "")
                results[rq] = pd.read_csv(os.path.join(results_dir, filename), index_col=0)
            elif filename.endswith("_results.txt"):
                rq = filename.replace("_results.txt", "")
                with open(os.path.join(results_dir, filename), "r", encoding="utf-8") as f:
                    results[rq] = f.read()
        return results