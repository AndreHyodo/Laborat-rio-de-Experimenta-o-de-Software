#!/usr/bin/env python3
"""
Este módulo é responsável por coletar dados do GitHub API para análise de code review.
Coleta repositórios populares e seus pull requests conforme critérios definidos.
"""

import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class GitHubCollector:
    """Coletor de dados do GitHub API."""
    
    def __init__(self, token: str):
        """
        Inicializa o coletor com token de autenticação.
        
        Args:
            token: Token de acesso pessoal do GitHub
        """
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.logger = logging.getLogger(__name__)
        
        self.requests_made = 0
        self.requests_limit = 5000
        
    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """
        Faz requisição para a API do GitHub com rate limiting.
        
        Args:
            url: URL para requisição
            params: Parâmetros da query
            
        Returns:
            Resposta JSON da API
        """
        if params is None:
            params = {}
            
        if self.requests_made >= self.requests_limit - 100:
            self.logger.warning("Aproximando do limite de requisições, aguardando...")
            time.sleep(60)
            self.requests_made = 0
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            self.requests_made += 1
            
            if response.status_code == 403:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = reset_time - int(time.time()) + 1
                self.logger.info(f"Rate limit excedido, aguardando {sleep_time}s...")
                time.sleep(max(sleep_time, 60))
                return self._make_request(url, params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição {url}: {str(e)}")
            raise
    
    def collect_popular_repositories(self, limit: int = 200, min_prs: int = 100) -> pd.DataFrame:
        """
        Coleta repositórios populares do GitHub.
        
        Args:
            limit: Número máximo de repositórios a coletar
            min_prs: Número mínimo de PRs que o repositório deve ter
            
        Returns:
            DataFrame com informações dos repositórios
        """
        self.logger.info(f"Coletando {limit} repositórios populares...")
        repositories = []
        page = 1
        per_page = 100
        
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
                prs_count = self._count_pull_requests(repo['full_name'])
                
                if prs_count >= min_prs:
                    repo_info = {
                        'full_name': repo['full_name'],
                        'name': repo['name'],
                        'owner': repo['owner']['login'],
                        'stars': repo['stargazers_count'],
                        'forks': repo['forks_count'],
                        'language': repo['language'],
                        'created_at': repo['created_at'],
                        'updated_at': repo['updated_at'],
                        'prs_count': prs_count,
                        'url': repo['html_url']
                    }
                    repositories.append(repo_info)
                    self.logger.info(f"Repositório adicionado: {repo['full_name']} ({prs_count} PRs)")
                
                if len(repositories) >= limit:
                    break
            
            page += 1
            
            if page > 50:
                break
        
        df = pd.DataFrame(repositories)
        self.logger.info(f"Coletados {len(df)} repositórios que atendem aos critérios")
        return df
    
    def _count_pull_requests(self, repo_full_name: str) -> int:
        """
        Conta o número de pull requests de um repositório.
        
        Args:
            repo_full_name: Nome completo do repositório (owner/repo)
            
        Returns:
            Número de PRs merged + closed
        """
        try:
            url = f"{self.base_url}/search/issues"
            params = {
                'q': f'repo:{repo_full_name} type:pr is:merged',
                'per_page': 1
            }
            merged_data = self._make_request(url, params)
            merged_count = merged_data.get('total_count', 0)
            
            params['q'] = f'repo:{repo_full_name} type:pr is:closed'
            closed_data = self._make_request(url, params)
            closed_count = closed_data.get('total_count', 0)
            
            return merged_count + closed_count
            
        except Exception as e:
            self.logger.warning(f"Erro ao contar PRs de {repo_full_name}: {str(e)}")
            return 0
    
    def collect_pull_requests(self, repositories_df: pd.DataFrame) -> pd.DataFrame:
        """
        Coleta pull requests dos repositórios selecionados.
        
        Args:
            repositories_df: DataFrame com os repositórios selecionados
            
        Returns:
            DataFrame com os pull requests coletados
        """
        self.logger.info(f"Coletando PRs de {len(repositories_df)} repositórios...")
        all_prs = []
        
        for idx, repo in repositories_df.iterrows():
            repo_name = repo['full_name']
            self.logger.info(f"Coletando PRs de {repo_name} ({idx+1}/{len(repositories_df)})")
            
            try:
                prs = self._collect_repo_pull_requests(repo_name)
                all_prs.extend(prs)
                self.logger.info(f"Coletados {len(prs)} PRs de {repo_name}")
                
            except Exception as e:
                self.logger.error(f"Erro ao coletar PRs de {repo_name}: {str(e)}")
                continue
        
        df = pd.DataFrame(all_prs)
        self.logger.info(f"Total de PRs coletados: {len(df)}")
        return df
    
    def _collect_repo_pull_requests(self, repo_full_name: str) -> List[Dict]:
        """
        Coleta pull requests de um repositório específico.
        
        Args:
            repo_full_name: Nome completo do repositório
            
        Returns:
            Lista de pull requests
        """
        prs = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/repos/{repo_full_name}/pulls"
            params = {
                'state': 'closed',
                'per_page': per_page,
                'page': page,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            data = self._make_request(url, params)
            
            if not data:
                break
            
            for pr in data:
                if not self._meets_criteria(pr, repo_full_name):
                    continue
                
                pr_info = self._extract_pr_info(pr, repo_full_name)
                if pr_info:
                    prs.append(pr_info)
            
            if len(data) < per_page:
                break
                
            page += 1
            
            if page > 10:
                break
        
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