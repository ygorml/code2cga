# core/view_manager_template.py

import flet as ft
from typing import Any, Dict, List
from .ui_components import ConfigCard, ExecutionCard, FilesCard
import logging

logger = logging.getLogger(__name__)

class SimplifiedViewManager:
    """
    ✅ MODELO SIMPLIFICADO: ViewManager genérico usando componentes compartilhados

    Elimina a complexidade dos ViewManagers atuais e usa os componentes UI genéricos:
    - ConfigCard para configurações
    - ExecutionCard para controle
    - FilesCard para seleção de arquivos
    - Layout padronizado
    """

    def __init__(self, controller: Any, notifier: Any, page: ft.Page):
        """
        Inicializa view manager simplificado

        Args:
            controller: Controller do módulo
            notifier: Serviço de notificação
            page: Página Flet
        """
        self.controller = controller
        self.notifier = notifier
        self.page = page

        # Configuração do controller
        self.controller.set_page(page)
        self.controller.set_view(self)

        # Componentes UI
        self.config_card = None
        self.execution_card = None
        self.files_card = None

        logger.info(f"SimplifiedViewManager criado para {controller.__class__.__name__}")

    def create_config_fields(self) -> List[Dict[str, Any]]:
        """
        Método template para criar configurações do módulo
        Sobrescrever nas subclasses específicas
        """
        return [
            {
                'name': 'model',
                'label': 'Modelo LLM',
                'type': 'dropdown',
                'options': ['llama2', 'codellama', 'mistral'],
                'default': 'codellama',
                'width': 300
            },
            {
                'name': 'temperature',
                'label': 'Temperatura',
                'type': 'slider',
                'min': 0.0,
                'max': 2.0,
                'default': 0.7,
                'divisions': 20
            },
            {
                'name': 'detailed_analysis',
                'label': 'Análise Detalhada',
                'type': 'checkbox',
                'default': True
            }
        ]

    def build(self) -> ft.Container:
        """
        Constrói a view completa usando componentes compartilhados
        """
        try:
            # Cria ConfigCard com configurações específicas do módulo
            self.config_card = ConfigCard(
                title=f"Configuração - {self.controller.__class__.__name__.replace('Controller', '')}",
                fields=self.create_config_fields(),
                on_save=self.controller.update_config,
                on_load=self.controller.get_default_config
            )

            # Cria ExecutionCard com callbacks do controller
            self.execution_card = ExecutionCard(
                title="Controle de Execução",
                on_start=self._on_start_operation,
                on_pause=self.controller.pausar_analise if hasattr(self.controller, 'pausar_analise') else None,
                on_stop=self.controller.parar_analise if hasattr(self.controller, 'parar_analise') else None,
                on_reset=self._on_reset_operation
            )

            # Cria FilesCard (se o módulo trabalhar com arquivos)
            self.files_card = FilesCard(
                title="Seleção de Arquivos",
                file_extensions=self.get_file_extensions(),
                on_files_selected=self._on_files_selected
            )

            # Conecta componentes UI ao controller
            progress_components = self.execution_card.get_progress_components()
            self.controller.set_ui_components(**progress_components)

            # Layout principal
            main_content = ft.Column([
                ft.Row([
                    self.config_card,
                    self.execution_card
                ], spacing=20, alignment=ft.MainAxisAlignment.START),
                ft.Container(height=20),
                self.files_card
            ], spacing=10, scroll=ft.ScrollMode.AUTO)

            # Container principal
            return ft.Container(
                content=main_content,
                padding=20,
                expand=True
            )

        except Exception as e:
            logger.error(f"Erro ao construir view: {e}")
            return ft.Container(
                content=ft.Text(f"Erro ao construir view: {e}", color=ft.Colors.RED),
                padding=20
            )

    def get_file_extensions(self) -> List[str]:
        """
        Método template para obter extensões de arquivo suportadas
        Sobrescrever nas subclasses específicas
        """
        return ['.c', '.h', '.cpp', '.hpp', '.py', '.js', '.ts']

    def _on_start_operation(self) -> bool:
        """
        Callback para iniciar operação
        Implementação padrão - sobrescrever se necessário
        """
        try:
            # Obtém arquivos selecionados
            files = self.files_card.get_files()
            if not files:
                self.notifier.error("Nenhum arquivo selecionado")
                return False

            # Obtém configuração
            config = self.config_card.get_config()

            # Inicia operação específica do módulo
            if hasattr(self.controller, 'iniciar_analise'):
                task_id = self.controller.iniciar_analise(files, config)
                return task_id is not None
            elif hasattr(self.controller, 'handle_sintese_execution'):
                # Para módulo de síntese
                self.controller.handle_sintese_execution(
                    files[0] if files else "",
                    config.get('secao_alvo', 'all'),
                    config.get('metodo_busca', 'similaridade'),
                    config.get('limiar_similaridade', 0.7)
                )
                return True
            else:
                self.notifier.error("Método de início não implementado")
                return False

        except Exception as e:
            logger.error(f"Erro ao iniciar operação: {e}")
            self.notifier.error(f"Erro ao iniciar operação: {str(e)}")
            return False

    def _on_reset_operation(self):
        """
        Callback para resetar operação
        """
        try:
            self.files_card.clear_files()
            self.execution_card.set_ready_state()
            self.notifier.info("Operação resetada")

            # Limpa resultados do controller se disponível
            if hasattr(self.controller, 'limpar_resultados'):
                self.controller.limpar_resultados()

        except Exception as e:
            logger.error(f"Erro ao resetar operação: {e}")

    def _on_files_selected(self) -> List[str]:
        """
        Callback para seleção de arquivos
        Implementação padrão - retornaria arquivos reais selecionados
        """
        # Em uma implementação real, abriria diálogo de seleção de arquivos
        # Por ora, retorna lista vazia
        return []

    def get_view_instance(self):
        """
        Retorna instância da view (compatibilidade com código existente)
        """
        return self.build()

    def __call__(self):
        """
        Permite que o view manager seja chamado como função (compatibilidade)
        """
        return self.build()


class AnaliseSimplifiedViewManager(SimplifiedViewManager):
    """
    Exemplo específico para módulo de análise
    """

    def create_config_fields(self) -> List[Dict[str, Any]]:
        """Configurações específicas para análise de código"""
        return [
            {
                'name': 'llm_modelo',
                'label': 'Modelo LLM',
                'type': 'dropdown',
                'options': ['codellama', 'llama2', 'mistral', 'gpt-oss:20b-cloud'],
                'default': 'codellama',
                'width': 300,
                'icon': ft.Iicons.SMART_TOY
            },
            {
                'name': 'linguagem',
                'label': 'Linguagem',
                'type': 'dropdown',
                'options': ['C', 'C++', 'Python', 'JavaScript', 'TypeScript'],
                'default': 'C',
                'width': 200
            },
            {
                'name': 'nivel_analise',
                'label': 'Nível de Análise',
                'type': 'dropdown',
                'options': ['básico', 'detalhado', 'completo'],
                'default': 'detalhado',
                'width': 200
            },
            {
                'name': 'limite_linhas',
                'label': 'Limite de Linhas por Arquivo',
                'type': 'text',
                'default': '1000',
                'width': 200,
                'icon': ft.Iicons.TEXT_FIELDS
            },
            {
                'name': 'incluir_comentarios',
                'label': 'Incluir Comentários na Análise',
                'type': 'checkbox',
                'default': True
            },
            {
                'name': 'analisar_dependencias',
                'label': 'Analisar Dependências',
                'type': 'checkbox',
                'default': True
            },
            {
                'name': 'llm_temperatura',
                'label': 'Temperatura do LLM',
                'type': 'slider',
                'min': 0.0,
                'max': 2.0,
                'default': 0.7,
                'divisions': 20
            },
            {
                'name': 'threads',
                'label': 'Threads de Processamento',
                'type': 'dropdown',
                'options': ['1', '2', '4', '8'],
                'default': '1',
                'width': 150
            }
        ]

    def get_file_extensions(self) -> List[str]:
        """Extensões suportadas para análise de código"""
        return ['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.py', '.js', '.ts', '.java', '.cs']