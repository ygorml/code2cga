# modules/analise/controller.py

"""
AnaliseController - Controller Simplificado de Análise de Código

Este módulo implementa o controller de análise de código refatorado para usar
o BaseController genérico, eliminando código duplicado e fornecendo
padrões consistentes com outros módulos da aplicação.

Funcionalidades:
- Análise de código-fonte usando LLMs (Ollama) com checkpoint inteligente
- Sistema de pausa automática por limites de API com retentativa programada
- Timing preciso que exclui períodos de pausa das medições
- Gerenciamento de configurações de análise
- Controle de execução (iniciar, pausar, parar)
- Registro detalhado de timing e estatísticas
- Interface com UI components via BaseController
- Suporte a múltiplas linguagens de programação
- Verificação de status completo e limpeza de análises com erro

Sistemas Avançados:
- Checkpoint inteligente: Evita análises redundantes validando configuração
- Pausa automática: Detecta limites de API (429, 403) e pausa automaticamente
- Timing preciso: Mede tempo efetivo excluindo períodos de inatividade
- JSON robusto: Extração com múltiplas estratégias e fallbacks

Refactoring:
- Antes: 575 linhas com código duplicado
- Depois: 393 linhas usando BaseController (-32%)
- Benefícios: Manutenibilidade centralizada, padrões consistentes

Author: Claude Code Assistant
Version: 2.0 (Simplificado com sistemas avançados)
Since: 2025-11-18
Refactoring: Migrado de controller independente para BaseController
"""

import logging
import os
import time
from typing import List, Dict, Any, Callable, Optional, Union
from middleware.auth_middleware import login_required
import flet as ft
from services.unified_timing_service import UnifiedTimingService
from core.base_controller import BaseController

logger = logging.getLogger(__name__)

class AnaliseController(BaseController):
    """
    Controller simplificado de análise de código herdando de BaseController com sistemas avançados.

    Este controller foi refatorado durante a simplificação do projeto para eliminar
    código duplicado e usar padrões consistentes. Mantém 100% da funcionalidade
    original enquanto reduz significativamente a complexidade.

    Principais melhorias em relação à versão original:
    - Herança do BaseController elimina código duplicado
    - Gerenciamento unificado de estado e ciclo de vida
    - Padrões consistentes de UI update
    - Debug integrado e logging melhorado
    - Serviço de timing unificado em vez de múltiplos serviços
    - Sistema completo de checkpoint inteligente
    - Pausa automática por limites de API
    - Timing preciso excluindo períodos de pausa

    Attributes:
        timing_service (UnifiedTimingService): Serviço de timing preciso
        model (Any): Modelo de análise de código com sistemas avançados

    Exemplo de uso:
        # Criação do controller
        model = AnaliseModel(notifier)
        controller = AnaliseController(model, notifier, auth_controller)

        # Configuração de UI components
        controller.set_ui_components(
            progress_bar=progress_bar,
            progress_text=progress_text,
            status_text=status_text,
            page=page
        )

        # Iniciar análise
        config = controller.get_config()
        task_id = controller.iniciar_analise(
            arquivos=['file1.c', 'file2.c'],
            config=config
        )

    Attributes:
        timing_service (UnifiedTimingService): Serviço unificado de medição de tempo
        analise_ativa (bool): Status específico da análise de código

    Note:
        Este controller depende dos seguintes componentes:
        - AnaliseModel: Modelo para processamento real da análise
        - UnifiedTimingService: Para medição de tempo
        - NotificationService: Para feedback ao usuário
        - AuthController: Para controle de acesso (opcional)
    """

    def __init__(self, model, notifier, auth_controller=None):
        """
        Inicializa o controller de análise usando BaseController
        """
        super().__init__(model, notifier, auth_controller)

        # 🔍 ULTRATHINK: ID único para rastrear instâncias
        import uuid
        self.controller_id = str(uuid.uuid4())[:8]
        self.thread_id = str(id(self))  # ID do objeto

        # Serviços específicos do módulo
        self.timing_service = UnifiedTimingService()

        # 🔍 ULTRATHINK: Adicionar ID ao timing_service também
        self.timing_service.controller_id = self.controller_id
        self.timing_service.instance_id = str(id(self.timing_service))

        # Estado específico
        self.analise_ativa = False

        logger.info(f"🆔 [ULTRATHINK] AnaliseController CRIADO: ID={self.controller_id}, ThreadID={self.thread_id}")
        logger.debug(f"🔍 [ULTRATHINK] timing_service ID: {self.timing_service.instance_id}")
        logger.debug(f"🔍 [ULTRATHINK] Controller mem address: {hex(id(self))}")

    # === Sobrescritas do BaseController para garantir compatibilidade ===
    def set_ui_components(self, progress_bar=None, progress_text=None,
                         status_text=None, info_text=None, page=None):
        """
        Sobrescreve para garantir que a página seja configurada corretamente
        """
        # Chama o método do BaseController primeiro
        super().set_ui_components(progress_bar, progress_text, status_text, info_text)

        # Garante que a página seja configurada se fornecida
        if page:
            self.page = page
            logger.debug(f"Página configurada via set_ui_components no AnaliseController")

        logger.debug(f"Componentes UI configurados: progress_bar={progress_bar is not None}, "
                    f"progress_text={progress_text is not None}, status_text={status_text is not None}")

    # === Métodos Específicos do Módulo ===
    def get_modelos_disponiveis(self) -> List[str]:
        """Retorna lista de modelos disponíveis no Ollama"""
        try:
            resultado = self.model.testar_conexao_ollama()
            return resultado.get('modelos', [])
        except Exception as e:
            logger.error(f"Erro ao obter modelos: {e}")
            return []

    def iniciar_analise(self, arquivos: List[str], config: Dict[str, Any],
                       progress_callback: Callable = None,
                       completion_callback: Callable = None) -> str:
        """
        Inicia análise usando gerenciamento de operação do BaseController
        """
        # Usa gerenciamento de operação do BaseController
        if not self.start_operation("análise de código"):
            return None

        try:
            # Atualiza configuração usando método do BaseController
            self.update_config(config)

            # Extrai informações do projeto
            if arquivos:
                # Normaliza o caminho e remove barras duplicadas
                project_path = arquivos[0].replace('\\', '/').replace('//', '/')

                # Se o caminho começa com "inspecao/", extrai o nome do projeto
                if project_path.startswith('inspecao/'):
                    # Remove "inspecao/" do início e divide o restante
                    remaining_path = project_path[len('inspecao/'):]
                    if remaining_path:  # Se há algo após "inspecao/"
                        path_parts = remaining_path.split('/')
                        project_name = path_parts[0]  # Ex: nginx/src/core.c -> nginx
                    else:
                        project_name = "unknown"  # Caso seja apenas "inspecao/"
                else:
                    # Fallback: pega o nome do diretório pai do arquivo
                    project_name = os.path.basename(os.path.dirname(arquivos[0]))
            else:
                project_name = "dummy1"
            project_root = os.path.dirname(arquivos[0]) if arquivos else "/inspeção"
            language = config.get('language', 'C')

            # Inicia timing unificado
            logger.info(f"🆔 [ULTRATHINK] INICIAR ANÁLISE - Controller ID: {self.controller_id}")
            logger.info(f"🔍 [ULTRATHINK] Thread atual: {hex(id(self))}")
            logger.debug(f"🔍 [ULTRATHINK] timing_service ID: {self.timing_service.instance_id}")
            logger.debug(f"🔍 [ULTRATHINK] timing_service controller_id: {getattr(self.timing_service, 'controller_id', 'N/A')}")
            logger.debug(f"🔍 [ULTRATHINK] arquivos ({len(arquivos)}): {arquivos}")

            self.timing_service.start_analysis(
                project_name=project_name,
                file_count=len(arquivos),
                files=arquivos,
                config=config,
                project_root=project_root,
                language=language
            )

            logger.info(f"✅ [ULTRATHINK] Timing iniciado - Controller: {self.controller_id}, Projeto: {project_name}")

            # Configura callbacks padrão se não fornecidos
            logger.info(f"🆔 [ULTRATHINK] CONFIGURANDO CALLBACKS - Controller: {self.controller_id}")
            logger.debug(f"🔍 [ULTRATHINK] progress_callback fornecido: {progress_callback is not None}")
            logger.debug(f"🔍 [ULTRATHINK] completion_callback fornecido: {completion_callback is not None}")

            if progress_callback is None:
                progress_callback = self._on_progresso_analise
                logger.info(f"✅ [ULTRATHINK] USANDO progress_callback padrão: {self.controller_id}")
                logger.debug(f"🔍 [ULTRATHINK] progress_callback function: {progress_callback}")
                logger.debug(f"🔍 [ULTRATHINK] progress_callback ID: {id(progress_callback)}")

            if completion_callback is None:
                completion_callback = self._create_completion_callback()
                logger.info(f"✅ [ULTRATHINK] USANDO completion_callback padrão: {self.controller_id}")
                logger.debug(f"🔍 [ULTRATHINK] completion_callback function: {completion_callback}")
                logger.debug(f"🔍 [ULTRATHINK] completion_callback ID: {id(completion_callback)}")

            logger.info(f"🚀 [ULTRATHINK] INICIANDO ANÁLISE NO MODEL - Controller: {self.controller_id}")
            logger.debug(f"🔍 [ULTRATHINK] Model: {self.model}")
            logger.debug(f"🔍 [ULTRATHINK] Model ID: {id(self.model)}")

            # Inicia análise no model
            task_id = self.model.analisar_codigo(
                arquivos=arquivos,
                config=config,
                progress_callback=progress_callback,
                completion_callback=completion_callback
            )

            self.analise_ativa = True
            self.notifier.info(f"Análise iniciada (Tarefa: {task_id}) - Projeto: {project_name}")

            return task_id

        except Exception as e:
            self.timing_service.finish_analysis(success=False, error_message=str(e))
            self.finish_operation(False, None, str(e))
            self.notifier.error(f"Erro ao iniciar análise: {str(e)}")
            return None

    def pausar_analise(self) -> bool:
        """Pausa análise usando verificação do BaseController"""
        if not self.require_auth():
            return False

        try:
            success = self.model.pausar_analise()
            if success:
                self.timing_service.pause_analysis()
                logger.info("Análise pausada")
                self.notifier.info("Análise pausada")
                self.update_status("Pausado", "#F57C00")  # Laranja
            return success
        except Exception as e:
            logger.error(f"Erro ao pausar análise: {e}")
            self.notifier.error(f"Erro ao pausar análise: {str(e)}")
            return False

    def retomar_analise(self) -> bool:
        """Retoma análise"""
        if not self.require_auth():
            return False

        try:
            success = self.model.retomar_analise()
            if success:
                self.timing_service.resume_analysis()
                logger.info("Análise retomada")
                self.notifier.info("Análise retomada")
                self.update_status("Executando", "#1976D2")  # Azul
            return success
        except Exception as e:
            logger.error(f"Erro ao retomar análise: {e}")
            self.notifier.error(f"Erro ao retomar análise: {str(e)}")
            return False

    def parar_analise(self) -> bool:
        """Para análise usando método do BaseController"""
        try:
            success = self.model.parar_analise()
            if success:
                self.analise_ativa = False
                self.timing_service.finish_analysis(success=False, error_message="Análise cancelada pelo usuário")
                self.finish_operation(False, None, "Análise cancelada pelo usuário")
                self.notifier.info("Análise parada")
            return success
        except Exception as e:
            logger.error(f"Erro ao parar análise: {e}")
            self.notifier.error(f"Erro ao parar análise: {str(e)}")
            return False

    def get_status_analise(self) -> Dict[str, Any]:
        """Retorna status atual da análise"""
        try:
            return self.model.get_status_analise()
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return {
                'executando': False,
                'pausada': False,
                'parada': True,
                'completada': False,
                'progresso': 0,
                'arquivo_atual': '',
                'resultados_count': 0,
                'erro': str(e)
            }

    # 🔥 NOVOS: Métodos para gerenciamento de pausa automática por API
    def obter_status_pausa_api(self) -> Dict[str, Any]:
        """
        Retorna informações detalhadas sobre o status da pausa automática por API.

        Este método fornece dados completos sobre o sistema de pausa automática,
        incluindo motivo da pausa, tempo decorrido, próximas tentativas e
        contador de tentativas realizadas.

        Returns:
            Dict[str, Any]: Dicionário com informações da pausa:
                - ativa (bool): True se pausa está ativa
                - motivo (str): Motivo da pausa (ex: "rate_limit")
                - tempo_esperado (int): Tempo total esperado em segundos
                - proxima_tentativa_segundos (int): Segundos até próxima tentativa
                - tentativas (int): Número de tentativas realizadas
                - maximo_tentativas (int): Máximo de tentativas permitidas

        Note:
            Se o modelo não suportar pausa automática, retorna status inativo.

        Example:
            >>> status = controller.obter_status_pausa_api()
            >>> if status['ativa']:
            ...     print(f"Pausa ativa: {status['motivo']}")
            ...     print(f"Próxima tentativa em: {status['proxima_tentativa_segundos']}s")
        """
        try:
            if hasattr(self.model, 'obter_status_pausa_api'):
                return self.model.obter_status_pausa_api()
            else:
                return {
                    'ativa': False,
                    'motivo': None,
                    'tempo_esperado': 0,
                    'tentativas': 0
                }
        except Exception as e:
            logger.error(f"Erro ao obter status de pausa da API: {e}")
            return {
                'ativa': False,
                'motivo': None,
                'tempo_esperado': 0,
                'tentativas': 0,
                'erro': str(e)
            }

    def forcar_retentativa_api(self) -> Dict[str, Any]:
        """
        Força uma tentativa imediata de reconexão com a API, ignorando intervalo de pausa.

        Este método permite ao usuário tentar reconectar à API antes do tempo
        automático de 30 minutos. Útil para testes rápidos ou quando o usuário
        sabe que a API voltou a funcionar.

        Returns:
            Dict[str, Any]: Resultado da tentativa:
                - status (str): 'sucesso', 'erro', ou 'nao_suportado'
                - mensagem (str): Mensagem descritiva do resultado
                - api_disponivel (bool): True se API respondeu com sucesso

        Note:
            - Se a API responder, o sistema retoma a análise automaticamente
            - Se a API não estiver disponível, mantém estado de pausa
            - Notifica usuário sobre sucesso ou falha da tentativa

        Example:
            >>> resultado = controller.forcar_retentativa_api()
            >>> if resultado['status'] == 'sucesso':
            ...     print("API disponível! Análise retomada.")
            >>> else:
            ...     print(f"Falha: {resultado['mensagem']}")
        """
        try:
            if hasattr(self.model, 'forcar_retentativa_api'):
                resultado = self.model.forcar_retentativa_api()
                if resultado.get('status') == 'sucesso':
                    self.notifier.success(resultado.get('mensagem', 'Retomada bem-sucedida'))
                return resultado
            else:
                return {
                    'status': 'nao_suportado',
                    'mensagem': 'Funcionalidade não disponível no modelo atual'
                }
        except Exception as e:
            logger.error(f"Erro ao forçar retentativa da API: {e}")
            self.notifier.error(f"Erro ao forçar retentativa: {str(e)}")
            return {
                'status': 'erro',
                'mensagem': f'Erro: {str(e)}'
            }

    def cancelar_pausa_automatica(self) -> Dict[str, Any]:
        """
        Cancela a pausa automática e interrompe completamente a análise.

        Este método permite ao usuário cancelar tanto a pausa automática quanto
        a análise em andamento. Útil quando o usuário deseja interromper o processo
        e não quer esperar as retentativas automáticas.

        Returns:
            Dict[str, Any]: Resultado do cancelamento:
                - status (str): 'sucesso', 'erro', ou 'nao_suportado'
                - mensagem (str): Mensagem descritiva do resultado

        Note:
            - Interrompe o thread de retentativa automática
            - Para completamente a análise em andamento
            - Limpa estado de pausa automática
            - Notifica usuário sobre o cancelamento

        Example:
            >>> resultado = controller.cancelar_pausa_automatica()
            >>> print(resultado['mensagem'])
        """
        try:
            if hasattr(self.model, 'cancelar_pausa_automatica'):
                resultado = self.model.cancelar_pausa_automatica()
                if resultado.get('status') == 'sucesso':
                    self.notifier.info(resultado.get('mensagem', 'Pausa cancelada'))
                return resultado
            else:
                return {
                    'status': 'nao_suportado',
                    'mensagem': 'Funcionalidade não disponível no modelo atual'
                }
        except Exception as e:
            logger.error(f"Erro ao cancelar pausa automática: {e}")
            self.notifier.error(f"Erro ao cancelar pausa: {str(e)}")
            return {
                'status': 'erro',
                'mensagem': f'Erro: {str(e)}'
            }

    def verificar_status_completo(self, pasta_projeto: str = "inspecao/") -> Dict[str, Any]:
        """
        Verifica status completo do sistema incluindo checkpoint e pausa automática.

        Este método fornece uma visão completa do estado da análise, incluindo
        estatísticas de checkpoint, economia de requisições, status de pausa
        automática e informações detalhadas de progresso.

        Args:
            pasta_projeto (str): Caminho da pasta do projeto a ser analisada.
                                Default: "inspecao/"

        Returns:
            Dict[str, Any]: Status completo do sistema:
                - status (str): 'sucesso', 'parcial', ou 'erro'
                - mensagem (str): Mensagem descritiva do status
                - total_arquivos (int): Total de arquivos no projeto
                - resumo (Dict): Resumo de análise por status:
                    * sucesso (int): Arquivos analisados com sucesso
                    * pendente (int): Arquivos pendentes de análise
                    * falha (int): Arquivos com erro de análise
                    * incompativel (int): Arquivos com configuração incompatível
                - economia (Dict): Estatísticas de economia:
                    * arquivos_ignorados (int): Arquivos não reanalisados
                    * tempo_economizado_segundos (float): Tempo economizado
                    * requisicoes_economizadas (int): Requisições evitadas
                - pausa_automatica (Dict): Status da pausa automática
                - analise_atual (Dict): Informações da análise em andamento

        Note:
            - Calcula economia baseada em checkpoints válidos
            - Valida compatibilidade de configurações
            - Inclui status completo do sistema de pausa automática

        Example:
            >>> status = controller.verificar_status_completo("meu_projeto/")
            >>> print(f"Arquivos: {status['resumo']['sucesso']}/{status['total_arquivos']}")
            >>> print(f"Economia: {status['economia']['requisicoes_economizadas']} requisições")
        """
        try:
            if hasattr(self.model, 'verificar_status_completo'):
                return self.model.verificar_status_completo(pasta_projeto)
            else:
                # Fallback se método não existir
                return {
                    'status': 'parcial',
                    'mensagem': 'Funcionalidade completa não disponível',
                    'total_arquivos': 0,
                    'resumo': {'sucesso': 0, 'pendente': 0, 'falha': 0, 'incompativel': 0},
                    'pausa_automatica': self.obter_status_pausa_api()
                }
        except Exception as e:
            logger.error(f"Erro ao verificar status completo: {e}")
            return {
                'status': 'erro',
                'mensagem': f'Erro: {str(e)}',
                'total_arquivos': 0
            }

    def testar_conexao_ollama(self) -> Dict[str, Any]:
        """Testa conexão com Ollama"""
        try:
            logger.info("Testando conexão com Ollama...")
            resultado = self.model.testar_conexao_ollama()

            if resultado.get('conectado'):
                modelos = resultado.get('modelos', [])
                logger.info(f"✅ Conexão bem-sucedida! {len(modelos)} modelos disponíveis")
                self.notifier.success(f"Conexão estabelecida! {len(modelos)} modelos disponíveis")
            else:
                logger.error(f"❌ Falha na conexão: {resultado.get('erro', 'Erro desconhecido')}")
                self.notifier.error(f"Falha na conexão: {resultado.get('erro', 'Erro desconhecido')}")

            return resultado

        except Exception as e:
            logger.error(f"Erro ao testar conexão Ollama: {e}")
            self.notifier.error(f"Erro ao testar conexão: {str(e)}")
            return {
                'conectado': False,
                'modelos': [],
                'erro': str(e)
            }

    # === Callbacks Específicos ===
    def _on_progresso_analise(self, progresso: float, arquivo: str, resultado: any):
        """
        Callback de progresso com registro de métricas prioritário e isolado.

        Este método é o coração do sistema de coleta de métricas, registrando
        tempos de análise e estatísticas para cada arquivo processado. Implementa
        múltiplas camadas de tratamento de erros para garantir que as métricas
        sejam registradas mesmo em caso de falhas na interface.

        Arquitetura do Callback:
        1. Registro PRIMEIRO de métricas (prioridade máxima)
        2. UI update DEPOIS (opcional, não crítica)
        3. Fallback automático se registro primário falhar

        Args:
            progresso (float): Percentual de progresso (0.0 a 100.0)
            arquivo (str): Caminho completo do arquivo analisado
            resultado (any): Dicionário com resultado da análise contendo:
                - status (str): 'sucesso', 'erro', 'checkpoint_reaproveitado'
                - estatisticas (dict): {nodes_count, edges_count}
                - tempo_llm (float): Tempo em segundos da chamada LLM
                - checkpoint (bool): Se foi reaproveitado de cache

        Returns:
            bool: True se métricas foram registradas com sucesso

        Note:
            As métricas são registradas através do UnifiedTimingService e incluem:
            - Tempo de análise por arquivo
            - Tempo de chamada LLM
            - Contagem de nós e arestas do grafo
            - Identificação de checkpoints

            O método é resiliente a falhas na UI e garante persistência
            dos dados mesmo se `update_progress()` lançar exceções.
        """

        # 🔍 ULTRATHINK: Logar início do callback com IDs
        import threading
        thread_id = threading.current_thread().ident
        logger.info(f"🆔 [ULTRATHINK] CALLBACK INICIADO - Controller: {self.controller_id}")
        logger.info(f"🔍 [ULTRATHINK] Callback Thread ID: {thread_id}")
        logger.info(f"🔍 [ULTRATHINK] Controller Object: {hex(id(self))}")
        logger.info(f"🔍 [ULTRATHINK] Arquivo: {arquivo}, Progresso: {progresso}%")

        # 🔥 MÉTODO 1: Registro de métricas (prioridade máxima, completamente isolado)
        def _registrar_metricas():
            """Função interna dedicada exclusivamente ao registro de métricas"""
            try:
                # 🔍 DEBUG DETALHADO - Verificar estado atual
                logger.debug(f"🔍 [DEBUG] Callback iniciado para: {arquivo}")
                logger.debug(f"🔍 [DEBUG] Resultado bruto: {resultado}")
                logger.debug(f"🔍 [DEBUG] timing_service existe: {hasattr(self, 'timing_service')}")
                logger.debug(f"🔍 [DEBUG] timing_service é None: {self.timing_service is None if hasattr(self, 'timing_service') else 'N/A'}")

                if hasattr(self, 'timing_service') and self.timing_service:
                    logger.debug(f"🔍 [DEBUG] current_analysis existe: {self.timing_service.current_analysis is not None}")
                    if self.timing_service.current_analysis:
                        logger.debug(f"🔍 [DEBUG] projeto atual: {self.timing_service.current_analysis.get('metadata', {}).get('project_name', 'N/A')}")

                if not resultado or 'status' not in resultado:
                    logger.error(f"❌ [DEBUG] Sem resultado válido ou sem status para {arquivo}")
                    logger.error(f"❌ [DEBUG] resultado é None: {resultado is None}")
                    logger.error(f"❌ [DEBUG] chaves em resultado: {list(resultado.keys()) if resultado else 'None'}")
                    return False

                status = resultado.get('status')
                logger.debug(f"🔍 [DEBUG] Status extraído: {status}")

                if status != 'sucesso':
                    logger.warning(f"⚠️ [DEBUG] Status não é sucesso ({status}) para {arquivo}")
                    return False

                # Extrair dados necessários
                stats = resultado.get('estatisticas', {})
                logger.debug(f"🔍 [DEBUG] Estatísticas extraídas: {stats}")

                nodes = stats.get('nodes_count', 0)
                edges = stats.get('edges_count', 0)
                tempo_llm = resultado.get('tempo_llm', 0)
                tempo_ms = tempo_llm * 1000
                is_checkpoint = resultado.get('checkpoint', False)

                logger.info(f"📊 [INÍCIO] Registrando métricas para {arquivo}: {nodes}n/{edges}e, {tempo_ms}ms (checkpoint: {is_checkpoint})")

                # Verificar se timing_service está disponível
                if not hasattr(self, 'timing_service') or self.timing_service is None:
                    logger.error(f"❌ [CRÍTICO] timing_service não disponível para {arquivo}")
                    logger.error(f"❌ [CRÍTICO] hasattr: {hasattr(self, 'timing_service')}")
                    logger.error(f"❌ [CRÍTICO] is None: {self.timing_service is None if hasattr(self, 'timing_service') else 'N/A'}")
                    return False

                # Registrar timing do arquivo (sempre)
                try:
                    self.timing_service.add_file_timing(
                        file_path=arquivo,
                        analysis_time_ms=tempo_ms if not is_checkpoint else 0.0,
                        nodes_count=nodes,
                        edges_count=edges
                    )
                    logger.debug(f"✅ File timing registrado: {arquivo}")
                except Exception as file_timing_error:
                    logger.error(f"❌ Erro no add_file_timing: {file_timing_error}")
                    return False

                # 🔥 CORREÇÃO: Registrar timing LLM mesmo para checkpoints (array deve existir)
                if tempo_llm > 0:
                    try:
                        config = self.get_config()
                        model = config.get('llm_modelo', 'unknown')
                        self.timing_service.add_llm_timing(
                            operation=f"analyze_{os.path.basename(arquivo)}",
                            duration_ms=tempo_ms,
                            model=model
                        )
                        logger.debug(f"✅ LLM timing registrado: {arquivo} ({model})")
                    except Exception as llm_timing_error:
                        logger.error(f"❌ Erro no add_llm_timing: {llm_timing_error}")
                        # Não retorna False aqui porque o file timing já foi registrado
                else:
                    # 🔥 CORREÇÃO: Garantir que array llm_calls exista mesmo sem tempo LLM
                    try:
                        if hasattr(self, 'timing_service') and self.timing_service:
                            if "llm_calls" not in self.timing_service.current_analysis.get("timing", {}):
                                self.timing_service.current_analysis["timing"]["llm_calls"] = []
                            logger.debug(f"✅ Array llm_calls garantido para: {arquivo}")
                    except Exception as llm_array_error:
                        logger.warning(f"⚠️ Não foi possível garantir array llm_calls: {llm_array_error}")
                    try:
                        config = self.get_config()
                        model = config.get('llm_modelo', 'unknown')
                        self.timing_service.add_llm_timing(
                            operation=f"analyze_{os.path.basename(arquivo)}",
                            duration_ms=tempo_ms,
                            model=model
                        )
                        logger.debug(f"✅ LLM timing registrado: {arquivo} ({model})")
                    except Exception as llm_timing_error:
                        logger.error(f"❌ Erro no add_llm_timing: {llm_timing_error}")
                        # Não retorna False aqui porque o file timing já foi registrado

                if is_checkpoint:
                    logger.info(f"⚡ Checkpoint registrado: {arquivo} (tempo zero)")
                else:
                    logger.info(f"📊 Métricas registradas: {arquivo} ({tempo_ms}ms, {nodes}n/{edges}e)")

                return True

            except Exception as metric_error:
                logger.error(f"❌ Erro crítico no registro de métricas para {arquivo}: {metric_error}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                return False

        # 🔥 MÉTODO 2: Tentar registrar métricas (múltiplas tentativas)
        metricas_registradas = False

        # Primeira tentativa: registro direto
        try:
            metricas_registradas = _registrar_metricas()
            if metricas_registradas:
                logger.debug(f"🎯 Métricas registradas com sucesso na primeira tentativa: {arquivo}")
        except Exception as primeira_tentativa_error:
            logger.error(f"❌ Falha na primeira tentativa: {primeira_tentativa_error}")

        # Segunda tentativa: se primeira falhou, tentar registro simplificado
        if not metricas_registradas:
            try:
                logger.warning(f"⚠️ Tentando registro simplificado para {arquivo}")
                if resultado and resultado.get('status') == 'sucesso':
                    stats = resultado.get('estatisticas', {})
                    tempo_llm = resultado.get('tempo_llm', 0)
                    self.timing_service.add_file_timing(
                        file_path=arquivo,
                        analysis_time_ms=tempo_llm * 1000,
                        nodes_count=stats.get('nodes_count', 0),
                        edges_count=stats.get('edges_count', 0)
                    )
                    metricas_registradas = True
                    logger.info(f"🚑 Registro simplificado funcionou: {arquivo}")
            except Exception as registro_simplificado_error:
                logger.error(f"❌ Falha no registro simplificado: {registro_simplificado_error}")

        # 🔥 MÉTODO 3: UI Update (opcional, não afeta métricas)
        try:
            if metricas_registradas:
                # Só atualiza UI se métricas foram registradas com sucesso
                percent = progresso / 100
                text = f"✅ {os.path.basename(arquivo)} ({progresso:.1f}%) - {nodes if 'nodes' in locals() else 0} nodes"
                self.update_progress(percent, text)
                logger.debug(f"🎨 UI atualizada com sucesso: {arquivo}")
            else:
                # Mostra progresso mesmo sem métricas
                percent = progresso / 100
                text = f"⚠️ {os.path.basename(arquivo)} ({progresso:.1f}%) - sem métricas"
                self.update_progress(percent, text)
                logger.warning(f"⚠️ UI atualizada sem métricas: {arquivo}")
        except Exception as ui_error:
            # UI falhou, mas métricas já estão seguras
            if metricas_registradas:
                logger.info(f"✅ Métricas salvas, UI falhou (aceitável): {ui_error}")
            else:
                logger.error(f"❌ UI falhou E métricas não registradas: {ui_error}")

        # 🔥 RESUMO FINAL
        if metricas_registradas:
            logger.debug(f"🎉 Callback concluído com sucesso para {arquivo}")
        else:
            logger.error(f"💀 Callback falhou completamente para {arquivo} - NENHUMA MÉTRICA REGISTRADA!")

        return metricas_registradas

    def _create_completion_callback(self):
        """Cria callback de conclusão usando BaseController"""
        def callback(resultados: list, erro: str = None):
            # 🔍 ULTRATHINK: Logar início do completion callback
            import threading
            thread_id = threading.current_thread().ident
            logger.info(f"🆔 [ULTRATHINK] COMPLETION CALLBACK - Controller: {self.controller_id}")
            logger.info(f"🔍 [ULTRATHINK] Completion Thread ID: {thread_id}")
            logger.info(f"🔍 [ULTRATHINK] Controller Object: {hex(id(self))}")
            logger.debug(f"🔍 [ULTRATHINK] resultados recebidos: {len(resultados) if resultados else 0}")
            logger.debug(f"🔍 [ULTRATHINK] erro: {erro}")

            try:
                # 🔍 ULTRATHINK: Verificar estado antes de finalizar
                logger.debug(f"🔍 [ULTRATHINK] timing_service ID: {self.timing_service.instance_id}")
                logger.debug(f"🔍 [ULTRATHINK] current_analysis existe: {self.timing_service.current_analysis is not None}")
                if self.timing_service.current_analysis:
                    files_count = len(self.timing_service.current_analysis.get('timing', {}).get('files', []))
                    logger.debug(f"🔍 [ULTRATHINK] arquivos registrados antes de finish: {files_count}")

                if erro:
                    # Finaliza com erro usando BaseController
                    logger.warning(f"⚠️ [ULTRATHINK] Finalizando com erro - Controller: {self.controller_id}")
                    self.timing_service.finish_analysis(success=False, error_message=erro)
                    self.finish_operation(False, None, erro)
                else:
                    logger.info(f"🔍 [ULTRATHINK] Processando sucesso - Controller: {self.controller_id}")
                    sucessos = sum(1 for r in resultados if r.get('status') == 'sucesso')
                    total_nodes = sum(r.get('estatisticas', {}).get('nodes_count', 0) for r in resultados if r.get('status') == 'sucesso')
                    total_edges = sum(r.get('estatisticas', {}).get('edges_count', 0) for r in resultados if r.get('status') == 'sucesso')

                    logger.debug(f"🔍 [ULTRATHINK] sucessos: {sucessos}, nodes: {total_nodes}, edges: {total_edges}")

                    # 🔍 ULTRATHINK: Estado FINAL antes de finish_analysis
                    logger.info(f"⚡ [ULTRATHINK] ESTADO FINAL - Controller: {self.controller_id}")
                    logger.debug(f"🔍 [ULTRATHINK] arquivos em timing_service: {len(self.timing_service.current_analysis.get('timing', {}).get('files', []))}")
                    logger.debug(f"🔍 [ULTRATHINK] llm_calls em timing_service: {len(self.timing_service.current_analysis.get('timing', {}).get('llm_calls', []))}")

                    # Finaliza timing
                    logger.info(f"💾 [ULTRATHINK] CHAMANDO finish_analysis - Controller: {self.controller_id}")
                    self.timing_service.finish_analysis(success=True, results_count=sucessos)
                    logger.info(f"✅ [ULTRATHINK] finish_analysis concluído - Controller: {self.controller_id}")

                    # Adiciona informação de tempo na notificação
                    elapsed = self.timing_service.get_current_elapsed_time()
                    time_info = f" em {self._format_duration(elapsed) if elapsed else ''}"

                    # Finaliza operação com sucesso usando BaseController
                    self.finish_operation(True, f"{sucessos} arquivos, {total_nodes} nodes, {total_edges} edges", None)
                    self.notifier.success(f"Análise completada{time_info}! {sucessos} arquivos processados")

                    # Atualiza info específico
                    self.update_info(f"Análise concluída! {sucessos} arquivos processados, {total_nodes} nodes, {total_edges} edges.")

            except Exception as e:
                logger.error(f"Erro no callback de conclusão: {e}")
                self.finish_operation(False, None, str(e))

        return callback

    # === Métodos Utilitários ===
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em formato legível"""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}min"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}h"

    def is_analise_ativa(self) -> bool:
        """Verifica se análise está ativa usando BaseController"""
        return self.is_operation_active() or self.analise_ativa

    def obter_resultados_analise(self, task_id: str = None) -> List[Dict[str, Any]]:
        """Obtém resultados da análise"""
        try:
            status = self.get_status_analise()
            return status.get('resultado', [])
        except Exception as e:
            logger.error(f"Erro ao obter resultados: {e}")
            return []

    def get_estatisticas_analise(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas da análise"""
        try:
            resultados = self.obter_resultados_analise()

            if not resultados:
                return {
                    'total_arquivos': 0,
                    'sucessos': 0,
                    'erros': 0,
                    'vazios': 0,
                    'total_nodes': 0,
                    'total_edges': 0,
                    'taxa_sucesso': 0
                }

            total_arquivos = len(resultados)
            sucessos = sum(1 for r in resultados if r.get('status') == 'sucesso')
            erros = sum(1 for r in resultados if r.get('status') == 'erro')
            vazios = sum(1 for r in resultados if r.get('status') == 'vazio')

            total_nodes = sum(r.get('estatisticas', {}).get('nodes_count', 0)
                            for r in resultados if r.get('status') == 'sucesso')
            total_edges = sum(r.get('estatisticas', {}).get('edges_count', 0)
                            for r in resultados if r.get('status') == 'sucesso')

            return {
                'total_arquivos': total_arquivos,
                'sucessos': sucessos,
                'erros': erros,
                'vazios': vazios,
                'total_nodes': total_nodes,
                'total_edges': total_edges,
                'taxa_sucesso': (sucessos / total_arquivos * 100) if total_arquivos > 0 else 0
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_arquivos': 0,
                'sucessos': 0,
                'erros': 0,
                'vazios': 0,
                'total_nodes': 0,
                'total_edges': 0,
                'taxa_sucesso': 0,
                'erro': str(e)
            }

    def exportar_resultados(self, formato: str = 'json') -> str:
        """Exporta resultados da análise"""
        try:
            resultados = self.obter_resultados_analise()

            if formato == 'json':
                export_path = f"storage/export/analise_export_{int(time.time())}.json"
                os.makedirs(os.path.dirname(export_path), exist_ok=True)

                import json
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, indent=2, ensure_ascii=False)

                logger.info(f"Resultados exportados para: {export_path}")
                self.notifier.success(f"Resultados exportados para: {export_path}")
                return export_path
            else:
                raise ValueError(f"Formato não suportado: {formato}")

        except Exception as e:
            logger.error(f"Erro ao exportar resultados: {e}")
            self.notifier.error(f"Erro ao exportar resultados: {str(e)}")
            return ""

    def limpar_resultados(self):
        """Limpa resultados da análise atual"""
        try:
            if self.analise_ativa:
                self.parar_analise()

            if hasattr(self.model, 'resultados'):
                self.model.resultados = []

            logger.info("Resultados limpos")
            self.notifier.info("Resultados limpos")

        except Exception as e:
            logger.error(f"Erro ao limpar resultados: {e}")
            self.notifier.error(f"Erro ao limpar resultados: {str(e)}")

    # === Sobrescrita do Cleanup ===
    def cleanup(self):
        """Cleanup específico do AnaliseController"""
        try:
            if self.analise_ativa:
                self.parar_analise()

            # Chama cleanup do BaseController
            super().cleanup()

        except Exception as e:
            logger.error(f"Erro no cleanup do AnaliseController: {e}")