import requests
from datetime import datetime, timezone
import time
import os
import csv

token = os.getenv('GIT_TOKEN')
print(token)
headers = {"Authorization": f"bearer {token}"}

def get_popular_repos(num_repos):
    repos = []
    page = 1
    per_page = 100
    while len(repos) < num_repos:
        to_fetch = min(per_page, num_repos - len(repos))
        url = f"https://api.github.com/search/repositories?q=stars:>10000&sort=stars&order=desc&per_page={to_fetch}&page={page}"
        response = requests.get(url, headers={"Authorization": f"token {token}"})
        if response.status_code == 200:
            items = response.json()["items"]
            repos.extend([
                {
                    "owner": repo["owner"]["login"],
                    "name": repo["name"],
                    "stars": repo["stargazers_count"]  # Pega as estrelas da REST!
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
            mergedPRs: pullRequests(states: MERGED) {{ totalCount }}
            closedIssues: issues(states: CLOSED) {{ totalCount }}
            openIssues: issues(states: OPEN) {{ totalCount }}
        }}
        '''
    query += "}"
    return query

def parse_repo_data(data, batch_repos, start_id):
    rows = []
    today = datetime.now(timezone.utc)
    for idx, ((key, repo), repo_rest) in enumerate(zip(data.items(), batch_repos), start=start_id):
        name = repo.get('name', 'N/A')
        stars = repo_rest.get('stars', 0)  # Estrelas vindas da REST!
        created_at = datetime.strptime(repo['createdAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        updated_at = datetime.strptime(repo['updatedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age_years = round((today - created_at).days / 365, 2)
        delta = today - updated_at
        last_update = delta.days if delta.days >= 1 else round(delta.total_seconds() / 3600, 1)
        last_update_str = f"{last_update} dias" if delta.days >= 1 else f"{last_update} horas"
        language = repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else 'N/A'
        releases = repo.get('releases', {}).get('totalCount', 0)
        pr_merged_count = repo.get('mergedPRs', {}).get('totalCount', 0)
        closed_issues = repo.get('closedIssues', {}).get('totalCount', 0)
        open_issues = repo.get('openIssues', {}).get('totalCount', 0)
        total_issues = closed_issues + open_issues
        ratio = round(closed_issues / total_issues, 2) if total_issues > 0 else 0

        row = {
            "id": idx,
            "Repo": name,
            "Estrelas": stars,
            "Idade (anos)": age_years,
            "PRs aceitos": pr_merged_count,
            "Total releases": releases,
            "Dias desde última atualização": last_update_str,
            "Linguagem primária": language,
            "Percentual issues fechadas": ratio
        }
        rows.append(row)
    return rows

def batch_collect_repo_info_graphql_csv(repos, batch_size=10, max_retries=3, sleep_on_error=10):
    all_rows = []
    id_counter = 1
    total_batches = (len(repos) + batch_size - 1) // batch_size
    for batch_idx in range(total_batches):
        batch = repos[batch_idx * batch_size : (batch_idx + 1) * batch_size]
        query = build_graphql_query(batch)
        for attempt in range(max_retries):
            response = requests.post(
                'https://api.github.com/graphql',
                json={'query': query},
                headers=headers
            )
            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception as e:
                    print("Erro ao decodificar JSON:", response.text)
                    raise
                if "errors" in result:
                    print(result["errors"])
                    raise Exception("Erro na consulta GraphQL")
                data = result['data']
                batch_rows = parse_repo_data(data, batch, id_counter)
                all_rows.extend(batch_rows)
                id_counter += len(batch)
                time.sleep(0.5)
                break  # Sucesso, não precisa tentar mais
            else:
                print(f"Erro: status {response.status_code} (tentativa {attempt+1}/{max_retries})")
                print(response.text)
                if response.status_code == 502 and attempt < max_retries - 1:
                    time.sleep(sleep_on_error)
                else:
                    raise Exception("Falha na consulta GraphQL")
    return all_rows

if __name__ == "__main__":
    num_repos = 1000  
    start = time.time()
    try:
        popular_repos = get_popular_repos(num_repos)
        rows = batch_collect_repo_info_graphql_csv(popular_repos, batch_size=10)
        end = time.time()
        elapsed = end - start
        fieldnames = [
            "id", "Repo", "Estrelas", "Idade (anos)", "PRs aceitos", "Total releases",
            "Dias desde última atualização", "Linguagem primária", "Percentual issues fechadas"
        ]
        with open("resultado.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        print(f"Arquivo resultado.csv gerado com sucesso em {elapsed:.2f} segundos.")
    except Exception as e:
        print(e)