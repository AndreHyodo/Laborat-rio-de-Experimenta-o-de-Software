import re
import sys
import os
from datetime import datetime
from statistics import mean, median
from typing import Dict, List, Any

# Arquivo de entrada padrão (gerado pelo seu script anterior)
INPUT_FILE = "resultado.txt"
# Arquivo de saída (relatório em .txt)
OUTPUT_FILE = "relatorio_rq7.txt"

# Linguagens populares conforme a imagem fornecida (ordem preservada)
POPULAR_LANGS = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C#",
    "C++",
    "PHP",
    "Shell",
    "C",
    "Go",
]

def parse_last_update_to_hours(text: str) -> int:
    """
    Converte "X dias" ou "Y horas" para horas (int).
    Retorna 0 se não conseguir interpretar.
    """
    if not text:
        return 0
    s = text.strip().lower()
    m = re.search(r"(\d+)\s*(dia|dias|hora|horas)", s)
    if not m:
        try:
            return int(float(s))
        except Exception:
            return 0
    val = int(m.group(1))
    unit = m.group(2)
    return val * 24 if unit.startswith("dia") else val

def parse_resultado(path: str) -> List[Dict[str, Any]]:
    """
    Lê o arquivo resultado.txt no formato:
      id: 1000
      Repo: yazi
      Idade (anos): 2.1
      PRs aceitos: 944
      Total releases: 27
      Dias desde última atualização: 0 horas
      Linguagem primária: Rust
      Percentual issues fechadas: 0.97
    Blocos podem ser separados por linhas '----' ou vazias.
    """
    repos: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}

    def commit():
        nonlocal current
        if current.get("repo"):
            current.setdefault("id", None)
            current.setdefault("idade_anos", None)
            current.setdefault("prs_aceitos", 0)
            current.setdefault("total_releases", 0)
            current.setdefault("last_update_hours", 0)
            current.setdefault("language", "N/A")
            current.setdefault("closed_issues_ratio", None)
            repos.append(current)
        current = {}

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or set(line) == {"-"}:
                if current:
                    commit()
                continue

            key = line.split(":", 1)[0].strip().lower()

            if key == "id":
                if current:
                    commit()
                try:
                    current = {"id": int(line.split(":", 1)[1].strip())}
                except Exception:
                    current = {"id": None}
                continue

            if key == "repo":
                current["repo"] = line.split(":", 1)[1].strip()
                continue

            if key.startswith("idade"):
                try:
                    current["idade_anos"] = float(line.split(":", 1)[1].strip())
                except Exception:
                    current["idade_anos"] = None
                continue

            if key.startswith("prs aceitos"):
                try:
                    current["prs_aceitos"] = int(line.split(":", 1)[1].strip())
                except Exception:
                    current["prs_aceitos"] = 0
                continue

            if key.startswith("total releases"):
                try:
                    current["total_releases"] = int(line.split(":", 1)[1].strip())
                except Exception:
                    current["total_releases"] = 0
                continue

            if key.startswith("dias desde última atualização") or key.startswith("dias desde ultima atualizacao"):
                val = line.split(":", 1)[1].strip()
                current["last_update_hours"] = parse_last_update_to_hours(val)
                continue

            if key.startswith("linguagem primária") or key.startswith("linguagem primaria"):
                current["language"] = line.split(":", 1)[1].strip()
                continue

            if key.startswith("percentual issues fechadas"):
                try:
                    current["closed_issues_ratio"] = float(line.split(":", 1)[1].strip())
                except Exception:
                    current["closed_issues_ratio"] = None
                continue

            # Demais linhas são ignoradas (como "Tempo de execução: ...")

    if current:
        commit()

    return repos

def group_by_language(repos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in repos:
        lang = r.get("language") or "N/A"
        groups.setdefault(lang, []).append(r)
    return groups

def safe_mean(arr: List[float]) -> float:
    return float(mean(arr)) if arr else 0.0

def safe_median(arr: List[float]) -> float:
    return float(median(arr)) if arr else 0.0

def summarize_group(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    prs = [int(x.get("prs_aceitos", 0) or 0) for x in items]
    rels = [int(x.get("total_releases", 0) or 0) for x in items]
    hrs = [int(x.get("last_update_hours", 0) or 0) for x in items]
    return {
        "count": len(items),
        "prs_mean": safe_mean(prs),
        "prs_median": safe_median(prs),
        "rels_mean": safe_mean(rels),
        "rels_median": safe_median(rels),
        "hrs_mean": safe_mean(hrs),       # menor é melhor (atualizados mais recentemente)
        "hrs_median": safe_median(hrs),
    }

def format_hours_as_human(hours: float) -> str:
    """Formata horas em string humana (horas ou dias)."""
    try:
        h = float(hours)
    except Exception:
        return str(hours)
    if h >= 24:
        return f"{h/24:.1f} dias"
    return f"{h:.1f} horas"

def build_report(repos: List[Dict[str, Any]]) -> str:
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    groups = group_by_language(repos)

    # Agregados por linguagem popular e outras
    per_lang: Dict[str, Dict[str, Any]] = {}
    popular_bucket: List[Dict[str, Any]] = []
    other_bucket: List[Dict[str, Any]] = []

    for lang, items in groups.items():
        if lang in POPULAR_LANGS:
            per_lang[lang] = summarize_group(items)
            popular_bucket.extend(items)
        else:
            other_bucket.extend(items)

    summary_popular = summarize_group(popular_bucket)
    summary_other = summarize_group(other_bucket) if other_bucket else None

    langs_present = [l for l in POPULAR_LANGS if l in per_lang]
    rank_prs = sorted(langs_present, key=lambda l: per_lang[l]["prs_mean"], reverse=True)
    rank_rels = sorted(langs_present, key=lambda l: per_lang[l]["rels_mean"], reverse=True)
    rank_freq = sorted(langs_present, key=lambda l: per_lang[l]["hrs_mean"])  # crescente = mais frequente

    lines: List[str] = []
    lines.append("Relatório RQ07 - Contribuição, Releases e Frequência de Atualização por Linguagem")
    lines.append(f"Gerado em: {created_at}")
    lines.append("")
    lines.append("Pergunta:")
    lines.append("RQ07: Sistemas escritos em linguagens mais populares recebem mais contribuição externa,")
    lines.append("lançam mais releases e são atualizados com mais frequência?")
    lines.append("")
    lines.append("Resumo do conjunto de dados:")
    lines.append(f"- Repositórios analisados: {len(repos)}")
    lines.append(f"- Linguagens totais encontradas: {len(groups)}")
    lines.append(f"- Linguagens populares presentes: {', '.join(langs_present) if langs_present else 'nenhuma'}")
    if other_bucket:
        lines.append(f"- Repositórios em outras linguagens: {len(other_bucket)}")
    lines.append("")

    lines.append("Métricas por linguagem popular (média; mediana entre parênteses):")
    if not langs_present:
        lines.append("Nenhuma das linguagens populares do gráfico foi encontrada no arquivo de entrada.")
    else:
        for l in langs_present:
            s = per_lang[l]
            lines.append(
                f"- {l} (n={s['count']}): "
                f"PRs aceitos {s['prs_mean']:.1f} ({s['prs_median']:.1f}), "
                f"releases {s['rels_mean']:.1f} ({s['rels_median']:.1f}), "
                f"tempo desde última atualização {format_hours_as_human(s['hrs_mean'])} "
                f"({format_hours_as_human(s['hrs_median'])})"
            )
    lines.append("")

    if langs_present:
        lines.append("Rankings entre linguagens populares:")
        lines.append("1) Contribuição externa (PRs aceitos, média): " + " > ".join(rank_prs))
        lines.append("2) Releases (média): " + " > ".join(rank_rels))
        lines.append("3) Frequência de atualização (menor tempo desde última atualização é melhor): " + " > ".join(rank_freq))
        lines.append("")

    if summary_other and summary_other["count"] > 0:
        lines.append("Comparação agregado (Populares) vs (Outras linguagens):")
        lines.append(f"- PRs aceitos (média): Populares={summary_popular['prs_mean']:.1f} vs Outras={summary_other['prs_mean']:.1f}")
        lines.append(f"- Releases (média): Populares={summary_popular['rels_mean']:.1f} vs Outras={summary_other['rels_mean']:.1f}")
        lines.append(f"- Tempo desde última atualização (média, menor é melhor): Populares={format_hours_as_human(summary_popular['hrs_mean'])} vs Outras={format_hours_as_human(summary_other['hrs_mean'])}")
        pop_prs_better = summary_popular["prs_mean"] > summary_other["prs_mean"]
        pop_rels_better = summary_popular["rels_mean"] > summary_other["rels_mean"]
        pop_update_better = summary_popular["hrs_mean"] < summary_other["hrs_mean"]
        lines.append("")
        lines.append("Conclusão (agregado):")
        lines.append(f"- Contribuição externa maior em linguagens populares? {'SIM' if pop_prs_better else 'NÃO'}")
        lines.append(f"- Mais releases em linguagens populares? {'SIM' if pop_rels_better else 'NÃO'}")
        lines.append(f"- Atualizados mais frequentemente em populares? {'SIM' if pop_update_better else 'NÃO'}")
        lines.append("")
    else:
        lines.append("Não há dados suficientes em 'Outras linguagens' para comparação agregada.")
        lines.append("Interprete os rankings entre linguagens populares com cautela.")
        lines.append("")

    lines.append("Notas e limitações:")
    lines.append("- Os dados provêm dos repositórios do arquivo resultado.txt (amostra pode ser enviesada).")
    lines.append("- A métrica de atualização usa 'horas desde a última atualização' (menor é melhor).")
    lines.append("- Métricas são médias/medianas; amostras pequenas por linguagem podem distorcer resultados.")
    return "\n".join(lines)

def write_report(text: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

import csv

def write_csv(repos: list, path: str) -> None:
    """Gera um arquivo CSV com separador ';' para melhor compatibilidade com Excel."""
    if not repos:
        return
    fieldnames = [
        "id",
        "repo",
        "idade_anos",
        "prs_aceitos",
        "total_releases",
        "last_update_hours",
        "language",
        "closed_issues_ratio",
    ]
    with open(path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in repos:
            row = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(row)

def main():

    in_path = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE
    csv_path = "repositorios.csv"

    if not os.path.exists(in_path):
        print(f"Arquivo de entrada não encontrado: {in_path}")
        sys.exit(1)

    repos = parse_resultado(in_path)
    if not repos:
        print("Nenhum repositório válido foi encontrado no arquivo de entrada.")
        sys.exit(1)

    report = build_report(repos)
    write_report(report, out_path)
    write_csv(repos, csv_path)
    print(f"Relatório gerado com sucesso em: {out_path}")
    print(f"Arquivo CSV gerado com sucesso em: {csv_path}")

if __name__ == "__main__":
    main()