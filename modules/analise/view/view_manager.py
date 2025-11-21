import flet as ft
import logging
from typing import Optional
from .components import (
    ConfigCard, ExecutionCard, FilesCard,
    PromptCard, LogViews
)

"""
ViewManager do Módulo de Análise

Este módulo implementa o gerenciador de interface do usuário para o módulo
de análise de código, utilizando componentes genéricos reutilizáveis.
Segue a arquitetura MVC padrão do projeto.

Funcionalidades:
- Gerencia todos os componentes visuais da análise
- Coordena comunicação entre controller e UI components
- Implementa atualização reativa da interface
- Gerencia estado da view e notificações
- Fornece callbacks para eventos do usuário
"""

logger = logging.getLogger(__name__)

class ViewManager:
    """
    Gerenciador da View do Módulo de Análise.

    Esta classe coordena todos os componentes visuais do módulo de análise,
    implementando comunicação entre o controller e a interface do usuário.
    Utiliza componentes genéricos reutilizáveis da camada core.

    Attributes:
        controller: Controller da análise contendo lógica de negócio
        notifier: Serviço de notificação para eventos da aplicação
        page: Página Flet para renderização dos componentes
        config_card: Componente de configuração de análise
        execution_card: Componente de controle de execução
        files_card: Componente de seleção de arquivos
        prompt_card: Componente de edição de prompts
        log_views: Componente de visualização de logs
        view_instance: Container Flet principal da view

    Example:
        >>> controller = AnaliseController(model, notifier)
        >>> view_manager = ViewManager(controller, notifier, page)
        >>> page.add(view_manager())
    """

    def __init__(self, controller, notifier, page: ft.Page):
        """
        Inicializa o ViewManager da análise.

        Args:
            controller: Controller do módulo de análise
            notifier: Serviço de notificação
            page: Página Flet para renderização
        """
        self.controller = controller
        self.notifier = notifier
        self.page = page

        # Inicializa componentes
        self.config_card: Optional[ConfigCard] = None
        self.execution_card: Optional[ExecutionCard] = None
        self.files_card: Optional[FilesCard] = None
        self.prompt_card: Optional[PromptCard] = None
        self.log_views: Optional[LogViews] = None

        # Constrói a view
        self.view_instance = self._build_view()

        # Inscreve para notificações
        self._subscribe_to_notifications()

        logger.info("ViewManager instanciado, UI construída e inscrita nas notificações.")

    def _build_view(self) -> ft.Container:
        """Constrói a interface do usuário completa"""
        try:
            # Inicializa os componentes
            self.config_card = ConfigCard(self.controller, self.notifier)
            self.execution_card = ExecutionCard(self.controller, self.notifier)
            self.files_card = FilesCard(self.controller, self.notifier)
            self.prompt_card = PromptCard(self.controller, self.notifier)
            self.log_views = LogViews(self.controller, self.notifier)
            
            # Configura a página nos componentes que precisam
            self._set_page_on_components()
            
            # Cria o layout principal
            main_layout = ft.Column(
                controls=[
                    # Card de Configuração
                    self.config_card.build(),
                    
                    # Card de Execução
                    self.execution_card.build(),
                    
                    # Linha com Files e Prompt
                    ft.Row(
                        controls=[
                            # Card de Arquivos (2/3 da largura)
                            ft.Container(
                                content=self.files_card.build(),
                                expand=2
                            ),
                            # Card de Prompt (1/3 da largura)
                            ft.Container(
                                content=self.prompt_card.build(),
                                expand=1
                            )
                        ],
                        expand=True,
                        spacing=10
                    ),
                    
                    # Card de Logs e Visualizações
                    self.log_views.build()
                ],
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=15
            )
            
            # Container principal
            container = ft.Container(
                content=main_layout,
                padding=20,
                expand=True
            )
            
            logger.info("Interface do usuário construída com sucesso")
            return container
            
        except Exception as e:
            logger.error(f"Erro ao construir a view: {e}")
            return self._build_error_view(str(e))

    def _set_page_on_components(self):
        """Configura a página nos componentes que precisam de referência para atualizações"""
        try:
            # ✅ CORREÇÃO: Lista de componentes para configurar
            components_to_set = [
                (self.execution_card, 'set_page'),
                (self.files_card, 'set_page'), 
                (self.prompt_card, 'set_page'),
                (self.log_views, 'set_page')
            ]
            
            for component, method_name in components_to_set:
                if component and hasattr(component, method_name):
                    getattr(component, method_name)(self.page)
                    logger.debug(f"Página configurada em {component.__class__.__name__}.{method_name}")
                
            # ✅ CORREÇÃO: Conectar o controller à view de forma mais robusta
            if hasattr(self.controller, 'set_view'):
                self.controller.set_view(self)
                logger.debug("View definida no controller")
                
            logger.info("Página configurada em todos os componentes")
            
        except Exception as e:
            logger.error(f"Erro ao configurar página nos componentes: {e}")

    def _build_error_view(self, error_message: str) -> ft.Container:
        """Constrói uma view de erro em caso de falha na construção principal"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED),
                                    title=ft.Text(
                                        "Erro ao Carregar a Interface",
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.RED
                                    ),
                                    subtitle=ft.Text(
                                        "Ocorreu um erro ao construir a interface do usuário",
                                        color=ft.Colors.GREY_600
                                    )
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text(
                                            "Detalhes do erro:",
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        ft.Text(
                                            error_message,
                                            color=ft.Colors.GREY_700,
                                            selectable=True
                                        ),
                                        ft.Container(height=20),
                                        ft.ElevatedButton(
                                            "Tentar Recarregar",
                                            icon=ft.Icons.REFRESH,
                                            on_click=self._recarregar_interface
                                        )
                                    ]),
                                    padding=20
                                )
                            ]),
                            padding=0
                        ),
                        elevation=3,
                        margin=ft.margin.all(10)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=20,
            expand=True
        )

    def _recarregar_interface(self, e):
        """Tenta recarregar a interface em caso de erro"""
        try:
            logger.info("Tentando recarregar a interface...")
            
            # ✅ CORREÇÃO: Limpar notificações antigas
            self._unsubscribe_from_notifications()
            
            # Reconstrói a view
            self.view_instance = self._build_view()
            
            # ✅ CORREÇÃO: Re-inscrever nas notificações
            self._subscribe_to_notifications()
            
            # Atualiza a página
            if self.page and hasattr(self.page, 'controls') and self.page.controls:
                # Tenta encontrar e substituir o conteúdo da aba de análise
                self._replace_tab_content()
                        
            self.page.update()
            self.notifier.success("Interface recarregada com sucesso")
            
        except Exception as ex:
            logger.error(f"Erro ao recarregar interface: {ex}")
            self.notifier.error(f"Erro ao recarregar: {str(ex)}")

    def _replace_tab_content(self):
        """✅ CORREÇÃO: Substitui o conteúdo da aba atual de forma segura"""
        try:
            # Procura por tabs na página
            for control in self.page.controls:
                if hasattr(control, 'tabs') and control.tabs:
                    # Assume que a primeira aba é a de análise
                    if len(control.tabs) > 0:
                        control.tabs[0].content = ft.Container(
                            content=self.view_instance,
                            padding=10
                        )
                        logger.info("Conteúdo da aba de análise atualizado")
                        break
        except Exception as e:
            logger.error(f"Erro ao substituir conteúdo da aba: {e}")

    def _subscribe_to_notifications(self):
        """Inscreve-se para eventos de notificação"""
        try:
            if self.notifier:
                # Eventos de análise
                self.notifier.subscribe("analise_iniciada", self._on_analise_iniciada)
                self.notifier.subscribe("analise_pausada", self._on_analise_pausada)
                self.notifier.subscribe("analise_retomada", self._on_analise_retomada)
                self.notifier.subscribe("analise_parada", self._on_analise_parada)
                self.notifier.subscribe("analise_completada", self._on_analise_completada)
                self.notifier.subscribe("analise_erro", self._on_analise_erro)
                
                # Eventos de arquivos
                self.notifier.subscribe("arquivos_selecionados", self._on_arquivos_selecionados)
                self.notifier.subscribe("arquivos_processados", self._on_arquivos_processados)
                
                # Eventos de configuração
                self.notifier.subscribe("configuracao_atualizada", self._on_configuracao_atualizada)
                
                # ✅ CORREÇÃO: Eventos de log
                self.notifier.subscribe("log_info", self._on_log_info)
                self.notifier.subscribe("log_error", self._on_log_error)
                self.notifier.subscribe("log_success", self._on_log_success)
                
                logger.debug("ViewManager inscrito em todos os eventos de notificação")
                
        except Exception as e:
            logger.error(f"Erro ao inscrever-se nas notificações: {e}")

    def _unsubscribe_from_notifications(self):
        """✅ CORREÇÃO: Cancela a inscrição de eventos de notificação de forma mais completa"""
        try:
            if self.notifier:
                # Lista de eventos para cancelar inscrição
                events = [
                    "analise_iniciada", "analise_pausada", "analise_retomada", 
                    "analise_parada", "analise_completada", "analise_erro",
                    "arquivos_selecionados", "arquivos_processados", 
                    "configuracao_atualizada", "log_info", "log_error", "log_success"
                ]
                
                # Tenta remover este objeto como subscriber de todos os eventos
                for event in events:
                    if hasattr(self.notifier, 'unsubscribe'):
                        self.notifier.unsubscribe(event, self)
                
                logger.debug("ViewManager cancelou inscrição em todos os eventos")
        except Exception as e:
            logger.error(f"Erro ao cancelar inscrição nas notificações: {e}")

    # Handlers de eventos de notificação
    def _on_analise_iniciada(self, task_id: str):
        """Handler para evento de análise iniciada"""
        logger.info(f"Análise iniciada: {task_id}")
        # ✅ CORREÇÃO: Atualizar UI se necessário
        if self.execution_card and hasattr(self.execution_card, '_atualizar_ui_analise_iniciada'):
            self.execution_card._atualizar_ui_analise_iniciada()

    def _on_analise_pausada(self):
        """Handler para evento de análise pausada"""
        logger.info("Análise pausada")
        # ✅ CORREÇÃO: Atualizar UI se necessário
        if self.execution_card and hasattr(self.execution_card, '_atualizar_ui_analise_pausada'):
            self.execution_card._atualizar_ui_analise_pausada()

    def _on_analise_retomada(self):
        """Handler para evento de análise retomada"""
        logger.info("Análise retomada")
        # ✅ CORREÇÃO: Atualizar UI se necessário
        if self.execution_card and hasattr(self.execution_card, '_atualizar_ui_analise_executando'):
            self.execution_card._atualizar_ui_analise_executando()

    def _on_analise_parada(self):
        """Handler para evento de análise parada"""
        logger.info("Análise parada")
        # ✅ CORREÇÃO: Atualizar UI se necessário
        if self.execution_card and hasattr(self.execution_card, '_atualizar_ui_analise_parada'):
            self.execution_card._atualizar_ui_analise_parada()

    def _on_analise_completada(self, resultados: list):
        """Handler para evento de análise completada"""
        logger.info(f"Análise completada: {len(resultados)} resultados")
        # ✅ CORREÇÃO: Atualizar componentes relevantes
        if self.files_card and hasattr(self.files_card, 'on_analise_completada'):
            self.files_card.on_analise_completada(resultados)
        
        if self.log_views and hasattr(self.log_views, 'atualizar_estatisticas'):
            self.log_views.atualizar_estatisticas(resultados)
        
        if self.execution_card and hasattr(self.execution_card, '_atualizar_ui_analise_concluida'):
            self.execution_card._atualizar_ui_analise_concluida()

    def _on_analise_erro(self, erro: str):
        """Handler para evento de erro na análise"""
        logger.error(f"Erro na análise: {erro}")
        # ✅ CORREÇÃO: Atualizar UI de erro
        if self.log_views and hasattr(self.log_views, 'adicionar_log'):
            self.log_views.adicionar_log(f"Erro na análise: {erro}", "ERROR")

    def _on_arquivos_selecionados(self, arquivos: list):
        """Handler para evento de arquivos selecionados"""
        logger.info(f"Arquivos selecionados: {len(arquivos)} arquivos")
        if self.files_card and hasattr(self.files_card, 'on_arquivos_selecionados'):
            self.files_card.on_arquivos_selecionados(arquivos)

    def _on_arquivos_processados(self, arquivos: list):
        """Handler para evento de arquivos processados"""
        logger.info(f"Arquivos processados: {len(arquivos)} arquivos")
        if self.files_card and hasattr(self.files_card, 'on_arquivos_processados'):
            self.files_card.on_arquivos_processados(arquivos)

    def _on_configuracao_atualizada(self, config: dict):
        """Handler para evento de configuração atualizada"""
        logger.info("Configuração atualizada")
        if self.config_card and hasattr(self.config_card, 'atualizar_ui'):
            self.config_card.atualizar_ui()

    def _on_log_info(self, mensagem: str):
        """✅ CORREÇÃO: Handler para eventos de log info"""
        if self.log_views and hasattr(self.log_views, 'adicionar_log'):
            self.log_views.adicionar_log(mensagem, "INFO")

    def _on_log_error(self, mensagem: str):
        """✅ CORREÇÃO: Handler para eventos de log error"""
        if self.log_views and hasattr(self.log_views, 'adicionar_log'):
            self.log_views.adicionar_log(mensagem, "ERROR")

    def _on_log_success(self, mensagem: str):
        """✅ CORREÇÃO: Handler para eventos de log success"""
        if self.log_views and hasattr(self.log_views, 'adicionar_log'):
            self.log_views.adicionar_log(mensagem, "SUCCESS")

    def get_view_instance(self):
        """Retorna a instância da view para uso nas abas"""
        # ✅ CORREÇÃO: Garantir que a view está construída
        if not hasattr(self, 'view_instance') or self.view_instance is None:
            logger.warning("View instance não encontrada, reconstruindo...")
            self.view_instance = self._build_view()
        return self.view_instance

    def update(self):
        """Atualiza a view completa"""
        try:
            logger.debug("Atualizando ViewManager...")
            
            # ✅ CORREÇÃO: Atualiza componentes individuais se necessário
            components_to_update = [
                (self.config_card, 'atualizar_ui'),
                (self.execution_card, 'update'),
                (self.files_card, 'update'),
                (self.prompt_card, 'update'),
                (self.log_views, 'update')
            ]
            
            for component, method_name in components_to_update:
                if component and hasattr(component, method_name):
                    try:
                        getattr(component, method_name)()
                    except Exception as comp_error:
                        logger.debug(f"Erro ao atualizar {component.__class__.__name__}: {comp_error}")
                
            # Atualiza a página
            if self.page:
                self.page.update()
                
            logger.debug("ViewManager atualizado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar ViewManager: {e}")

    def refresh(self):
        """Recarrega completamente a view"""
        try:
            logger.info("Recarregando ViewManager...")
            
            # ✅ CORREÇÃO: Limpar notificações antes de recarregar
            self._unsubscribe_from_notifications()
            
            # Reconstrói a view
            self.view_instance = self._build_view()
            
            # ✅ CORREÇÃO: Re-inscrever nas notificações
            self._subscribe_to_notifications()
            
            # Atualiza a página se possível
            if self.page:
                self.page.update()
                
            self.notifier.info("Interface recarregada")
            
        except Exception as e:
            logger.error(f"Erro ao recarregar ViewManager: {e}")
            self.notifier.error(f"Erro ao recarregar interface: {str(e)}")

    def get_component(self, component_name: str):
        """Retorna um componente específico pelo nome"""
        components = {
            'config_card': self.config_card,
            'execution_card': self.execution_card,
            'files_card': self.files_card,
            'prompt_card': self.prompt_card,
            'log_views': self.log_views
        }
        
        return components.get(component_name)

    def show_loading(self, message: str = "Carregando..."):
        """Exibe um indicador de carregamento"""
        try:
            if self.page:
                # ✅ CORREÇÃO: Implementação básica de loading
                loading_dialog = ft.AlertDialog(
                    title=ft.Text("Carregando"),
                    content=ft.Column([
                        ft.ProgressRing(),
                        ft.Text(message)
                    ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    open=True
                )
                self.page.dialog = loading_dialog
                self.page.update()
                
            self.notifier.info(message)
        except Exception as e:
            logger.error(f"Erro ao mostrar loading: {e}")

    def hide_loading(self):
        """Esconde o indicador de carregamento"""
        try:
            if self.page and self.page.dialog:
                self.page.dialog.open = False
                self.page.update()
        except Exception as e:
            logger.error(f"Erro ao esconder loading: {e}")

    def show_error(self, message: str, details: str = ""):
        """Exibe uma mensagem de erro"""
        try:
            logger.error(f"Erro na UI: {message} - {details}")
            self.notifier.error(message)
            
            # ✅ CORREÇÃO: Mostrar dialog de erro mais detalhado
            if self.page and details:
                def close_dialog(e):
                    if self.page.dialog:
                        self.page.dialog.open = False
                        self.page.update()
                
                error_dialog = ft.AlertDialog(
                    title=ft.Text("Erro Detalhado"),
                    content=ft.Column([
                        ft.Text(message, weight=ft.FontWeight.BOLD),
                        ft.Text(details, selectable=True),
                    ], tight=True),
                    actions=[ft.TextButton("Fechar", on_click=close_dialog)],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                
                self.page.dialog = error_dialog
                error_dialog.open = True
                self.page.update()
                
        except Exception as e:
            logger.error(f"Erro ao exibir erro na UI: {e}")

    def show_success(self, message: str):
        """✅ CORREÇÃO: Exibe uma mensagem de sucesso"""
        try:
            self.notifier.success(message)
        except Exception as e:
            logger.error(f"Erro ao exibir sucesso na UI: {e}")

    def add_log_entry(self, message: str, level: str = "INFO"):
        """✅ CORREÇÃO: Adiciona entrada de log de forma conveniente"""
        try:
            if self.log_views and hasattr(self.log_views, 'adicionar_log'):
                self.log_views.adicionar_log(message, level)
        except Exception as e:
            logger.error(f"Erro ao adicionar log entry: {e}")
    
    def _on_log_system(self, mensagem: str, nivel: str = "INFO"):
        """Handler para logs do sistema"""
        if self.log_views and hasattr(self.log_views, 'adicionar_log'):
            self.log_views.adicionar_log(mensagem, nivel)


    def __del__(self):
        """Cleanup ao destruir o ViewManager"""
        try:
            self._unsubscribe_from_notifications()
            logger.info("ViewManager destruído")
        except Exception as e:
            logger.error(f"Erro no cleanup do ViewManager: {e}")