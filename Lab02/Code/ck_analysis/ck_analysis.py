import csv
import requests
import zipfile
import os
import shutil
import time
import subprocess
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

NUM_REPOS_TO_ANALYZE = 1000
NUM_THREADS = 16
BLOCO = 200

CK_JAR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "CK", "ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"))
Log4j_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "CK", "log4j.properties"))

BASE_CVS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Docs"))
BASE_CK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "Docs"))
REPOS_DIR = os.path.join(BASE_CK_DIR, "repos")
REPOS_CSV = os.path.join(BASE_CVS_DIR, "repos_java_metrics.csv")

os.makedirs(REPOS_DIR, exist_ok=True)

def get_repos_list(csv_file, num_repos) -> List[dict]:
    repos = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= num_repos:
                break
            full_name = f"{row['owner']}/{row['Repo']}"
            repos.append({'full_name': full_name})
    return repos

def download_and_extract_zip(full_name: str) -> Optional[str]:
    owner, repo = full_name.split("/")
    extract_path = os.path.join(REPOS_DIR, f"{owner}__{repo}")

    # NOVO: Checa se já existe pasta extraída e não está vazia
    if os.path.isdir(extract_path) and os.listdir(extract_path):
        # Busca o subdiretório extraído (padrão do zip)
        repo_dirs = [os.path.join(extract_path, d) for d in os.listdir(extract_path)]
        if repo_dirs:
            print(f"Já existe extração para {full_name} em {repo_dirs[0]}")
            return repo_dirs[0]

    for branch in ["main", "master"]:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        zip_path = os.path.join(REPOS_DIR, f"{owner}__{repo}__{branch}.zip")
        try:
            r = requests.get(zip_url, timeout=60)
            if r.status_code == 200:
                with open(zip_path, "wb") as f:
                    f.write(r.content)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                os.remove(zip_path)
                # Pega o diretório extraído dentro da pasta (nome padrão do zip)
                [repo_dir] = [os.path.join(extract_path, d) for d in os.listdir(extract_path)]
                return repo_dir
        except Exception as e:
            continue  # tenta o próximo branch
    print(f"Erro ao baixar/extrair {full_name}")
    return None

def run_ck_on_repo(repo_path, repo_name):
    result = subprocess.run([
        "java",
        f"-Dlog4j.configuration=file:{Log4j_file}",
        "-jar", CK_JAR_PATH, repo_path
    ], cwd=os.getcwd())
    if result.returncode != 0:
        print(f"Erro ao rodar CK em {repo_path}")

def process_download(full_name):
    return (full_name, download_and_extract_zip(full_name))

def process_ck(full_name, repo_dir):
    if repo_dir:
        run_ck_on_repo(repo_dir, full_name)

def process_delete(repo_dir):
    shutil.rmtree(os.path.dirname(repo_dir), ignore_errors=True)

if __name__ == "__main__":
    total_start = time.perf_counter()
    repos = get_repos_list(REPOS_CSV, NUM_REPOS_TO_ANALYZE)
    num_blocos = (len(repos) + BLOCO - 1) // BLOCO
    print(f"Iniciando processamento em blocos de {BLOCO} com até {NUM_THREADS} threads por bloco...")

    for bloco_idx in range(num_blocos):
        bloco_repos = repos[bloco_idx*BLOCO : (bloco_idx+1)*BLOCO]
        print(f"\nProcessando bloco {bloco_idx+1}/{num_blocos} ({len(bloco_repos)} repositórios)")

        # Download em paralelo
        download_results = []
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = [executor.submit(process_download, repo["full_name"]) for repo in bloco_repos]
            for i, future in enumerate(as_completed(futures), 1):
                full_name, repo_dir = future.result()
                download_results.append((full_name, repo_dir))
                print(f"[{i}/{len(bloco_repos)}] Download {full_name} {'OK' if repo_dir else 'ERRO'}")

        # Rodar CK (paralelo)
        print("Rodando CK no bloco...")
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = [executor.submit(process_ck, full_name, repo_dir) for (full_name, repo_dir) in download_results if repo_dir]
            for i, future in enumerate(as_completed(futures), 1):
                future.result()
                print(f"[{i}/{len(futures)}] CK concluído")

        # 3. Excluir pastas
        print("Limpando diretórios do bloco...")
        for (full_name, repo_dir) in download_results:
            if repo_dir:
                process_delete(repo_dir)

    total_elapsed = time.perf_counter() - total_start
    print(f"\nAnálise CK concluída para {NUM_REPOS_TO_ANALYZE} repositório(s) em {total_elapsed:.2f} segundos.")