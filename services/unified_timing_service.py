# services/unified_timing_service.py

"""
UnifiedTimingService - Serviço Unificado de Medição de Tempo

Este módulo implementa um serviço unificado que substitui três serviços anteriores
de medição de tempo, eliminando duplicação e fornecendo uma interface consistente.

Serviços substituídos:
- AnalysisTimerService: Timer complexo com JSON logging e pausas
- TimingLoggerService: Formato específico de timing para exportação
- OllamaService timing: Tempo de resposta do LLM

Funcionalidades:
- Medição completa de tempo de análise (incluindo pausas)
- Registro de tempo por arquivo processado
- Tracking de chamadas ao LLM
- Exportação em múltiplos formatos
- Estatísticas consolidadas
- Compatibilidade com dados existentes

Author: Claude Code Assistant
Version: 2.0 (Unificado)
Since: 2025-11-18
Refactoring: Substitui 3 serviços duplicados por 1 serviço unificado
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class UnifiedTimingService:
    """
    Serviço unificado de timing que combina funcionalidades dos três serviços anteriores.

    Esta classe foi criada durante a refatoração de simplificação para eliminar a
    duplicação de serviços de timing. Mantém compatibilidade total com as interfaces
    anteriores enquanto adiciona novas funcionalidades.

    Principais benefícios:
    - Eliminação completa de duplicação de código
    - Interface unificada para todos os tipos de timing
    - Compatibilidade com dados existentes (formatos antigo e novo)
    - Tracking integrado de LLM calls
    - Estatísticas consolidadas em tempo real
    - Exportação em múltiplos formatos

    Exemplo de uso:
        # Iniciar análise
        timing_service = UnifiedTimingService()
        timing_service.start_analysis(
            project_name="meu_projeto",
            file_count=5,
            files=["file1.c", "file2.c"],
            language="C"
        )

        # Registrar timing de arquivo
        timing_service.add_file_timing("file1.c", 1500.0, nodes=10, edges=5)

        # Registrar chamada LLM
        timing_service.add_llm_timing("analyze_file1", 1200.0, "codellama")

        # Finalizar e obter estatísticas
        timing_service.finish_analysis(success=True, results_count=1)
        stats = timing_service.get_statistics()

    Attributes:
        storage_dir (str): Diretório base para armazenamento de dados
        current_analysis (Optional[Dict]): Análise atual em andamento
        start_time (Optional[float]): Timestamp de início da análise
        file_timings (List[Tuple]): Lista de tempos por arquivo
        llm_times (List[float]): Lista de tempos de chamadas LLM
        analysis_log_file (str): Caminho do arquivo de log unificado
    """

    def __init__(self, storage_dir: str = "storage"):
        # 🔍 ULTRATHINK: Rastrear instâncias
        import uuid
        self.service_id = str(uuid.uuid4())[:8]
        self.instance_id = str(id(self))
        self.controller_id = getattr(self, 'controller_id', 'N/A')

        self.storage_dir = storage_dir
        self.current_analysis = None
        self.start_time = None
        self.file_timings = []
        self.llm_times = []

        # 🔥 NOVO: Tracking de tempo efetivo (excluindo pausas)
        self.pause_start_time = None
        self.total_pause_time = 0
        self.last_resume_time = None
        self.effective_start_time = None

        # Garante que os diretórios existam
        os.makedirs(os.path.join(storage_dir, "data"), exist_ok=True)

        logger.info(f"🆔 [ULTRATHINK] UnifiedTimingService CRIADO: ID={self.service_id}")
        logger.debug(f"🔍 [ULTRATHINK] Instance ID: {self.instance_id}")
        logger.debug(f"🔍 [ULTRATHINK] Controller ID: {self.controller_id}")
        logger.debug(f"🔍 [ULTRATHINK] Memory address: {hex(id(self))}")
        os.makedirs(os.path.join(storage_dir, "export"), exist_ok=True)

        # Arquivos de log
        self.analysis_log_file = os.path.join(storage_dir, "analysis_times.json")
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Inicializa o arquivo de log se não existir"""
        if not os.path.exists(self.analysis_log_file):
            with open(self.analysis_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": "2.0",
                    "created_at": datetime.now().isoformat(),
                    "analyses": []
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Arquivo de log unificado criado: {self.analysis_log_file}")

    # === Interface AnalysisTimerService ===
    def start_analysis(self, project_name: str, file_count: int = 0, files: list = None,
                      config: Dict[str, Any] = None, project_root: str = None,
                      language: str = "C"):
        """
        Inicia medição de tempo para nova análise (compatível com ambas interfaces)

        Args:
            project_name: Nome do projeto
            file_count: Número de arquivos (interface AnalysisTimerService)
            files: Lista de arquivos (interface AnalysisTimerService)
            config: Configurações (interface AnalysisTimerService)
            project_root: Raiz do projeto (interface TimingLoggerService)
            language: Linguagem (interface TimingLoggerService)
        """
        # 🔍 ULTRATHINK: DEBUG DETALHADO COM IDs
        logger.info(f"🆔 [ULTRATHINK] start_analysis - Service ID: {self.service_id}")
        logger.info(f"🔍 [ULTRATHINK] Controller ID: {self.controller_id}")
        logger.info(f"🚀 [ULTRATHINK] INICIANDO ANÁLISE - Projeto: {project_name}")
        logger.debug(f"🔍 [ULTRATHINK] file_count: {file_count}")
        logger.debug(f"🔍 [ULTRATHINK] files: {files}")
        logger.debug(f"🔍 [ULTRATHINK] language: {language}")

        self.start_time = time.time()
        self.effective_start_time = self.start_time  # 🔥 Tempo efetivo
        self.file_timings = []
        self.llm_times = []

        # 🔥 Reset de tracking de pausas
        self.pause_start_time = None
        self.total_pause_time = 0
        self.last_resume_time = self.start_time

        # Compatibilidade com ambas interfaces
        files = files or []
        project_root = project_root or ""

        self.current_analysis = {
            "id": f"analysis_{int(time.time())}",
            "metadata": {
                "tool_name": "AgenteAnalistaCodigo",
                "tool_version": "2.0",
                "project_name": project_name,
                "project_root": project_root,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "language": language
            },
            "analysis_info": {
                "file_count": file_count or len(files),
                "files": files,
                "config": config or {},
                "start_time": datetime.now().isoformat(),
                "status": "running"
            },
            "timing": {
                "total_analysis_time_ms": 0,
                "llm_total_time_ms": 0,
                "files": [],
                "llm_calls": []
            },
            "summary": {
                "total_files_processed": 0,
                "total_nodes": 0,
                "total_edges": 0
            }
        }

        logger.info(f"Análise iniciada: {project_name} ({file_count or len(files)} arquivos)")

    def add_file_timing(self, file_path: str, analysis_time_ms: float,
                       nodes_count: int = 0, edges_count: int = 0):
        """
        Adiciona tempo de análise para um arquivo
        """
        # 🔍 ULTRATHINK: DEBUG DETALHADO COM IDs
        logger.info(f"🆔 [ULTRATHINK] add_file_timing - Service: {self.service_id}")
        logger.info(f"🔍 [ULTRATHINK] Controller: {self.controller_id}")
        logger.info(f"📊 [ULTRATHINK] Arquivo: {file_path}")
        logger.debug(f"🔍 [ULTRATHINK] current_analysis existe: {self.current_analysis is not None}")
        logger.debug(f"🔍 [ULTRATHINK] analysis_time_ms: {analysis_time_ms}")
        logger.debug(f"🔍 [ULTRATHINK] nodes_count: {nodes_count}, edges_count: {edges_count}")

        if not self.current_analysis:
            logger.error(f"❌ [CRÍTICO] Tentativa de adicionar timing sem análise iniciada")
            logger.error(f"❌ [CRÍTICO] current_analysis é None")
            return

        logger.debug(f"🔍 [DEBUG] projeto atual: {self.current_analysis.get('metadata', {}).get('project_name', 'N/A')}")
        logger.debug(f"🔍 [DEBUG] files antes: {len(self.current_analysis['timing']['files'])}")

        file_record = {
            "file": file_path,
            "analysis_time_ms": round(analysis_time_ms, 2),
            "timestamp": datetime.now().isoformat()
        }

        # Adiciona nodes e edges (sempre incluir, mesmo que zero)
        file_record["nodes"] = nodes_count
        file_record["edges"] = edges_count

        self.current_analysis["timing"]["files"].append(file_record)
        self.file_timings.append((file_path, analysis_time_ms))

        logger.info(f"✅ [SUCESSO] File timing adicionado: {file_path} -> {nodes_count}n/{edges_count}e, {analysis_time_ms:.2f}ms")
        logger.debug(f"🔍 [DEBUG] files depois: {len(self.current_analysis['timing']['files'])}")

    def add_llm_timing(self, operation: str, duration_ms: float, model: str = "unknown"):
        """
        Adiciona tempo de resposta do LLM (funcionalidade do OllamaService)
        """
        if not self.current_analysis:
            logger.warning("Tentativa de adicionar timing LLM sem análise iniciada")
            return

        llm_record = {
            "operation": operation,
            "model": model,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now().isoformat()
        }

        # Adiciona ao registro se não existir
        if "llm_calls" not in self.current_analysis["timing"]:
            self.current_analysis["timing"]["llm_calls"] = []

        self.current_analysis["timing"]["llm_calls"].append(llm_record)
        self.llm_times.append(duration_ms)

        # Atualiza total LLM time
        self.current_analysis["timing"]["llm_total_time_ms"] += duration_ms
        logger.debug(f"🤖 LLM timing adicionado: {operation} ({model}) -> {duration_ms:.2f}ms")

    def finish_analysis(self, success: bool = True, error_message: str = None,
                       results_count: int = 0):
        """
        Finaliza análise e salva em ambos formatos
        """
        if not self.current_analysis or not self.start_time:
            logger.warning("Tentativa de finalizar análise não iniciada")
            return

        # 🔥 MELHORIA: Calcula tempos totais (incluindo tempo efetivo sem pausas)
        total_time_seconds = time.time() - self.start_time
        total_time_ms = total_time_seconds * 1000

        # 🔥 Tempo efetivo (excluindo pausas)
        if self.pause_start_time:
            # Se está pausado, calcula até agora
            effective_time_seconds = (self.pause_start_time - self.effective_start_time) - self.total_pause_time
        else:
            # Se não está pausado, calcula até agora
            effective_time_seconds = (time.time() - self.effective_start_time) - self.total_pause_time

        effective_time_ms = effective_time_seconds * 1000

        # Tempo total dos arquivos (se disponível)
        files_time = sum(f["analysis_time_ms"] for f in self.current_analysis["timing"]["files"])

        # Atualiza informações finais
        self.current_analysis["analysis_info"].update({
            "end_time": datetime.now().isoformat(),
            "status": "completed" if success else "failed",
            "error_message": error_message,
            "results_count": results_count
        })

        # 🔥 Adiciona ambos tempos (total e efetivo)
        self.current_analysis["timing"].update({
            "total_analysis_time_ms": round(total_time_ms, 2),
            "effective_analysis_time_ms": round(effective_time_ms, 2),  # 🔥 NOVO
            "files_processing_time_ms": round(files_time, 2),
            "llm_total_time_ms": round(sum(self.llm_times), 2),
            "total_pause_time_ms": round(self.total_pause_time * 1000, 2)  # 🔥 NOVO
        })

        # Atualiza summary
        files_processed = len(self.current_analysis["timing"]["files"])
        total_nodes = sum(f.get("nodes", 0) for f in self.current_analysis["timing"]["files"])
        total_edges = sum(f.get("edges", 0) for f in self.current_analysis["timing"]["files"])

        # Debug detalhado
        logger.debug(f"📊 Processando summary: {files_processed} arquivos")
        logger.debug(f"📊 Total LLM times: {self.llm_times}")
        logger.debug(f"📊 Files array: {self.current_analysis['timing']['files']}")

        self.current_analysis["summary"].update({
            "total_files_processed": files_processed,
            "total_nodes": total_nodes,
            "total_edges": total_edges
        })

        logger.debug(f"📊 Summary atualizado: {self.current_analysis['summary']}")

        # Salva em ambos formatos para compatibilidade
        self._save_to_unified_log()
        self._save_to_export_format()

        logger.info(f"Análise finalizada: {files_processed} arquivos em {total_time_ms:.2f}ms")
        logger.info(f"⏱️ Tempo efetivo (sem pausas): {effective_time_ms:.2f}ms | Tempo total com pausas: {total_time_ms:.2f}ms")

        # Limpa estado
        self.current_analysis = None
        self.start_time = None
        self.file_timings = []
        self.llm_times = []

        # 🔥 Limpa tracking de pausas
        self.pause_start_time = None
        self.total_pause_time = 0
        self.last_resume_time = None
        self.effective_start_time = None

    # 🔥 NOVOS: Métodos para gerenciar pausas
    def pause_analysis(self):
        """Inicia tracking de tempo de pausa"""
        if not self.pause_start_time and self.effective_start_time:
            self.pause_start_time = time.time()
            logger.debug(f"Análise pausada em {self.pause_start_time}")

    def resume_analysis(self):
        """Finaliza tracking de tempo de pausa"""
        if self.pause_start_time:
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_time += pause_duration
            self.last_resume_time = time.time()
            self.pause_start_time = None
            logger.debug(f"Análise retomada após {pause_duration:.2f}s de pausa (total pausado: {self.total_pause_time:.2f}s)")

    def get_effective_elapsed_time(self) -> float:
        """Retorna tempo efetivo decorrido (excluindo pausas atuais)"""
        if not self.effective_start_time:
            return 0

        if self.pause_start_time:
            # Se está pausado, calcula até início da pausa
            effective_time = (self.pause_start_time - self.effective_start_time) - self.total_pause_time
        else:
            # Se não está pausado, calcula até agora
            effective_time = (time.time() - self.effective_start_time) - self.total_pause_time

        return max(0, effective_time)

    def _save_to_unified_log(self):
        """Salva no log unificado (formato AnalysisTimerService)"""
        try:
            with open(self.analysis_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            # Adiciona análise atual
            log_data["analyses"].append(self.current_analysis)

            # Mantém apenas últimas 100 para não sobrecarregar
            if len(log_data["analyses"]) > 100:
                log_data["analyses"] = log_data["analyses"][-100:]

            log_data["last_updated"] = datetime.now().isoformat()
            log_data["total_analyses"] = len(log_data["analyses"])

            with open(self.analysis_log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Erro ao salvar no log unificado: {e}")

    def _save_to_export_format(self):
        """Salva no formato export (compatível TimingLoggerService)"""
        try:
            project_name = self.current_analysis["metadata"]["project_name"]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Formato de exportação (TimingLoggerService compatibility)
            export_filename = f"timing_{project_name}_{timestamp}.json"
            export_filepath = os.path.join(self.storage_dir, "export", export_filename)

            with open(export_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_analysis, f, indent=2, ensure_ascii=False)

            # Também salva como latest
            latest_filepath = os.path.join(self.storage_dir, "export", f"timing_{project_name}.json")
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_analysis, f, indent=2, ensure_ascii=False)

            logger.info(f"Arquivo de exportação salvo: {export_filepath}")

        except Exception as e:
            logger.error(f"Erro ao salvar arquivo de exportação: {e}")

    # === Métodos de Compatibilidade ===
    def get_current_elapsed_time(self) -> Optional[float]:
        """Retorna tempo decorrido da análise atual (seconds)"""
        if self.start_time:
            return time.time() - self.start_time
        return None

    def get_current_timing_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos tempos atuais"""
        if not self.current_analysis:
            return {}

        files = self.current_analysis["timing"]["files"]
        if not files:
            return {"files_processed": 0, "total_time_ms": 0}

        total_time = sum(f["analysis_time_ms"] for f in files)
        avg_time = total_time / len(files)

        return {
            "files_processed": len(files),
            "total_time_ms": round(total_time, 2),
            "average_time_ms": round(avg_time, 2),
            "llm_total_time_ms": round(self.current_analysis["timing"]["llm_total_time_ms"], 2),
            "llm_calls_count": len(self.current_analysis["timing"].get("llm_calls", []))
        }

    def get_analysis_history(self, limit: int = 10) -> list:
        """Retorna histórico de análises"""
        try:
            with open(self.analysis_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            return log_data.get("analyses", [])[-limit:]
        except Exception as e:
            logger.error(f"Erro ao ler histórico: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais"""
        try:
            with open(self.analysis_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            analyses = log_data.get("analyses", [])
            if not analyses:
                return {"message": "Nenhuma análise registrada"}

            # Compatibilidade com formato antigo e novo
            completed = []
            failed = []

            for a in analyses:
                # Formato novo (unificado)
                if "analysis_info" in a:
                    if a["analysis_info"].get("status") == "completed":
                        completed.append(a)
                    elif a["analysis_info"].get("status") == "failed":
                        failed.append(a)
                # Formato antigo (AnalysisTimerService)
                else:
                    if a.get("status") == "completed":
                        completed.append(a)
                    elif a.get("status") == "failed":
                        failed.append(a)

            # Total files - compatibilidade com ambos formatos
            total_files = 0
            total_time = 0
            total_llm_time = 0
            total_llm_calls = 0

            for a in completed:
                # Formato novo
                if "summary" in a:
                    total_files += a["summary"].get("total_files_processed", 0)
                    total_time += a["timing"].get("total_analysis_time_ms", 0) / 1000
                    total_llm_time += a["timing"].get("llm_total_time_ms", 0) / 1000
                    total_llm_calls += len(a["timing"].get("llm_calls", []))
                # Formato antigo
                else:
                    total_files += a.get("file_count", 0)
                    total_time += a.get("effective_analysis_seconds", a.get("total_duration_seconds", 0))

            return {
                "total_analyses": len(analyses),
                "completed_analyses": len(completed),
                "failed_analyses": len(failed),
                "success_rate": len(completed) / len(analyses) * 100 if analyses else 0,
                "total_files_analyzed": total_files,
                "total_analysis_time_seconds": total_time,
                "total_llm_time_seconds": total_llm_time,
                "total_llm_calls": total_llm_calls,
                "average_files_per_analysis": total_files / len(completed) if completed else 0,
                "average_analysis_time_seconds": total_time / len(completed) if completed else 0,
                "average_llm_time_seconds": total_llm_time / total_llm_calls if total_llm_calls > 0 else 0
            }

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {"error": str(e)}

    def export_report(self, output_path: str = None) -> str:
        """Exporta relatório detalhado"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.storage_dir, "export", f"analysis_report_{timestamp}.json")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "service_version": "2.0",
                "statistics": self.get_statistics(),
                "recent_analyses": self.get_analysis_history(20)
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"Relatório exportado: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            raise

    # === Métados de Compatibilidade ===
    # Nota: Métodos pause_analysis e resume_analysis implementados acima (linha 338)
    # Esta seção mantida para referência futura de compatibilidade