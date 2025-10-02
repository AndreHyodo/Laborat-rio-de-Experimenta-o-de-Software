#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_collector import GitHubCollector
# from arquivosRestantesLab03.metrics_calculator import MetricsCalculator
# from arquivosRestantesLab03.statistical_analyzer import StatisticalAnalyzer
# from arquivosRestantesLab03.data_visualizer import DataVisualizer

def setup_logging(log_level='INFO'):
    """Configure logging for the application."""
    log_dir = os.path.join(os.path.dirname(__file__), '../Results')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'lab03.log')

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def parallel_collect_pull_requests(collector, repos_df, max_workers=8):
    """
    Coleta os PRs de múltiplos repositórios em paralelo.
    Supõe que collector.collect_pull_requests_of_repo aceita owner, repo e retorna DataFrame.
    """
    pr_dfs = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for _, row in repos_df.iterrows():
            owner = row['owner']
            repo = row['name']
            futures.append(executor.submit(collector.collect_pull_requests_of_repo, owner, repo))
        for future in as_completed(futures):
            result = future.result()
            if result is not None and not result.empty:
                pr_dfs.append(result)
    if pr_dfs:
        return pd.concat(pr_dfs, ignore_index=True)
    return pd.DataFrame()

def main():
    """Função principal do laboratório."""
    parser = argparse.ArgumentParser(description='Lab03 - Code Review Analysis')
    parser.add_argument('--phase', choices=['collect', 'analyze', 'visualize', 'all'], 
                       default='all', help='Fase do laboratório a executar')
    parser.add_argument('--repos-limit', type=int, default=200, 
                       help='Número de repositórios populares a analisar')
    parser.add_argument('--min-prs', type=int, default=100,
                       help='Número mínimo de PRs por repositório')
    parser.add_argument('--log-level', default='INFO',
                       help='Nível de log (DEBUG, INFO, WARNING, ERROR)')
    
    args = parser.parse_args()
    logger = setup_logging(args.log_level)
    
    logger.info("=== Iniciando Lab03 - Análise de Code Review no GitHub ===")
    logger.info(f"Fase: {args.phase}")
    logger.info(f"Repositórios: {args.repos_limit}")
    logger.info(f"PRs mínimos: {args.min_prs}")
    
    token = os.environ.get('GIT_TOKEN')
    if not token:
        logger.error("Variável de ambiente GIT_TOKEN não está definida!")
        sys.exit(1)
    
    try:
        if args.phase in ['collect', 'all']:
            logger.info("--- Fase 1: Coleta de Dados ---")
            collector = GitHubCollector(token)
            
            repos_df = collector.collect_popular_repositories(
                limit=args.repos_limit,
                min_prs=args.min_prs
            )
            data_dir = os.path.join(os.path.dirname(__file__), '../Data')
            os.makedirs(data_dir, exist_ok=True)
            repos_csv = os.path.join(data_dir, 'repositories.csv')
            repos_df.to_csv(repos_csv, index=False)
            logger.info(f"Coletados {len(repos_df)} repositórios")

            # Coletando PRs em paralelo (ajuste o método conforme sua implementação)
            prs_df = parallel_collect_pull_requests(collector, repos_df)
            prs_csv = os.path.join(data_dir, 'pull_requests_raw.csv')
            prs_df.to_csv(prs_csv, index=False)
            logger.info(f"Coletados {len(prs_df)} pull requests")

            # Se existir MetricsCalculator, pode ser serializado normalmente
            calculator = MetricsCalculator()
            metrics_df = calculator.calculate_all_metrics(prs_df)
            metrics_csv = os.path.join(data_dir, 'pull_requests_metrics.csv')
            metrics_df.to_csv(metrics_csv, index=False)
            logger.info(f"Métricas calculadas para {len(metrics_df)} PRs")
        
        if args.phase in ['analyze', 'all']:
            logger.info("--- Fase 2: Análise Estatística ---")
            
            if args.phase == 'analyze':
                data_dir = os.path.join(os.path.dirname(__file__), '../Data')
                metrics_df = pd.read_csv(os.path.join(data_dir, 'pull_requests_metrics.csv'))
            
            analyzer = StatisticalAnalyzer()
            results = analyzer.analyze_research_questions(metrics_df)
            results_dir = os.path.join(os.path.dirname(__file__), '../Results')
            analyzer.save_results(results, results_dir)
            logger.info("Análise estatística concluída")
        
        if args.phase in ['visualize', 'all']:
            logger.info("--- Fase 3: Visualização ---")
            
            if args.phase == 'visualize':
                data_dir = os.path.join(os.path.dirname(__file__), '../Data')
                results_dir = os.path.join(os.path.dirname(__file__), '../Results')
                metrics_df = pd.read_csv(os.path.join(data_dir, 'pull_requests_metrics.csv'))
                results = StatisticalAnalyzer.load_results(results_dir)
            
            visualizer = DataVisualizer()
            visualizer.create_all_visualizations(metrics_df, results, results_dir)
            logger.info("Visualizações criadas")
        
        logger.info("=== Lab03 Concluído com Sucesso ===")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {str(e)}")
        raise

if __name__ == "__main__":
    main()