# services/timing_logger_service.py

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TimingLoggerService:
    """
    Serviço responsável por registrar tempos de análise em formato JSON.
    Gera arquivos de timing no diretório storage/export/.
    """

    def __init__(self, export_dir: str = "storage/export"):
        self.export_dir = export_dir
        self.current_analysis = None
        self.start_time = None
        self.file_timings = []

        # Garante que o diretório exista
        os.makedirs(export_dir, exist_ok=True)

    def start_analysis(self, project_name: str, project_root: str, language: str = "C"):
        """
        Inicia uma nova análise de timing

        Args:
            project_name: Nome do projeto
            project_root: Caminho raiz do projeto
            language: Linguagem de programação
        """
        self.start_time = time.time()
        self.file_timings = []

        self.current_analysis = {
            "metadata": {
                "tool_name": "CallGraphAnalyzer",
                "tool_version": "1.0.0",
                "project_name": project_name,
                "project_root": project_root,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "language": language
            },
            "timing": {
                "total_analysis_time_ms": 0,
                "files": []
            },
            "summary": {
                "total_files_processed": 0,
                "total_nodes": 0,
                "total_edges": 0
            }
        }

        logger.info(f"Iniciando log de timing para o projeto: {project_name}")

    def add_file_timing(self, file_path: str, analysis_time_ms: float,
                       nodes_count: int = 0, edges_count: int = 0):
        """
        Adiciona o tempo de análise de um arquivo

        Args:
            file_path: Caminho do arquivo analisado
            analysis_time_ms: Tempo de análise em milissegundos
            nodes_count: Número de nodes extraídos
            edges_count: Número de edges extraídos
        """
        if not self.current_analysis:
            logger.warning("Tentativa de adicionar timing sem análise iniciada")
            return

        file_record = {
            "file": file_path,
            "analysis_time_ms": round(analysis_time_ms, 2)
        }

        # Adiciona nodes e edges se disponíveis
        if nodes_count > 0 or edges_count > 0:
            file_record["nodes"] = nodes_count
            file_record["edges"] = edges_count

        self.current_analysis["timing"]["files"].append(file_record)
        self.file_timings.append((file_path, analysis_time_ms))

        logger.debug(f"Timing adicionado: {file_path} - {analysis_time_ms:.2f}ms")

    def finish_analysis(self):
        """
        Finaliza a análise e salva o arquivo JSON
        """
        if not self.current_analysis or not self.start_time:
            logger.warning("Tentativa de finalizar análise não iniciada")
            return

        # Calcula tempo total
        total_time = (time.time() - self.start_time) * 1000  # Converte para ms
        self.current_analysis["timing"]["total_analysis_time_ms"] = round(total_time, 2)

        # Atualiza summary
        files_processed = len(self.current_analysis["timing"]["files"])
        total_nodes = sum(f.get("nodes", 0) for f in self.current_analysis["timing"]["files"])
        total_edges = sum(f.get("edges", 0) for f in self.current_analysis["timing"]["files"])

        self.current_analysis["summary"]["total_files_processed"] = files_processed
        self.current_analysis["summary"]["total_nodes"] = total_nodes
        self.current_analysis["summary"]["total_edges"] = total_edges

        # Salva o arquivo
        self._save_timing_file()

        logger.info(f"Análise finalizada: {files_processed} arquivos em {total_time:.2f}ms")

    def _save_timing_file(self):
        """Salva o arquivo JSON com os tempos de análise"""
        try:
            # Nome do arquivo: timing_<projeto>_<timestamp>.json
            project_name = self.current_analysis["metadata"]["project_name"]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"timing_{project_name}_{timestamp}.json"

            filepath = os.path.join(self.export_dir, filename)

            # Salva o JSON com formatação
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_analysis, f, indent=2, ensure_ascii=False)

            logger.info(f"Arquivo de timing salvo: {filepath}")

            # Também salva como timing_<projeto>.json (última análise)
            latest_filename = f"timing_{project_name}.json"
            latest_filepath = os.path.join(self.export_dir, latest_filename)

            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_analysis, f, indent=2, ensure_ascii=False)

            logger.info(f"Arquivo de timing atualizado: {latest_filepath}")

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo de timing: {e}", exc_info=True)

    def get_current_timing_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo dos tempos da análise atual

        Returns:
            Dicionário com resumo dos tempos
        """
        if not self.current_analysis:
            return {}

        files = self.current_analysis["timing"]["files"]
        if not files:
            return {"files_processed": 0, "total_time_ms": 0}

        total_time = sum(f["analysis_time_ms"] for f in files)
        avg_time = total_time / len(files)
        max_time = max(f["analysis_time_ms"] for f in files)
        min_time = min(f["analysis_time_ms"] for f in files)

        return {
            "files_processed": len(files),
            "total_time_ms": round(total_time, 2),
            "average_time_ms": round(avg_time, 2),
            "max_time_ms": round(max_time, 2),
            "min_time_ms": round(min_time, 2),
            "slowest_file": max(files, key=lambda x: x["analysis_time_ms"])["file"],
            "fastest_file": min(files, key=lambda x: x["analysis_time_ms"])["file"]
        }