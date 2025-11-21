# core/base_controller.py

"""
BaseController - Controller Genérico para o Projeto de Análise de Código

Este módulo implementa um controller base genérico que elimina código duplicado
e fornece funcionalidades padronizadas para todos os módulos da aplicação.

Funcionalidades:
- Gerenciamento centralizado de autenticação e autorização
- Configurações padronizadas com validação
- Ciclo de vida unificado de operações
- Atualização segura de componentes UI
- Sistema de callbacks padronizados
- Logging e debug integrados
- Cleanup automático de recursos

Author: Claude Code Assistant
Version: 2.0 (Simplificado)
Since: 2025-11-18
"""

import logging
from typing import Any, Dict, Optional, Callable, Union
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class BaseController:
    """
    Controller base genérico que implementa padrões comuns a todos os módulos.

    Esta classe foi criada durante a refatoração de simplificação do projeto para
    eliminar código duplicado e fornecer uma base consistente para todos os controllers.
    Implementa o padrão Template Method para operações comuns.

    Principais benefícios:
    - Eliminação de código duplicado entre módulos
    - Padrões consistentes de autenticação e configuração
    - Gerenciamento unificado do ciclo de vida das operações
    - Atualização segura e centralizada da UI
    - Debug e logging integrados
    - Cleanup automático de recursos

    Exemplo de uso:
        class MyController(BaseController):
            def __init__(self, model, notifier, auth_controller=None):
                super().__init__(model, notifier, auth_controller)
                self.specific_service = SpecificService()

            def start_specific_operation(self):
                if not self.start_operation("operação específica"):
                    return False

                try:
                    result = self.model.specific_operation()
                    self.finish_operation(True, result)
                    return True
                except Exception as e:
                    self.finish_operation(False, None, str(e))
                    return False

    Attributes:
        model (Any): Modelo de dados do módulo específico
        notifier (NotificationService): Serviço de notificação centralizado
        auth_controller (Optional[Any]): Controller de autenticação
        view (Optional[Any]): Referência para a view do módulo
        page (Optional[Any]): Página Flet para atualizações de UI
        is_active (bool): Status da operação atual
        current_operation (Optional[str]): Nome da operação em andamento
        operation_result (Optional[Any]): Resultado da última operação
        progress_bar (Optional[Any]): Barra de progresso da UI
        progress_text (Optional[Any]): Texto de progresso da UI
        status_text (Optional[Any]): Texto de status da UI
        info_text (Optional[Any]): Texto informativo da UI
    """

    def __init__(self, model: Any, notifier: NotificationService, auth_controller: Optional[Any] = None):
        """
        Inicializa o controller base com padrões consistentes.

        Este método configura os atributos básicos necessários para todos os controllers
        e inicializa o estado para gerenciamento do ciclo de vida das operações.

        Args:
            model (Any): Modelo de dados específico do módulo. Deve implementar métodos
                        como get_config() e update_config() quando aplicável.
            notifier (NotificationService): Serviço centralizado de notificações para
                                          feedback ao usuário.
            auth_controller (Optional[Any]): Controller de autenticação para validação
                                           de permissões. Se None, assume que não há
                                           controle de acesso.

        Note:
            Todos os controllers específicos devem chamar super().__init__() primeiro
            e depois configurar seus serviços específicos.

        Example:
            class AnaliseController(BaseController):
                def __init__(self, model, notifier, auth_controller=None):
                    super().__init__(model, notifier, auth_controller)
                    self.timing_service = UnifiedTimingService()  # Serviço específico
        """
        self.model = model
        self.notifier = notifier
        self.auth_controller = auth_controller
        self.view = None
        self.page = None

        # Estado comum
        self.is_active = False
        self.current_operation = None
        self.operation_result = None

        # Componentes UI comuns
        self.progress_bar = None
        self.progress_text = None
        self.status_text = None
        self.info_text = None

        logger.debug(f"{self.__class__.__name__} inicializado")

    # === Métodos de Autenticação ===
    def require_auth(self, required_role: str = "user") -> bool:
        """
        Verifica se o usuário tem permissão para acessar o módulo

        Args:
            required_role: Papel necessário (user, admin)

        Returns:
            bool: True se autenticado e autorizado
        """
        if not self.auth_controller:
            logger.warning("Controller de autenticação não configurado")
            return True  # Permitir se não tiver auth configurado

        if not self.auth_controller.is_authenticated:
            self.notifier.error("Autenticação necessária")
            return False

        user_role = self.auth_controller.get_current_user().get('role', 'user')
        if required_role == "admin" and user_role != "admin":
            self.notifier.error("Permissão de administrador necessária")
            return False

        return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna informações do usuário atual"""
        if self.auth_controller:
            return self.auth_controller.get_current_user()
        return None

    # === Métodos de Configuração ===
    def get_config(self) -> Dict[str, Any]:
        """
        Retorna configuração do modelo

        Returns:
            Dict com configuração atual ou vazio em caso de erro
        """
        try:
            if hasattr(self.model, 'get_config'):
                return self.model.get_config()
            elif hasattr(self.model, 'config'):
                return getattr(self.model, 'config', {})
            else:
                logger.warning(f"Model {type(self.model).__name__} não tem método get_config")
                return {}
        except Exception as e:
            logger.error(f"Erro ao obter configuração: {e}")
            self.notifier.error(f"Erro ao obter configuração: {str(e)}")
            return {}

    def update_config(self, config: Dict[str, Any]) -> bool:
        """
        Atualiza configuração no modelo

        Args:
            config: Nova configuração

        Returns:
            bool: True se sucesso
        """
        try:
            if hasattr(self.model, 'update_config'):
                self.model.update_config(config)
            elif hasattr(self.model, 'config'):
                self.model.config.update(config)
            else:
                logger.warning(f"Model {type(self.model).__name__} não suporta atualização de config")
                return False

            logger.info(f"Configuração atualizada em {self.__class__.__name__}")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
            self.notifier.error(f"Erro ao atualizar configuração: {str(e)}")
            return False

    def get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        try:
            if hasattr(self.model, '_get_default_config'):
                return self.model._get_default_config()
            return {}
        except Exception as e:
            logger.error(f"Erro ao obter config padrão: {e}")
            return {}

    # === Métodos de View e UI ===
    def set_view(self, view: Any):
        """Define a referência para a view"""
        self.view = view
        logger.debug(f"View definida em {self.__class__.__name__}")

    def set_page(self, page: Any):
        """Define a referência para a página Flet"""
        self.page = page

    def set_ui_components(self, progress_bar=None, progress_text=None,
                         status_text=None, info_text=None):
        """
        Define componentes de UI para atualização automática

        Args:
            progress_bar: Barra de progresso
            progress_text: Texto de progresso
            status_text: Texto de status
            info_text: Texto informativo
        """
        self.progress_bar = progress_bar
        self.progress_text = progress_text
        self.status_text = status_text
        self.info_text = info_text
        logger.debug("Componentes UI definidos no controller")

    def update_progress(self, value: float, text: str = None):
        """
        Atualiza barra de progresso com tratamento robusto de erros.

        Implementa múltiplas estratégias de atualização para garantir compatibilidade
        com diferentes contextos de execução (síncrono/assíncrono) e prevenir que
        falhas na UI interrompam operações críticas.

        Estratégia de Atualização (em ordem):
        1. Tenta update_async() para contextos assíncronos
        2. Fallback para update() síncrono
        3. Tratamento de erro não-crítico

        Args:
            value (float): Valor do progresso (0.0 a 1.0)
            text (str): Texto opcional para descrição do progresso

        Note:
            Este método é resiliente a falhas e nunca interromperá a operação
            principal. Falhas na UI são registradas apenas como debug para não
            poluir o log em operações normais.

            Exceções na atualização da página são tratadas especialmente porque
            podem ocorrer em contextos de thread diferentes ou quando a página
            Flet está em estado de transição.
        """
        try:
            if self.progress_bar:
                self.progress_bar.value = value
            if self.progress_text and text:
                self.progress_text.value = text
            # Correção: Usar método mais seguro para atualizar a página
            # Evita erro de chamada síncrona em contexto assíncrono
            if self.page and hasattr(self.page, 'update_async'):
                # Tenta usar método assíncrono se disponível
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop and not loop.is_closed():
                        asyncio.create_task(self.page.update_async())
                except:
                    # Fallback para método síncrono se assíncrono falhar
                    try:
                        self.page.update()
                    except Exception as update_error:
                        # Log detalhado mas não interrompe operação
                        logger.debug(f"Falha ao atualizar UI (ignorado): {update_error}")
            elif self.page:
                # Fallback final - tenta update direto com tratamento de erro
                try:
                    self.page.update()
                except Exception as update_error:
                    # Erro de UI não deve interromper operações críticas
                    logger.debug(f"Falha na atualização da UI (ignorado): {update_error}")
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso: {e}")

    def update_status(self, status: str, color: str = None):
        """
        Atualiza texto de status

        Args:
            status: Novo status
            color: Cor opcional (hexadecimal)
        """
        try:
            if self.status_text:
                self.status_text.value = f"Status: {status}"
                if color:
                    self.status_text.color = color
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")

    def update_info(self, info: str):
        """
        Atualiza texto informativo

        Args:
            info: Nova informação
        """
        try:
            if self.info_text:
                self.info_text.value = info
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Erro ao atualizar info: {e}")

    # === Métodos de Ciclo de Vida ===
    def start_operation(self, operation_name: str) -> bool:
        """
        Inicia uma operação, verificando autenticação e estado

        Args:
            operation_name: Nome da operação para logging

        Returns:
            bool: True se pode iniciar
        """
        if not self.require_auth():
            return False

        if self.is_active:
            self.notifier.warning(f"Já existe uma operação em andamento em {self.__class__.__name__}")
            return False

        self.is_active = True
        self.current_operation = operation_name
        self.operation_result = None

        logger.info(f"Iniciando operação: {operation_name}")
        self.update_status("Executando", "#1976D2")  # Azul

        return True

    def finish_operation(self, success: bool, result: Any = None, error: str = None):
        """
        Finaliza operação atual

        Args:
            success: True se sucesso
            result: Resultado da operação
            error: Mensagem de erro se falhou
        """
        self.is_active = False
        self.operation_result = result

        if success:
            # 🔥 MELHORIA: Logging mais detalhado com informações do resultado
            operation_info = self.current_operation
            if hasattr(self, 'timing_service') and hasattr(self.timing_service, 'get_current_elapsed_time'):
                try:
                    elapsed_time = self.timing_service.get_current_elapsed_time()
                    if elapsed_time > 0:
                        minutes = int(elapsed_time // 60)
                        seconds = elapsed_time % 60
                        operation_info += f" ({minutes}m {seconds:.0f}s)"
                except:
                    pass

            logger.info(f"Operação concluída com sucesso: {operation_info}")

            # 🔥 MELHORIA: Adiciona informações do resultado se disponível
            if result:
                if isinstance(result, list) and len(result) > 0:
                    # Se é uma lista de resultados (ex: análise)
                    total_items = len(result)
                    success_items = sum(1 for r in result if getattr(r, 'get', lambda x: None)('status') == 'sucesso')
                    logger.info(f"Resultado: {success_items}/{total_items} itens processados com sucesso")
                    self.update_info(f"Concluído: {success_items}/{total_items} itens")
                elif isinstance(result, dict):
                    # Se é um dicionário com informações
                    if 'total_files_processed' in result:
                        files = result['total_files_processed']
                        logger.info(f"Resultado: {files} arquivos processados")
                        self.update_info(f"Concluído: {files} arquivos")
                    else:
                        self.update_info(str(result))
                else:
                    self.update_info(str(result))
            else:
                self.update_info("Operação concluída com sucesso")

            self.update_status("Concluído", "#388E3C")  # Verde
        else:
            logger.error(f"Operação falhou: {self.current_operation} - {error}")
            self.update_status("Erro", "#D32F2F")  # Vermelho
            self.update_info(f"Erro: {error}" if error else "Operação falhou")

        self.current_operation = None

    def is_operation_active(self) -> bool:
        """Verifica se há operação em andamento"""
        return self.is_active

    # === Métodos de Callback Padrão ===
    def create_progress_callback(self, description: str = "Processando") -> Callable:
        """
        Cria callback padrão para progresso

        Args:
            description: Descrição do progresso

        Returns:
            Callable para callback de progresso
        """
        def callback(progress: float, item: str = "", **kwargs):
            try:
                percent = progress * 100
                text = f"{description}: {item} ({percent:.1f}%)" if item else f"{description} ({percent:.1f}%)"
                self.update_progress(progress, text)
            except Exception as e:
                logger.error(f"Erro no callback de progresso: {e}")

        return callback

    def create_completion_callback(self, success_message: str = None, error_message: str = None) -> Callable:
        """
        Cria callback padrão para conclusão

        Args:
            success_message: Mensagem de sucesso personalizada
            error_message: Mensagem de erro personalizada

        Returns:
            Callable para callback de conclusão
        """
        def callback(result: Any = None, error: str = None, **kwargs):
            success = error is None
            self.finish_operation(success, result, error)

            if success:
                if success_message:
                    self.notifier.success(success_message)
                else:
                    self.notifier.success("Operação concluída com sucesso")
            else:
                if error_message:
                    self.notifier.error(f"{error_message}: {error}")
                else:
                    self.notifier.error(f"Operação falhou: {error}")

        return callback

    # === Métodos de Limpeza ===
    def cleanup(self):
        """
        Limpa recursos e para operações em andamento
        """
        try:
            if self.is_active:
                self.finish_operation(False, None, "Controller sendo limpo")

            logger.info(f"Cleanup concluído para {self.__class__.__name__}")

        except Exception as e:
            logger.error(f"Erro no cleanup de {self.__class__.__name__}: {e}")

    def shutdown(self):
        """
        Shutdown completo do controller
        """
        self.cleanup()
        logger.info(f"Shutdown concluído para {self.__class__.__name__}")

    def __del__(self):
        """Cleanup automático ao destruir objeto"""
        try:
            self.shutdown()
        except Exception as e:
            logger.error(f"Erro no __del__ de {self.__class__.__name__}: {e}")