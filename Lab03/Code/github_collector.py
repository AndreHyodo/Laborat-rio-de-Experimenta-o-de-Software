import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class GitHubCollector:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.logger = logging.getLogger(__name__)

    def _make_request(self, url: str, params: Dict = None, method: str = "get") -> Dict:
        if params is None:
            params = {}
        while True:
            try:
                response = (
                    requests.get(url, headers=self.headers, params=params)
                    if method == "get"
                    else requests.post(url, headers=self.headers, json=params)
                )
                remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
                reset = int(response.headers.get("X-RateLimit-Reset", 0))
                if remaining < 10 or (response.status_code == 403 and remaining == 0):
                    wait = max(reset - int(time.time()), 1)
                    self.logger.warning(f"Rate limit quase/excedido, aguardando {wait}s...")
                    time.sleep(wait + 5)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Erro na requisição {url}: {str(e)}")
                time.sleep(10)
                continue

    def collect_popular_repositories(self, limit: int = 50, min_prs: int = 100) -> pd.DataFrame:
        self.logger.info(f"Coletando {limit} repositórios populares...")
        repositories = []
        page = 1
        per_page = 50

        while len(repositories) < limit:
            self.logger.info(f"Buscando repositórios - página {page}")
            url = f"{self.base_url}/search/repositories"
            params = {
                'q': 'stars:>1000 language:python',
                'sort': 'stars',
                'order': 'desc',
                'per_page': per_page,
                'page': page
            }
            data = self._make_request(url, params)
            if not data.get('items'):
                break

            for repo in data['items']:
                repo_info = {
                    'full_name': repo['full_name'],
                    'name': repo['name'],
                    'owner': repo['owner']['login'],
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'language': repo['language'],
                    'created_at': repo['created_at'],
                    'updated_at': repo['updated_at'],
                    'url': repo['html_url']
                }
                repositories.append(repo_info)
                if len(repositories) >= limit:
                    break
            page += 1
            if page > 10: break
        df = pd.DataFrame(repositories)
        self.logger.info(f"Coletados {len(df)} repositórios")
        return df

    def collect_pull_requests(self, repositories_df: pd.DataFrame, min_prs: int = 100) -> pd.DataFrame:
        self.logger.info(f"Coletando PRs de {len(repositories_df)} repositórios...")
        all_prs = []
        for idx, repo in repositories_df.iterrows():
            repo_name = repo['full_name']
            self.logger.info(f"Coletando PRs de {repo_name} ({idx+1}/{len(repositories_df)})")
            try:
                prs = self._collect_repo_pull_requests(repo_name, min_prs=min_prs)
                all_prs.extend(prs)
                # self.logger.info(f"Coletados {len(prs)} PRs de {repo_name}")
            except Exception as e:
                self.logger.error(f"Erro ao coletar PRs de {repo_name}: {str(e)}")
                time.sleep(5)
                continue
        df = pd.DataFrame(all_prs)
        self.logger.info(f"Total de PRs coletados: {len(df)}")
        return df
    
    def collect_pull_requests_of_repo(self, owner: str, repo: str, min_prs: int = 100) -> pd.DataFrame:
        """
        Coleta os PRs de um único repositório (owner/repo) e retorna DataFrame.
        """
        repo_full_name = f"{owner}/{repo}"
        try:
            prs = self._collect_repo_pull_requests(repo_full_name, min_prs=min_prs)
            df = pd.DataFrame(prs)
            # self.logger.info(f"Coletados {len(df)} PRs de {repo_full_name}")
            return df
        except Exception as e:
            self.logger.error(f"Erro ao coletar PRs de {repo_full_name}: {str(e)}")
            return pd.DataFrame()

    def _collect_repo_pull_requests(self, repo_full_name: str, min_prs: int = 100) -> List[Dict]:
        prs = []
        page = 1
        per_page = 100
        collected = 0
        while collected < min_prs:
            url = f"{self.base_url}/repos/{repo_full_name}/pulls"
            params = {
                'state': 'closed',
                'per_page': per_page,
                'page': page,
                'sort': 'updated',
                'direction': 'desc'
            }
            data = self._make_request(url, params)
            if not data: break
            for pr in data:
                # Use apenas campos já disponíveis aqui!
                pr_info = {
                    'repository': repo_full_name,
                    'pr_number': pr['number'],
                    'title': pr['title'],
                    'state': pr['state'],
                    'merged_at': pr.get('merged_at'),
                    'created_at': pr['created_at'],
                    'closed_at': pr.get('closed_at'),
                    'author': pr['user']['login'],
                    'url': pr['html_url'],
                    'additions': pr.get('additions'),
                    'deletions': pr.get('deletions'),
                    'changed_files': pr.get('changed_files')
                }
                prs.append(pr_info)
                collected += 1
                if collected >= min_prs:
                    break
            if len(data) < per_page: break
            page += 1
            if page > 10: break
        return prs
    
    def _meets_criteria(self, pr: Dict, repo_full_name: str) -> bool:
        """
        Verifica se o PR atende aos critérios de seleção.
        
        Args:
            pr: Dados do pull request
            repo_full_name: Nome do repositório
            
        Returns:
            True se atende aos critérios
        """
        is_merged = pr.get('merged_at') is not None
        is_closed = pr.get('state') == 'closed'
        
        if not (is_merged or is_closed):
            return False
        
        reviews_count = self._count_pr_reviews(repo_full_name, pr['number'])
        if reviews_count < 1:
            return False
        
        created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
        
        end_time_str = pr.get('merged_at') or pr.get('closed_at')
        if not end_time_str:
            return False
            
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        time_diff = end_time - created_at
        
        if time_diff < timedelta(hours=1):
            return False
        
        return True
    
    def _count_pr_reviews(self, repo_full_name: str, pr_number: int) -> int:
        """
        Conta o número de revisões de um PR.
        
        Args:
            repo_full_name: Nome do repositório
            pr_number: Número do PR
            
        Returns:
            Número de revisões
        """
        try:
            url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/reviews"
            data = self._make_request(url)
            return len(data) if data else 0
        except:
            return 0
    
    def _extract_pr_info(self, pr: Dict, repo_full_name: str) -> Optional[Dict]:
        """
        Extrai informações relevantes do pull request.
        
        Args:
            pr: Dados do PR da API
            repo_full_name: Nome do repositório
            
        Returns:
            Dicionário com informações do PR
        """
        try:
            pr_details = self._get_pr_details(repo_full_name, pr['number'])
            if not pr_details:
                return None
            
            reviews = self._get_pr_reviews(repo_full_name, pr['number'])
            
            comments = self._get_pr_comments(repo_full_name, pr['number'])
            
            pr_info = {
                'repository': repo_full_name,
                'pr_number': pr['number'],
                'title': pr['title'],
                'body': pr['body'] or '',
                'state': pr['state'],
                'is_merged': pr.get('merged_at') is not None,
                'created_at': pr['created_at'],
                'updated_at': pr['updated_at'],
                'closed_at': pr.get('closed_at'),
                'merged_at': pr.get('merged_at'),
                'author': pr['user']['login'],
                'author_association': pr.get('author_association', ''),
                
                'files_changed': pr_details.get('changed_files', 0),
                'additions': pr_details.get('additions', 0),
                'deletions': pr_details.get('deletions', 0),
                
                'reviews_count': len(reviews),
                'comments_count': len(comments),
                'participants': self._count_participants(pr, reviews, comments),
                
                'url': pr['html_url']
            }
            
            return pr_info
            
        except Exception as e:
            self.logger.warning(f"Erro ao extrair informações do PR {pr['number']}: {str(e)}")
            return None
    
    def _get_pr_details(self, repo_full_name: str, pr_number: int) -> Optional[Dict]:
        """Busca detalhes do PR."""
        try:
            url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}"
            return self._make_request(url)
        except:
            return None
    
    def _get_pr_reviews(self, repo_full_name: str, pr_number: int) -> List[Dict]:
        """Busca revisões do PR."""
        try:
            url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/reviews"
            return self._make_request(url) or []
        except:
            return []
    
    def _get_pr_comments(self, repo_full_name: str, pr_number: int) -> List[Dict]:
        """Busca comentários do PR."""
        try:
            url = f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/comments"
            review_comments = self._make_request(url) or []
            
            url = f"{self.base_url}/repos/{repo_full_name}/issues/{pr_number}/comments"
            issue_comments = self._make_request(url) or []
            
            return review_comments + issue_comments
        except:
            return []
    
    def _count_participants(self, pr: Dict, reviews: List[Dict], comments: List[Dict]) -> int:
        """Conta número único de participantes no PR."""
        participants = set()
        
        participants.add(pr['user']['login'])
        
        for review in reviews:
            participants.add(review['user']['login'])
        
        for comment in comments:
            participants.add(comment['user']['login'])
        
        return len(participants)