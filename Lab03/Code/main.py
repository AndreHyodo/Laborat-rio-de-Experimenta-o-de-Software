#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_collector import GitHubCollector
from arquivosRestantesLab03.metrics_calculator import MetricsCalculator
from arquivosRestantesLab03.statistical_analyzer import StatisticalAnalyzer
from arquivosRestantesLab03.data_visualizer import DataVisualizer

def setup_logging(log_level='INFO'):
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('../Results/lab03.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Função principal do laboratório."""
    parser = argparse.ArgumentParser(description='Lab03 - Code Review Analysis')
    parser.add_argument('--phase', choices=['collect', 'analyze', 'visualize', 'all'], 
                       default='all', help='Fase do laboratório a executar')
    parser.add_argument('--repos-limit', type=int, default=200, 
                       help='Número de repositórios populares a analisar')
    parser.add_argument('--min-prs', type=int, default=100,
                       help='Número mínimo de PRs por repositório')
    parser.add_argument('--token', type=str, required=True,
                       help='Token de acesso do GitHub API')
    parser.add_argument('--log-level', default='INFO',
                       help='Nível de log (DEBUG, INFO, WARNING, ERROR)')
    
    args = parser.parse_args()
    logger = setup_logging(args.log_level)
    
    logger.info("=== Iniciando Lab03 - Análise de Code Review no GitHub ===")
    logger.info(f"Fase: {args.phase}")
    logger.info(f"Repositórios: {args.repos_limit}")
    logger.info(f"PRs mínimos: {args.min_prs}")
    
    try:
        if args.phase in ['collect', 'all']:
            logger.info("--- Fase 1: Coleta de Dados ---")
            collector = GitHubCollector(args.token)
            
            repos_df = collector.collect_popular_repositories(
                limit=args.repos_limit,
                min_prs=args.min_prs
            )
            repos_df.to_csv('../Data/repositories.csv', index=False)
            logger.info(f"Coletados {len(repos_df)} repositórios")
            
            prs_df = collector.collect_pull_requests(repos_df)
            prs_df.to_csv('../Data/pull_requests_raw.csv', index=False)
            logger.info(f"Coletados {len(prs_df)} pull requests")
            
            calculator = MetricsCalculator()
            metrics_df = calculator.calculate_all_metrics(prs_df)
            metrics_df.to_csv('../Data/pull_requests_metrics.csv', index=False)
            logger.info(f"Métricas calculadas para {len(metrics_df)} PRs")
        
        if args.phase in ['analyze', 'all']:
            logger.info("--- Fase 2: Análise Estatística ---")
            
            if args.phase == 'analyze':
                metrics_df = pd.read_csv('../Data/pull_requests_metrics.csv')
            
            analyzer = StatisticalAnalyzer()
            results = analyzer.analyze_research_questions(metrics_df)
            
            analyzer.save_results(results, '../Results/')
            logger.info("Análise estatística concluída")
        
        if args.phase in ['visualize', 'all']:
            logger.info("--- Fase 3: Visualização ---")
            
            if args.phase == 'visualize':
                metrics_df = pd.read_csv('../Data/pull_requests_metrics.csv')
                results = StatisticalAnalyzer.load_results('../Results/')
            
            visualizer = DataVisualizer()
            visualizer.create_all_visualizations(metrics_df, results, '../Results/')
            logger.info("Visualizações criadas")
        
        logger.info("=== Lab03 Concluído com Sucesso ===")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {str(e)}")
        raise

if __name__ == "__main__":
    main()