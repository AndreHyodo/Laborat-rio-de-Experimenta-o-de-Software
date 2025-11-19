"""Benchmark Runner para comparar REST vs GraphQL.

Uso (após criar config.yaml a partir de config.example.yaml):

    python Lab05/Code/benchmark_runner.py --config Lab05/Code/config.yaml

Saídas: arquivos CSV para REST e GraphQL em Lab05/Data/.
Cada linha inclui: trial_id, type, label/name, latency_ms, payload_bytes, status_code, timestamps, error
"""
from __future__ import annotations
import argparse
import csv
import os
import random
import time
from typing import List, Dict, Any
import yaml
import os

from rest_client import RestClient
from graphql_client import GraphQLClient

OUTPUT_REST = os.path.join("Lab05", "Data", "rest_results.csv")
OUTPUT_GQL = os.path.join("Lab05", "Data", "graphql_results.csv")


def _expand_env(value):
    if isinstance(value, str):
        # Suporta ${ENV_VAR} em strings
        parts = []
        i = 0
        while i < len(value):
            if value.startswith("${", i):
                j = value.find("}", i + 2)
                if j != -1:
                    env_key = value[i + 2 : j]
                    parts.append(os.environ.get(env_key, ""))
                    i = j + 1
                    continue
            parts.append(value[i])
            i += 1
        return "".join(parts)
    elif isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _expand_env(data)


def ensure_dirs():
    os.makedirs(os.path.join("Lab05", "Data"), exist_ok=True)


def write_csv(path: str, rows: List[Dict[str, Any]]):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerows(rows)


def _compose_headers(cfg: Dict[str, Any]) -> Dict[str, str]:
    headers = dict(cfg.get("metrics", {}).get("extra_headers", {}) or {})
    headers.setdefault("User-Agent", "Lab05-Benchmark/1.0")
    return headers


def run_rest_trials(cfg: Dict[str, Any], benchmark_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    rest_cfg = cfg["rest"]
    headers = _compose_headers(cfg)
    client = RestClient(rest_cfg["base_url"], default_headers=headers, timeout=benchmark_cfg.get("timeout_seconds", 10))
    trials = benchmark_cfg["trials"]
    sleep_ms = benchmark_cfg.get("sleep_between_ms", 0)
    endpoints = rest_cfg.get("endpoints", [])
    rows: List[Dict[str, Any]] = []
    for t in range(trials):
        for ep in endpoints:
            result = client.fetch(ep["path"], label=ep.get("label", ep["path"]))
            rows.append({
                "trial_id": t,
                "type": "REST",
                "label": result.label,
                "url": result.url,
                "latency_ms": round(result.latency_ms, 3),
                "payload_bytes": result.payload_bytes,
                "status_code": result.status_code,
                "timestamp_start": result.timestamp_start,
                "timestamp_end": result.timestamp_end,
                "error": result.error or ""
            })
            if sleep_ms:
                time.sleep(sleep_ms / 1000.0)
    return rows


def run_graphql_trials(cfg: Dict[str, Any], benchmark_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    gql_cfg = cfg["graphql"]
    headers = _compose_headers(cfg)
    client = GraphQLClient(gql_cfg["url"], headers=headers, timeout=benchmark_cfg.get("timeout_seconds", 10))
    trials = benchmark_cfg["trials"]
    sleep_ms = benchmark_cfg.get("sleep_between_ms", 0)
    queries = gql_cfg.get("queries", [])
    rows: List[Dict[str, Any]] = []
    for t in range(trials):
        for q in queries:
            result = client.execute(q["name"], q["query"], variables=q.get("variables"))
            rows.append({
                "trial_id": t,
                "type": "GraphQL",
                "name": result.name,
                "url": result.url,
                "latency_ms": round(result.latency_ms, 3),
                "payload_bytes": result.payload_bytes,
                "status_code": result.status_code,
                "timestamp_start": result.timestamp_start,
                "timestamp_end": result.timestamp_end,
                "error": result.error or ""
            })
            if sleep_ms:
                time.sleep(sleep_ms / 1000.0)
    return rows


def maybe_randomize(order: List[str], flag: bool) -> List[str]:
    if flag:
        random.shuffle(order)
    return order


def main():
    parser = argparse.ArgumentParser(description="Benchmark REST vs GraphQL")
    parser.add_argument("--config", required=True, help="Caminho para config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    benchmark_cfg = cfg.get("benchmark", {})
    ensure_dirs()

    exec_order = maybe_randomize(["REST", "GraphQL"], benchmark_cfg.get("randomize_order", False))
    print(f"Ordem de execução: {exec_order}")

    rest_rows = []
    gql_rows = []

    for kind in exec_order:
        if kind == "REST":
            print("Iniciando trials REST...")
            rest_rows = run_rest_trials(cfg, benchmark_cfg)
            write_csv(OUTPUT_REST, rest_rows)
            print(f"REST concluído: {len(rest_rows)} medições")
        else:
            print("Iniciando trials GraphQL...")
            gql_rows = run_graphql_trials(cfg, benchmark_cfg)
            write_csv(OUTPUT_GQL, gql_rows)
            print(f"GraphQL concluído: {len(gql_rows)} medições")

    print("Benchmark finalizado.")
    print("Arquivos gerados:")
    print(f" - {OUTPUT_REST} ({len(rest_rows)} linhas)")
    print(f" - {OUTPUT_GQL} ({len(gql_rows)} linhas)")


if __name__ == "__main__":
    main()
