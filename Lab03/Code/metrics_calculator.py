import pandas as pd
from datetime import datetime

class MetricsCalculator:
    """
    Calcula métricas relevantes para PRs de acordo com o laboratório:
    - Tamanho: arquivos, adições, remoções
    - Tempo de análise: criação até fechamento/merge
    - Descrição: caracteres do corpo
    - Interações: participantes, comentários
    - Feedback: status final (merged/closed)
    - Número de revisões
    """

    def calculate_all_metrics(self, prs_df: pd.DataFrame) -> pd.DataFrame:
        metrics = []
        for _, pr in prs_df.iterrows():
            metrics.append(self._calculate_metrics_for_pr(pr))
        metrics_df = pd.DataFrame(metrics)
        return metrics_df

    def _calculate_metrics_for_pr(self, pr: pd.Series) -> dict:
        # Tamanho
        files_changed = pr.get("changed_files", 0)
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)

        # Tempo de análise
        created_at = self._parse_datetime(pr.get("created_at"))
        closed_at = self._parse_datetime(pr.get("closed_at"))
        merged_at = self._parse_datetime(pr.get("merged_at"))
        end_time = merged_at if merged_at else closed_at
        analysis_time_hours = (
            (end_time - created_at).total_seconds() / 3600 if end_time and created_at else None
        )

        # Descrição
        body = pr.get("body", "") or ""
        description_length = len(body)

        # Interações
        participants = pr.get("participants", 1)
        comments_count = pr.get("comments_count", pr.get("comments", 0))

        # Feedback final
        status = "merged" if pr.get("merged_at") else pr.get("state", "unknown")

        # Número de revisões
        reviews_count = pr.get("reviews_count", 0)

        return {
            "repository": pr.get("repository"),
            "pr_number": pr.get("pr_number"),
            "status": status,
            "files_changed": files_changed,
            "additions": additions,
            "deletions": deletions,
            "analysis_time_hours": analysis_time_hours,
            "description_length": description_length,
            "participants": participants,
            "comments_count": comments_count,
            "reviews_count": reviews_count
        }

    def _parse_datetime(self, value):
        if pd.isnull(value) or not value:
            return None
        # GitHub's timestamps: '2021-01-01T12:34:56Z'
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            try:
                # Sometimes might be with timezone (+00:00)
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return None