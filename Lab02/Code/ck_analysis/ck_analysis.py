import csv
import subprocess
import os
import shutil

NUM_REPOS_TO_ANALYZE = 1

CK_JAR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "CK", "ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"))

BASE_CVS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),"..", "..", "Docs"))
BASE_CK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "Docs"))
REPOS_DIR = os.path.join(BASE_CK_DIR, "repos")
REPOS_CSV = os.path.join(BASE_CVS_DIR, "repos_java_metrics.csv")

os.makedirs(REPOS_DIR, exist_ok=True)

def get_repos_list(csv_file, num_repos):
    repos = []
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= num_repos:
                break
            full_name = f"{row['owner']}/{row['Repo']}"
            repos.append({'full_name': full_name})
    return repos

def clone_repo(full_name):
    repo_url = f"https://github.com/{full_name}.git"
    target_path = os.path.join(REPOS_DIR, full_name.replace("/", "__"))
    if os.path.exists(target_path):
        print(f"Já existe clone: {target_path}")
        return target_path
    print(f"Clonando {repo_url} em {target_path} ...")
    result = subprocess.run(["git", "clone", "--depth=1", repo_url, target_path])
    if result.returncode != 0:
        print(f"Erro ao clonar {repo_url}")
        return None
    return target_path

def run_ck_on_repo(repo_path, repo_name):
    print(f"Rodando CK em {repo_path} ...")
    result = subprocess.run([
        "java", "-jar", CK_JAR_PATH, repo_path
    ], cwd=os.getcwd())
    if result.returncode != 0:
        print(f"Erro ao rodar CK em {repo_path}")
        return

if __name__ == "__main__":
    repos = get_repos_list(REPOS_CSV, NUM_REPOS_TO_ANALYZE)
    for repo in repos:
        full_name = repo["full_name"]
        repo_path = clone_repo(full_name)
        if repo_path:
            run_ck_on_repo(repo_path, full_name)
    print(f"\nAnálise CK concluída para {NUM_REPOS_TO_ANALYZE} repositório(s).")