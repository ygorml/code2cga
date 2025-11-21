# main.py

"""
Aplicação Principal - Analisador de Código-Fonte com LLMs

Este módulo contém o ponto de entrada da aplicação desktop para análise
de código-fonte usando Large Language Models (LLMs) através do Ollama.
Implementa uma interface gráfica completa com Flet seguindo arquitetura MVC.

Arquitetura:
- Interface gráfica construída com Flet
- Módulos organizados em padrão MVC
- Sistema de autenticação integrado
- Serviços centralizados (notificação, banco de dados, timing)
- Componentes genéricos reutilizáveis

Módulos implementados:
- Análise: Processamento de código-fonte com LLMs
- Síntese: Geração de resumos e insights
- Grafo: Visualização interativa de grafos de chamada
- Dashboard: Analytics e métricas com RAG
- Autenticação: Sistema de login e controle de acesso

Sistemas Avançados:
- Checkpoint inteligente para evitar análises redundantes
- Pausa automática por limites de API com retentativa
- Timing preciso excluindo períodos de inatividade
- Sistema completo de logging e debugging

Author: Claude Code Assistant
Version: 2.0 (Simplificado com Sistemas Avançados)
Since: 2025-11-18
"""

import flet as ft
import logging
import os
import shutil
import atexit
import sys

# Adiciona o diretório raiz ao path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService
from modules.analise.view.view_manager import ViewManager as AnaliseViewManager
from modules.analise.model import AnaliseModel
from modules.analise.controller import AnaliseController
from modules.sintese.model import SinteseModel
from modules.sintese.controller import SinteseController
from modules.sintese.view.view_manager import ViewManager as SinteseViewManager
from modules.grafo.model import GrafoModel
from modules.grafo.controller import GrafoController
from modules.grafo.view.view_manager import ViewManager as GrafoViewManager
from modules.dashboard.view.view_manager import ViewManager as DashboardViewManager
from modules.dashboard.model import DashboardModel
from modules.dashboard.controller import DashboardController

from modules.auth.controller import AuthController
from middleware.auth_middleware import login_required

# Configuração do diretório de downloads
DOWNLOADS_DIR = "assets/downloads"
if os.path.exists(DOWNLOADS_DIR):
    for filename in os.listdir(DOWNLOADS_DIR):
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
else:
    os.makedirs(DOWNLOADS_DIR)

# Configuração do Logging
os.makedirs('log', exist_ok=True)

# Configura handlers com UTF-8 para suportar emojis
file_handler = logging.FileHandler('log/app.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Stream handler com tratamento para Windows
if os.name == 'nt':  # Windows
    stream_handler = logging.StreamHandler()
    # Mantém caracteres acentuados, remove apenas emojis
    class WindowsFormatter(logging.Formatter):
        def format(self, record):
            # Remove apenas emojis Unicode, mantém acentuados
            message = super().format(record)
            import re
            # Remove emojis mas mantém caracteres acentuados (U+00FF-U+017F)
            # Range de emojis: U+1F600-U+1F64F (emoticons), U+1F300-U+1F5FF (símbolos), etc.
            emoji_pattern = re.compile(
                '[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
                '\U00002702-\U000027B0\U000024C2-\U0001F251]+'
            )
            message = emoji_pattern.sub('', message)
            return message
    stream_handler.setFormatter(WindowsFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
else:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)

# Configure logging para capturar logs de todos os módulos
logging.getLogger('modules.analise').setLevel(logging.INFO)
logging.getLogger('services').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

class MainApp:
    def __init__(self):
        self.page = None
        self.notifier = None
        self.auth_controller = None
        self.analise_controller = None
        self.sintese_controller = None
        self.grafo_controller = None
        self.dashboard_controller = None
        
    def main(self, page: ft.Page):
        """
        Executa main.

        Args:
            page (ft.Page): Página principal da aplicação Flet
        """
        # Configuração da página
        page.title = "Agente Analista de Código - Dashboard Avançado"
        page.window_width = 1400
        page.window_height = 1400
        page.window_min_width = 1200
        page.window_min_height = 800
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        
        logger.info("Aplicação iniciada.")

        # 1. Instanciar serviços compartilhados
        self.page = page
        self.notifier = NotificationService()
        self.notifier.set_page(page)

        # 2. Instanciar controlador de autenticação
        self.auth_controller = AuthController(self.notifier)
        
        # 3. Verificar se usuário já está autenticado
        if self.auth_controller.verify_session():
            self._show_main_interface()
        else:
            self._show_login_interface()

    def _show_login_interface(self):
        """Mostra interface de login"""
        login_component = self.auth_controller.get_login_component(
            on_login_success=self._on_login_success
        )
        login_component.set_page(self.page)
        
        self.page.clean()
        self.page.add(login_component.build())
        self.page.update()

    def _on_login_success(self, session_data):
        """Callback chamado após login bem-sucedido"""
        self.auth_controller.current_user = session_data["user"]
        self.auth_controller.session_id = session_data["session_id"]
        self.auth_controller.is_authenticated = True
        
        # Inicializar módulos principais após autenticação
        self._initialize_modules()
        self._show_main_interface()

    def _initialize_modules(self):
        """Inicializa os módulos principais após autenticação"""
        try:
            # Análise (agora com suporte a threads)
            logger.info("Inicializando módulo de Análise...")
            analise_model = AnaliseModel(self.notifier)
            self.analise_controller = AnaliseController(analise_model, self.notifier)
            self.analise_controller.auth_controller = self.auth_controller
            
            # Síntese
            logger.info("Inicializando módulo de Síntese...")
            sintese_model = SinteseModel(self.notifier)
            self.sintese_controller = SinteseController(sintese_model, self.notifier)
            self.sintese_controller.auth_controller = self.auth_controller
            
            # Grafos
            logger.info("Inicializando módulo de Grafos...")
            grafo_model = GrafoModel(self.notifier)
            self.grafo_controller = GrafoController(grafo_model, self.notifier)
            self.grafo_controller.auth_controller = self.auth_controller
            
            # Dashboard Analytics com RAG
            logger.info("Inicializando módulo de Dashboard Analytics...")
            dashboard_model = DashboardModel(self.notifier)
            self.dashboard_controller = DashboardController(dashboard_model, self.notifier, self.grafo_controller, self.analise_controller)
            self.dashboard_controller.auth_controller = self.auth_controller
            
        except Exception as e:
            logger.error(f"Erro ao inicializar módulos: {e}")
            self.notifier.error(f"Erro na inicialização: {str(e)}")
            return

    def _show_main_interface(self):
        """Mostra interface principal"""
        try:
            # Obter as views
            logger.info("Carregando views dos módulos...")
            analise_view_manager = AnaliseViewManager(self.analise_controller, self.notifier, self.page)
            sintese_view_manager = SinteseViewManager(self.sintese_controller, self.notifier, self.page)
            grafo_view_manager = GrafoViewManager(self.grafo_controller, self.notifier, self.page)
            dashboard_view_manager = DashboardViewManager(self.dashboard_controller, self.notifier, self.page)
            
            analise_view = analise_view_manager.get_view_instance()
            sintese_view = sintese_view_manager
            grafo_view = grafo_view_manager()
            dashboard_view = dashboard_view_manager()

            # Conectar módulos para integração
            try:
                grafo_view_manager.set_dashboard_controller(self.dashboard_controller)
                logger.info("Módulos conectados para integração")
            except Exception as e:
                logger.warning(f"Erro na conexão entre módulos: {e}")

            # Configurar a estrutura de abas
            logger.info("Configurando interface de abas...")
            
            # Define as abas da aplicação
            tabs = ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        text="Análise de Código",
                        icon=ft.Icons.CODE,
                        content=ft.Container(
                            content=analise_view,
                            padding=10
                        )
                    ),
                    ft.Tab(
                        text="Síntese de Grafos", 
                        icon=ft.Icons.DATA_OBJECT,
                        content=ft.Container(
                            content=sintese_view,
                            padding=10
                        )
                    ),
                    ft.Tab(
                        text="Visualização de Grafos",
                        icon=ft.Icons.ACCOUNT_TREE,
                        content=ft.Container(
                            content=grafo_view,
                            padding=10
                        )
                    ),
                    ft.Tab(
                        text="Dashboard Analytics",
                        icon=ft.Icons.DASHBOARD, 
                        content=ft.Container(
                            content=dashboard_view,
                            padding=10
                        )
                    ),
                ],
                expand=1,
            )

            # Configurar eventos globais
            def on_tab_change(e):
                """Evento quando muda de aba"""
                try:
                    tab_index = e.control.selected_index
                    tab_names = ["Análise de Código", "Síntese de Grafos", "Visualização de Grafos", "Dashboard Analytics"]
                    logger.info(f"Alternando para aba: {tab_names[tab_index]}")
                    
                    # Atualiza componentes específicos quando mudar para certas abas
                    if tab_index == 2:  # Visualização de Grafos
                        try:
                            # Atualiza componentes do grafo se houver dados
                            grafo_view_manager.grafo_card.atualizar_componentes()
                        except Exception as ex:
                            logger.debug(f"Erro ao atualizar componentes do grafo: {ex}")
                            
                    elif tab_index == 3:  # Dashboard Analytics
                        try:
                            # Atualiza estatísticas do dashboard se houver análise
                            if self.dashboard_controller.verificar_analise_disponivel():
                                self.notifier.info("Dashboard atualizado com análise existente")
                        except Exception as ex:
                            logger.debug(f"Erro ao atualizar dashboard: {ex}")
                            
                except Exception as ex:
                    logger.error(f"Erro no evento de mudança de aba: {ex}")

            tabs.on_change = on_tab_change

            # Limpa a página e adiciona os componentes
            self.page.clean()
            self.page.add(self._create_app_bar())
            self.page.add(tabs)
            
            # Configurar cleanup
            self._setup_cleanup()
            
            # Atualizar a página
            self.page.update()
            logger.info("Interface principal carregada com sucesso!")
            
            # Mensagem de boas-vindas
            user = self.auth_controller.get_current_user()
            self.notifier.success(f"Bem-vindo, {user['username']}! Sistema inicializado com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao carregar interface principal: {e}")
            self.notifier.error(f"Erro ao carregar interface: {str(e)}")
            return

    def _create_app_bar(self):
        """Cria a barra de aplicação com informações do usuário"""
        user = self.auth_controller.get_current_user()
        
        return ft.AppBar(
            title=ft.Text("Agente Analista de Código - v2.0"),
            center_title=True,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            actions=[
                # Informações do usuário
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=20),
                        ft.Text(
                            f"{user['username']} ({user['role']})",
                            color=ft.Colors.WHITE,
                            size=14
                        ),
                    ]),
                    padding=10
                ),
                
                # Botão de logout
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Menu do usuário",
                    items=[
                        ft.PopupMenuItem(
                            text="Alterar Senha",
                            icon=ft.Icons.PASSWORD,
                            on_click=self._show_change_password
                        ),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(
                            text="Sair",
                            icon=ft.Icons.LOGOUT,
                            on_click=self._logout
                        )
                    ]
                ),
                
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Recarregar Aplicação",
                    on_click=self._recarregar_aplicacao
                ),
                ft.IconButton(
                    icon=ft.Icons.HELP_OUTLINE,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Ajuda",
                    on_click=lambda _: self.notifier.info("Use as abas para navegar entre as funcionalidades")
                ),
            ]
        )

    def _show_change_password(self, e):
        """Mostra diálogo para alterar senha"""
        def change_password(e):
            old_password = old_password_field.value
            new_password = new_password_field.value
            confirm_password = confirm_password_field.value
            
            if not old_password or not new_password:
                show_error("Preencha todos os campos")
                return
                
            if new_password != confirm_password:
                show_error("Novas senhas não coincidem")
                return
            
            success = self.auth_controller.change_password(old_password, new_password)
            
            if success:
                self.page.dialog.open = False
                self.notifier.success("Senha alterada com sucesso!")
            else:
                show_error("Erro ao alterar senha")
            
            self.page.update()
        
        def show_error(message: str):
            error_text.value = message
            self.page.update()
        
        # Campos do diálogo
        old_password_field = ft.TextField(
            label="Senha atual",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        new_password_field = ft.TextField(
            label="Nova senha",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        confirm_password_field = ft.TextField(
            label="Confirmar nova senha",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        error_text = ft.Text(
            "",
            color=ft.Colors.RED_600,
            size=12
        )
        
        # Diálogo
        change_password_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Alterar Senha"),
            content=ft.Column([
                old_password_field,
                new_password_field,
                confirm_password_field,
                error_text
            ], width=400, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(self.page.dialog, "open", False)),
                ft.ElevatedButton("Alterar Senha", on_click=change_password)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = change_password_dialog
        self.page.dialog.open = True
        self.page.update()

    def _logout(self, e):
        """Realiza logout"""
        self.auth_controller.logout()
        self._cleanup_modules()
        self._show_login_interface()

    def _cleanup_modules(self):
        """Limpa os módulos ao fazer logout"""
        try:
            if hasattr(self, 'analise_controller') and self.analise_controller:
                # Para threads ativas
                if hasattr(self.analise_controller.model, 'thread_manager'):
                    try:
                        self.analise_controller.model.thread_manager.stop()
                        logger.info("Threads de análise paradas")
                    except Exception as ex:
                        logger.error(f"Erro ao parar threads: {ex}")
            
            # Limpa análise atual do dashboard
            if hasattr(self, 'dashboard_controller') and self.dashboard_controller:
                try:
                    self.dashboard_controller.limpar_analise_atual()
                    logger.info("Análise do dashboard limpa")
                except Exception as ex:
                    logger.warning(f"Erro ao limpar análise do dashboard: {ex}")
                    
        except Exception as e:
            logger.error(f"Erro durante cleanup dos módulos: {e}")

    def _recarregar_aplicacao(self, e):
        """Recarrega a aplicação"""
        try:
            logger.info("Recarregando aplicação...")
            self.notifier.info("Recarregando aplicação...")
            
            # Limpa recursos antes de recarregar
            self._cleanup_modules()
            
            # Recarrega a página
            self.page.clean()
            self.main(self.page)
            
        except Exception as ex:
            logger.error(f"Erro ao recarregar aplicação: {ex}")
            self.notifier.error(f"Erro ao recarregar: {str(ex)}")

    def _setup_cleanup(self):
        """Configura cleanup quando a página fechar"""
        def on_window_event(e):
            if e.data == "close":
                logger.info("Janela fechando, executando cleanup...")
                self._cleanup_modules()
        
        self.page.on_window_event = on_window_event
        
        # Registrar cleanup no exit
        def cleanup():
            """Função de cleanup para ser executada no exit"""
            try:
                logger.info("Executando cleanup da aplicação...")
                self._cleanup_modules()
                logger.info("Cleanup concluído com sucesso")
            except Exception as e:
                logger.error(f"Erro durante cleanup: {e}")
        
        atexit.register(cleanup)

def main(page: ft.Page):
    app = MainApp()
    app.main(page)

if __name__ == "__main__":
    try:
        logger.info("Iniciando aplicação Flet...")
        
        # Verifica se diretórios necessários existem
        required_dirs = ["storage", "storage/data", "grafo_gerado", "assets", "modules/auth", "middleware"]
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Inicia a aplicação Flet no modo web para suporte WebView
        ft.app(
            target=main,
            assets_dir="assets",
            view=ft.AppView.WEB_BROWSER,
            port=8550
        )
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário")
        print("\nAplicação encerrada.")
    except Exception as e:
        logger.error(f"Erro fatal ao iniciar aplicação: {e}")
        print(f"Erro fatal: {e}")
        sys.exit(1)