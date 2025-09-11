import requests
import os
import time
import csv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

token = os.getenv('GIT_TOKEN')
headers = {"Authorization": f"bearer {token}"}

def get_popular_java_repos(num_repos, per_page=100):
    repos = []
    page = 1
    while len(repos) < num_repos:
        to_fetch = min(per_page, num_repos - len(repos))
        url = f"https://api.github.com/search/repositories?q=language:Java+stars:>0&sort=stars&order=desc&per_page={to_fetch}&page={page}"
        response = requests.get(url, headers={"Authorization": f"token {token}"})
        if response.status_code == 200:
            items = response.json()["items"]
            repos.extend([
                {
                    "owner": repo["owner"]["login"],
                    "name": repo["name"],
                    "stars": repo["stargazers_count"]
                }
                for repo in items
            ])
            if len(items) < to_fetch:
                break
        else:
            print(response.json())
            raise Exception(f"Failed to fetch repositories: {response.status_code}")
        page += 1
    return repos[:num_repos]

def build_graphql_query(repos):
    query = "query {"
    for i, repo in enumerate(repos):
        alias = f"repo{i}"
        query += f'''
        {alias}: repository(owner: "{repo['owner']}", name: "{repo['name']}") {{
            name
            createdAt
            updatedAt
            primaryLanguage {{ name }}
            releases {{ totalCount }}
        }}
        '''
    query += "}"
    return query

def parse_repo_data(data, batch_repos, start_id):
    rows = []
    today = datetime.now(timezone.utc)
    for idx, ((key, repo), repo_rest) in enumerate(zip(data.items(), batch_repos), start=start_id):
        name = repo.get('name', 'N/A')
        stars = repo_rest.get('stars', 0)
        created_at = datetime.strptime(repo['createdAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        updated_at = datetime.strptime(repo['updatedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age_years = round((today - created_at).days / 365, 2)
        last_update = (today - updated_at).days
        language = repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else 'N/A'
        releases = repo.get('releases', {}).get('totalCount', 0)

        row = {
            "id": idx,
            "owner": repo_rest.get("owner", "N/A"),
            "Repo": name,
            "Estrelas": stars,
            "Idade (anos)": age_years,
            "Total releases": releases,
            "Dias desde última atualização": last_update,
            "Linguagem primária": language
        }
        rows.append(row)
    return rows

def get_repo_and_graphql(batch_info):
    batch, batch_idx, start_id = batch_info
    query = build_graphql_query(batch)
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query},
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        if "errors" in result:
            print(result["errors"])
            raise Exception("Erro na consulta GraphQL")
        data = result['data']
        batch_rows = parse_repo_data(data, batch, start_id)
        return batch_rows
    else:
        print(f"Erro: status {response.status_code}")
        print(response.text)
        raise Exception("Falha na consulta GraphQL")

if __name__ == "__main__":
    num_repos = 1000
    batch_size = 10
    start = time.time()
    try:
        popular_repos = get_popular_java_repos(num_repos)
        repo_batches = [
            (popular_repos[i:i+batch_size], idx, i+1)
            for idx, i in enumerate(range(0, len(popular_repos), batch_size))
        ]
        all_rows = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_batch = {
                executor.submit(get_repo_and_graphql, batch_info): batch_info
                for batch_info in repo_batches
            }
            for future in as_completed(future_to_batch):
                batch_results = future.result()
                all_rows.extend(batch_results)
        end = time.time()
        fieldnames = [
            "id", "owner", "Repo", "Estrelas", "Idade (anos)", "Total releases",
            "Dias desde última atualização", "Linguagem primária"
        ]
        with open("repos_java_metrics.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_rows:
                writer.writerow(row)
        print(f"Arquivo repos_java_metrics.csv gerado com sucesso em {end-start:.2f} segundos.")
    except Exception as e:
        print(e)