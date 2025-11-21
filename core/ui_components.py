# core/ui_components.py

"""
UI Components - Componentes Genéricos de Interface do Usuário

Este módulo implementa componentes de UI genéricos e reutilizáveis que eliminam
a duplicação de Cards em todos os módulos da aplicação, seguindo os princípios
da refatoração de simplificação.

Componentes implementados:
- ConfigCard: Card dinâmico de configuração
- ExecutionCard: Card de controle de execução
- FilesCard: Card de seleção de arquivos

Benefícios:
- Eliminação completa de código duplicado
- Interface consistente entre módulos
- Configuração dinâmica via JSON/dicionários
- Estado padronizado de UI
- Manutenção centralizada

Author: Claude Code Assistant
Version: 2.0 (Genérico)
Since: 2025-11-18
Refactoring: Substitui Cards duplicados por componentes genéricos
"""

import flet as ft
from typing import List, Dict, Any, Callable, Optional, Union
import logging

logger = logging.getLogger(__name__)

class ConfigCard(ft.Card):
    """
    Card de configuração genérico e reutilizável.

    Este componente elimina a duplicação de ConfigCard em todos os módulos,
    fornecendo uma interface consistente para configuração de parâmetros.

    Módulos que utilizam:
    - Análise: configuração de LLM, prompts, linguagens
    - Síntese: configuração de busca e similaridade
    - Dashboard: configuração de analytics e RAG

    Características:
    - Criação dinâmica de campos via configuração
    - Suporte a múltiplos tipos de campos (text, dropdown, checkbox, slider, switch)
    - Callbacks configuráveis para save/load
    - Validação e tratamento de erros integrados
    - Interface responsiva e consistente

    Exemplo de uso:
        fields = [
            {
                'name': 'model',
                'label': 'Modelo LLM',
                'type': 'dropdown',
                'options': ['codellama', 'llama2'],
                'default': 'codellama'
            },
            {
                'name': 'temperature',
                'label': 'Temperatura',
                'type': 'slider',
                'min': 0.0,
                'max': 2.0,
                'default': 0.7
            }
        ]

        config_card = ConfigCard(
            title="Configuração da Análise",
            fields=fields,
            on_save=lambda config: save_config(config),
            on_load=lambda: get_default_config()
        )

    Attributes:
        title (str): Título exibido no card
        fields (List[Dict]): Configuração dos campos dinâmicos
        on_save (Optional[Callable]): Callback para salvar configuração
        on_load (Optional[Callable]): Callback para carregar configuração padrão
        field_controls (Dict): Controles Flet criados dinamicamente
    """

    def __init__(self, title: str, fields: List[Dict[str, Any]],
                 on_save: Callable = None, on_load: Callable = None):
        """
        Inicializa card de configuração genérico

        Args:
            title: Título do card
            fields: Lista de configurações de campos
            on_save: Callback para salvar configurações
            on_load: Callback para carregar configurações
        """
        super().__init__()

        self.title = title
        self.fields = fields
        self.on_save = on_save
        self.on_load = on_load
        self.field_controls = {}

        self.elevation = 3
        self._build_content()

    def _build_content(self):
        """Constrói o conteúdo do card"""
        # Cria campos dinamicamente
        field_controls = []

        for field in self.fields:
            field_type = field.get('type', 'text')
            field_name = field['name']
            field_label = field['label']
            field_value = field.get('default', '')
            field_options = field.get('options', [])

            if field_type == 'text':
                control = ft.TextField(
                    label=field_label,
                    value=str(field_value),
                    width=field.get('width', 300),
                    prefix_icon=field.get('icon')
                )

            elif field_type == 'dropdown':
                control = ft.Dropdown(
                    label=field_label,
                    options=[ft.dropdown.Option(opt) for opt in field_options],
                    value=str(field_value),
                    width=field.get('width', 300)
                )

            elif field_type == 'checkbox':
                control = ft.Checkbox(
                    label=field_label,
                    value=bool(field_value)
                )

            elif field_type == 'slider':
                control = ft.Slider(
                    label=field_label,
                    min=field.get('min', 0),
                    max=field.get('max', 100),
                    value=float(field_value),
                    divisions=field.get('divisions', 10)
                )

            elif field_type == 'switch':
                control = ft.Switch(
                    label=field_label,
                    value=bool(field_value)
                )

            else:  # default to text
                control = ft.TextField(
                    label=field_label,
                    value=str(field_value),
                    width=field.get('width', 300)
                )

            self.field_controls[field_name] = control
            field_controls.append(control)

        # Botões de ação
        save_button = ft.ElevatedButton(
            "Salvar Configuração",
            icon=ft.Icons.SAVE,
            on_click=self._on_save_clicked
        )

        load_button = ft.OutlinedButton(
            "Carregar Padrão",
            icon=ft.Icons.REFRESH,
            on_click=self._on_load_clicked
        )

        actions_row = ft.Row([
            save_button,
            load_button
        ], alignment=ft.MainAxisAlignment.END)

        # Conteúdo do card
        self.content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(10, 15)
                ),
                ft.Divider(),
                ft.Column(field_controls, spacing=10),
                ft.Container(height=10),
                actions_row
            ], spacing=5),
            padding=15
        )

    def _on_save_clicked(self, e):
        """Handle save button click"""
        if self.on_save:
            config = self.get_config()
            try:
                success = self.on_save(config)
                if success:
                    logger.info(f"Configuração '{self.title}' salva com sucesso")
            except Exception as ex:
                logger.error(f"Erro ao salvar configuração: {ex}")

    def _on_load_clicked(self, e):
        """Handle load button click"""
        if self.on_load:
            try:
                config = self.on_load()
                self.set_config(config)
                logger.info(f"Configuração padrão '{self.title}' carregada")
            except Exception as ex:
                logger.error(f"Erro ao carregar configuração: {ex}")

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual dos campos"""
        config = {}

        for field in self.fields:
            field_name = field['name']
            field_type = field.get('type', 'text')
            control = self.field_controls.get(field_name)

            if control:
                if field_type in ['text', 'dropdown']:
                    config[field_name] = control.value
                elif field_type in ['checkbox', 'switch']:
                    config[field_name] = control.value
                elif field_type == 'slider':
                    config[field_name] = control.value

        return config

    def set_config(self, config: Dict[str, Any]):
        """Define configuração dos campos"""
        for field_name, value in config.items():
            control = self.field_controls.get(field_name)
            if control:
                control.value = value


class ExecutionCard(ft.Card):
    """
    ✅ COMPONENTE GENÉRICO: Card de controle de execução

    Elimina duplicação em todos os módulos:
    - Botões start/pause/stop padronizados
    - Status e progresso consistentes
    - Callbacks configuráveis
    """

    def __init__(self, title: str = "Controle de Execução",
                 on_start: Callable = None, on_pause: Callable = None,
                 on_stop: Callable = None, on_reset: Callable = None):
        """
        Inicializa card de execução genérico

        Args:
            title: Título do card
            on_start: Callback para iniciar operação
            on_pause: Callback para pausar operação
            on_stop: Callback para parar operação
            on_reset: Callback para resetar operação
        """
        super().__init__()

        self.title = title
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.on_reset = on_reset

        self.elevation = 3

        # Estado
        self.is_running = False
        self.is_paused = False

        # Componentes UI
        self.status_text = ft.Text("Status: Pronto", color=ft.Colors.GREY_600)
        self.progress_bar = ft.ProgressBar(visible=False)
        self.progress_text = ft.Text("", visible=False)

        # Botões
        self.start_button = ft.ElevatedButton(
            "Iniciar",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_start_clicked
        )

        self.pause_button = ft.ElevatedButton(
            "Pausar",
            icon=ft.Icons.PAUSE,
            visible=False,
            on_click=self._on_pause_clicked
        )

        self.stop_button = ft.ElevatedButton(
            "Parar",
            icon=ft.Icons.STOP,
            visible=False,
            on_click=self._on_stop_clicked
        )

        self.reset_button = ft.OutlinedButton(
            "Resetar",
            icon=ft.Icons.REFRESH,
            on_click=self._on_reset_clicked
        )

        self._build_content()

    def _build_content(self):
        """Constrói o conteúdo do card"""
        buttons_row = ft.Row([
            self.start_button,
            self.pause_button,
            self.stop_button,
            self.reset_button
        ], alignment=ft.MainAxisAlignment.START)

        self.content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(10, 15)
                ),
                ft.Divider(),
                self.status_text,
                ft.Container(height=5),
                self.progress_bar,
                self.progress_text,
                ft.Container(height=10),
                buttons_row
            ], spacing=5),
            padding=15
        )

    def _on_start_clicked(self, e):
        """Handle start button click"""
        if self.on_start and not self.is_running:
            try:
                success = self.on_start()
                if success:
                    self.set_running_state()
            except Exception as ex:
                logger.error(f"Erro ao iniciar operação: {ex}")

    def _on_pause_clicked(self, e):
        """Handle pause button click"""
        if self.on_pause and self.is_running:
            try:
                success = self.on_pause()
                if success:
                    self.set_paused_state()
            except Exception as ex:
                logger.error(f"Erro ao pausar operação: {ex}")

    def _on_stop_clicked(self, e):
        """Handle stop button click"""
        if self.on_stop:
            try:
                success = self.on_stop()
                if success:
                    self.set_stopped_state()
            except Exception as ex:
                logger.error(f"Erro ao parar operação: {ex}")

    def _on_reset_clicked(self, e):
        """Handle reset button click"""
        if self.on_reset:
            try:
                self.on_reset()
                self.set_ready_state()
            except Exception as ex:
                logger.error(f"Erro ao resetar operação: {ex}")

    def set_running_state(self):
        """Atualiza UI para estado executando"""
        self.is_running = True
        self.is_paused = False
        self.status_text.value = "Status: Executando"
        self.status_text.color = ft.Colors.BLUE_700
        self.progress_bar.visible = True
        self.start_button.visible = False
        self.pause_button.visible = True
        self.stop_button.visible = True

    def set_paused_state(self):
        """Atualiza UI para estado pausado"""
        self.is_running = False
        self.is_paused = True
        self.status_text.value = "Status: Pausado"
        self.status_text.color = ft.Colors.ORANGE_700
        self.pause_button.text = "Retomar"
        self.pause_button.icon = ft.Icons.PLAY_ARROW
        self.start_button.visible = False

    def set_resumed_state(self):
        """Atualiza UI para estado retomado"""
        self.is_running = True
        self.is_paused = False
        self.status_text.value = "Status: Executando"
        self.status_text.color = ft.Colors.BLUE_700
        self.pause_button.text = "Pausar"
        self.pause_button.icon = ft.Icons.PAUSE

    def set_stopped_state(self):
        """Atualiza UI para estado parado"""
        self.is_running = False
        self.is_paused = False
        self.status_text.value = "Status: Parado"
        self.status_text.color = ft.Colors.RED_700
        self.progress_bar.visible = False
        self.start_button.visible = True
        self.pause_button.visible = False
        self.stop_button.visible = False

    def set_ready_state(self):
        """Atualiza UI para estado pronto"""
        self.is_running = False
        self.is_paused = False
        self.status_text.value = "Status: Pronto"
        self.status_text.color = ft.Colors.GREY_600
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.progress_bar.value = 0
        self.start_button.visible = True
        self.pause_button.visible = False
        self.stop_button.visible = False

    def set_completed_state(self):
        """Atualiza UI para estado concluído"""
        self.is_running = False
        self.is_paused = False
        self.status_text.value = "Status: Concluído"
        self.status_text.color = ft.Colors.GREEN_700
        self.start_button.visible = True
        self.pause_button.visible = False
        self.stop_button.visible = False

    def update_progress(self, value: float, text: str = None):
        """Atualiza barra de progresso"""
        self.progress_bar.value = value
        if text:
            self.progress_text.value = text
            self.progress_text.visible = True

    def get_progress_components(self):
        """Retorna componentes de progresso para controller"""
        return {
            'progress_bar': self.progress_bar,
            'progress_text': self.progress_text,
            'status_text': self.status_text,
            'info_text': self.progress_text  # Usa progress_text como info_text
        }


class FilesCard(ft.Card):
    """
    ✅ COMPONENTE GENÉRICO: Card de seleção de arquivos

    Elimina duplicação em todos os módulos:
    - Seleção de arquivos padronizada
    - Lista de arquivos selecionados
    - Validação e filtros
    """

    def __init__(self, title: str = "Seleção de Arquivos",
                 file_extensions: List[str] = None,
                 on_files_selected: Callable = None,
                 on_clear: Callable = None):
        """
        Inicializa card de arquivos genérico

        Args:
            title: Título do card
            file_extensions: Extensões de arquivo permitidas
            on_files_selected: Callback quando arquivos são selecionados
            on_clear: Callback para limpar seleção
        """
        super().__init__()

        self.title = title
        self.file_extensions = file_extensions or ['*']
        self.on_files_selected = on_files_selected
        self.on_clear = on_clear

        self.elevation = 3
        self.selected_files = []

        # Componentes UI
        self.files_list = ft.ListView(expand=1, spacing=5, padding=5)
        self.count_text = ft.Text("Nenhum arquivo selecionado", color=ft.Colors.GREY_600)

        self._build_content()

    def _build_content(self):
        """Constrói o conteúdo do card"""
        select_button = ft.ElevatedButton(
            "Selecionar Arquivos",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_select_clicked
        )

        clear_button = ft.OutlinedButton(
            "Limpar Seleção",
            icon=ft.Icons.CLEAR,
            on_click=self._on_clear_clicked
        )

        buttons_row = ft.Row([select_button, clear_button], alignment=ft.MainAxisAlignment.START)

        # Área de arquivos selecionados
        files_container = ft.Container(
            content=ft.Column([
                ft.Text("Arquivos Selecionados:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.files_list,
                    height=200,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=5
                ),
                self.count_text
            ], spacing=10),
            width=400
        )

        self.content = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(10, 15)
                ),
                ft.Divider(),
                buttons_row,
                ft.Container(height=10),
                files_container
            ], spacing=5),
            padding=15
        )

    def _on_select_clicked(self, e):
        """Handle select files button click"""
        # Em uma implementação real, abriria o diálogo de seleção de arquivos
        # Por ora, chamamos o callback
        if self.on_files_selected:
            try:
                files = self.on_files_selected()
                self.set_files(files)
            except Exception as ex:
                logger.error(f"Erro ao selecionar arquivos: {ex}")

    def _on_clear_clicked(self, e):
        """Handle clear button click"""
        self.clear_files()
        if self.on_clear:
            try:
                self.on_clear()
            except Exception as ex:
                logger.error(f"Erro ao limpar arquivos: {ex}")

    def set_files(self, files: List[str]):
        """Define a lista de arquivos selecionados"""
        self.selected_files = files
        self._update_files_list()

    def add_file(self, file_path: str):
        """Adiciona um arquivo à seleção"""
        if file_path not in self.selected_files:
            self.selected_files.append(file_path)
            self._update_files_list()

    def remove_file(self, file_path: str):
        """Remove um arquivo da seleção"""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            self._update_files_list()

    def clear_files(self):
        """Limpa todos os arquivos selecionados"""
        self.selected_files = []
        self._update_files_list()

    def _update_files_list(self):
        """Atualiza a lista visual de arquivos"""
        self.files_list.controls.clear()

        for file_path in self.selected_files:
            # Extrai apenas o nome do arquivo
            file_name = file_path.split('/')[-1].split('\\')[-1]

            file_item = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.DESCRIPTION, size=16, color=ft.Colors.BLUE_600),
                    ft.Text(file_name, expand=1, size=12),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_size=16,
                        on_click=lambda e, fp=file_path: self.remove_file(fp)
                    )
                ]),
                padding=ft.padding.symmetric(5, 8),
                bgcolor=ft.Colors.GREY_50,
                border_radius=4
            )
            self.files_list.controls.append(file_item)

        # Atualiza contador
        count = len(self.selected_files)
        if count == 0:
            self.count_text.value = "Nenhum arquivo selecionado"
            self.count_text.color = ft.Colors.GREY_600
        elif count == 1:
            self.count_text.value = "1 arquivo selecionado"
            self.count_text.color = ft.Colors.BLUE_600
        else:
            self.count_text.value = f"{count} arquivos selecionados"
            self.count_text.color = ft.Colors.BLUE_600

    def get_files(self) -> List[str]:
        """Retorna lista de arquivos selecionados"""
        return self.selected_files.copy()