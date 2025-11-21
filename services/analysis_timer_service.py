# services/analysis_timer_service.py

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AnalysisTimerService:
    """
    Serviço responsável por medir e registrar o tempo de análise de projetos.
    Mantém um histórico detalhado em formato JSON.
    """

    def __init__(self, log_file: str = "storage/analysis_times.json"):
        self.log_file = log_file
        self.current_analysis = None
        self.start_time = None
        self.pause_times = []
        self.pause_start = None

        # Garante que o diretório exista
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Inicializa o arquivo de log se não existir
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Inicializa o arquivo de log com uma estrutura vazia se não existir"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "analyses": []
                }, f, indent=4, ensure_ascii=False)
            logger.info(f"Arquivo de log de tempos criado: {self.log_file}")

    def start_analysis(self, project_name: str, file_count: int, files: list, config: Dict[str, Any] = None):
        """
        Inicia a medição de tempo para uma nova análise

        Args:
            project_name: Nome do projeto being analisado
            file_count: Número de arquivos a serem analisados
            files: Lista de caminhos dos arquivos
            config: Configurações usadas na análise
        """
        self.start_time = time.time()
        self.pause_times = []
        self.pause_start = None

        self.current_analysis = {
            "id": f"analysis_{int(time.time())}",
            "project_name": project_name,
            "file_count": file_count,
            "files": files,
            "config": config or {},
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "pauses": []
        }

        logger.info(f"Análise iniciada: {project_name} ({file_count} arquivos)")

    def pause_analysis(self):
        """Marca o início de uma pausa na análise"""
        if self.current_analysis and self.pause_start is None:
            self.pause_start = time.time()
            logger.info("Análise pausada")

    def resume_analysis(self):
        """Marca o fim de uma pausa na análise"""
        if self.current_analysis and self.pause_start is not None:
            pause_duration = time.time() - self.pause_start
            self.pause_times.append(pause_duration)

            # Registra a pausa na análise atual
            self.current_analysis["pauses"].append({
                "start": datetime.fromtimestamp(self.pause_start).isoformat(),
                "end": datetime.now().isoformat(),
                "duration_seconds": pause_duration
            })

            self.pause_start = None
            logger.info(f"Análise retomada após {pause_duration:.2f} segundos de pausa")

    def finish_analysis(self, success: bool = True, error_message: str = None, results_count: int = 0):
        """
        Finaliza a análise e salva no log

        Args:
            success: Indica se a análise foi concluída com sucesso
            error_message: Mensagem de erro se a análise falhou
            results_count: Número de resultados gerados
        """
        if not self.current_analysis or not self.start_time:
            logger.warning("Tentativa de finalizar análise não iniciada")
            return

        # Calcula tempos
        total_time = time.time() - self.start_time
        total_pause_time = sum(self.pause_times)
        effective_time = total_time - total_pause_time

        # Completa os dados da análise
        self.current_analysis.update({
            "end_time": datetime.now().isoformat(),
            "status": "completed" if success else "failed",
            "total_duration_seconds": total_time,
            "total_pause_duration_seconds": total_pause_time,
            "effective_analysis_seconds": effective_time,
            "results_count": results_count,
            "average_time_per_file": effective_time / self.current_analysis["file_count"] if self.current_analysis["file_count"] > 0 else 0,
            "error_message": error_message
        })

        # Formata tempos para melhor legibilidade
        self.current_analysis.update({
            "total_duration_formatted": self._format_duration(total_time),
            "effective_analysis_formatted": self._format_duration(effective_time),
            "average_time_per_file_formatted": self._format_duration(self.current_analysis["average_time_per_file"])
        })

        # Salva no log
        self._save_analysis_to_log()

        logger.info(f"Análise finalizada em {self._format_duration(total_time)} "
                   f"(efetivo: {self._format_duration(effective_time)})")

        # Limpa estado
        self.current_analysis = None
        self.start_time = None
        self.pause_times = []
        self.pause_start = None

    def _format_duration(self, seconds: float) -> str:
        """Formata a duração em um formato legível"""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}min"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}h"

    def _save_analysis_to_log(self):
        """Salva a análise atual no arquivo de log JSON"""
        try:
            # Lê o log existente
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            # Adiciona a nova análise
            log_data["analyses"].append(self.current_analysis)

            # Mantém apenas as últimas 100 análises para não sobrecarregar o arquivo
            if len(log_data["analyses"]) > 100:
                log_data["analyses"] = log_data["analyses"][-100:]

            # Atualiza estatísticas gerais
            log_data["last_updated"] = datetime.now().isoformat()
            log_data["total_analyses"] = len(log_data["analyses"])

            # Salva de volta no arquivo
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Erro ao salvar análise no log: {e}")

    def get_current_elapsed_time(self) -> Optional[float]:
        """Retorna o tempo decorrido da análise atual"""
        if self.start_time:
            return time.time() - self.start_time - sum(self.pause_times)
        return None

    def get_analysis_history(self, limit: int = 10) -> list:
        """
        Retorna o histórico de análises

        Args:
            limit: Número máximo de análises a retornar (mais recentes)

        Returns:
            Lista com as análises mais recentes
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            # Retorna as análises mais recentes (limitadas)
            return log_data.get("analyses", [])[-limit:]

        except Exception as e:
            logger.error(f"Erro ao ler histórico de análises: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas gerais das análises

        Returns:
            Dicionário com estatísticas
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            analyses = log_data.get("analyses", [])

            if not analyses:
                return {"message": "Nenhuma análise registrada"}

            # Calcula estatísticas
            completed = [a for a in analyses if a["status"] == "completed"]
            failed = [a for a in analyses if a["status"] == "failed"]

            total_files = sum(a["file_count"] for a in completed)
            total_time = sum(a["effective_analysis_seconds"] for a in completed)

            return {
                "total_analyses": len(analyses),
                "completed_analyses": len(completed),
                "failed_analyses": len(failed),
                "success_rate": len(completed) / len(analyses) * 100 if analyses else 0,
                "total_files_analyzed": total_files,
                "total_analysis_time": self._format_duration(total_time),
                "average_files_per_analysis": total_files / len(completed) if completed else 0,
                "average_analysis_time": self._format_duration(total_time / len(completed)) if completed else 0
            }

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {"error": str(e)}

    def export_report(self, output_path: str = None) -> str:
        """
        Exporta um relatório detalhado das análises

        Args:
            output_path: Caminho para salvar o relatório

        Returns:
            Caminho do arquivo gerado
        """
        if output_path is None:
            output_path = f"storage/export/analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            # Gera relatório completo
            report = {
                "generated_at": datetime.now().isoformat(),
                "statistics": self.get_statistics(),
                "recent_analyses": self.get_analysis_history(20),
                "all_time_best": self._get_best_analyses(),
                "all_time_worst": self._get_worst_analyses()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)

            logger.info(f"Relatório exportado para: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            raise

    def _get_best_analyses(self, limit: int = 5) -> list:
        """Retorna as análises mais rápidas (por arquivo)"""
        analyses = self.get_analysis_history(100)
        # Filtra apenas completas e ordena por tempo por arquivo
        completed = [a for a in analyses if a["status"] == "completed"]
        return sorted(completed, key=lambda x: x.get("average_time_per_file", float('inf')))[:limit]

    def _get_worst_analyses(self, limit: int = 5) -> list:
        """Retorna as análises mais lentas (por arquivo)"""
        analyses = self.get_analysis_history(100)
        # Filtra apenas completas e ordena por tempo por arquivo (decrescente)
        completed = [a for a in analyses if a["status"] == "completed"]
        return sorted(completed, key=lambda x: x.get("average_time_per_file", 0), reverse=True)[:limit]