import requests
from datetime import datetime, timezone
import time
import os

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
                {"owner": repo["owner"]["login"], "name": repo["name"]}
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

def parse_repo_data(data, start_id):
    lines = []
    today = datetime.now(timezone.utc)
    for idx, (key, repo) in enumerate(data.items(), start=start_id):
        name = repo.get('name', 'N/A')
        created_at = datetime.strptime(repo['createdAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        updated_at = datetime.strptime(repo['updatedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age_years = round((today - created_at).days / 365, 2)
        delta = today - updated_at
        last_update = f"{delta.days} dias" if delta.days >= 1 else f"{int(delta.total_seconds() // 3600)} horas"
        language = repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else 'N/A'
        releases = repo.get('releases', {}).get('totalCount', 0)
        pr_merged_count = repo.get('mergedPRs', {}).get('totalCount', 0)
        closed_issues = repo.get('closedIssues', {}).get('totalCount', 0)
        open_issues = repo.get('openIssues', {}).get('totalCount', 0)
        total_issues = closed_issues + open_issues
        ratio = round(closed_issues / total_issues, 2) if total_issues > 0 else 0

        lines.append(f"id: {idx}")
        lines.append(f"Repo: {name}")
        lines.append(f"Idade (anos): {age_years}")
        lines.append(f"PRs aceitos: {pr_merged_count}")
        lines.append(f"Total releases: {releases}")
        lines.append(f"Dias desde última atualização: {last_update}")
        lines.append(f"Linguagem primária: {language}")
        lines.append(f"Percentual issues fechadas: {ratio}")
        lines.append("-" * 40)
    return lines

def batch_collect_repo_info_graphql(repos, batch_size=20):
    all_lines = []
    id_counter = 1
    total_batches = (len(repos) + batch_size - 1) // batch_size
    for batch_idx in range(total_batches):
        batch = repos[batch_idx * batch_size : (batch_idx + 1) * batch_size]
        query = build_graphql_query(batch)
        response = requests.post(
            'https://api.github.com/graphql',
            json={'query': query},
            headers=headers
        )
        if response.status_code != 200:
            print(f"Erro: status {response.status_code}")
            print(response.text)
            raise Exception("Falha na consulta GraphQL")
        try:
            result = response.json()
        except Exception as e:
            print("Erro ao decodificar JSON:", response.text)
            raise
        if "errors" in result:
            print(result["errors"])
            raise Exception("Erro na consulta GraphQL")
        data = result['data']
        batch_lines = parse_repo_data(data, id_counter)
        all_lines.extend(batch_lines)
        id_counter += len(batch)
        time.sleep(0.5)
    return all_lines

if __name__ == "__main__":
    num_repos = 1000  
    start = time.time()
    try:
        popular_repos = get_popular_repos(num_repos)
        output_lines = batch_collect_repo_info_graphql(popular_repos, batch_size=20)
        end = time.time()
        elapsed = end - start
        output_lines.append("")
        output_lines.append(f"Tempo de execução: {elapsed:.2f} segundos")
        with open("resultado.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        print("Arquivo resultado.txt gerado com sucesso.")
    except Exception as e:
        print(e)