import flet as ft
from ..controller import SinteseController
from services.notification_service import NotificationService
from .components.files_card import FilesCard
from .components.config_card import ConfigCard
from .components.execution_card import ExecutionCard
from .components.log_views import LogViews
from .components.results_card import ResultsCard # NOVO

class ViewManager(ft.Column):
    def __init__(self, controller: SinteseController, notifier: NotificationService, page: ft.Page):
        super().__init__()
        self.controller = controller
        self.notifier = notifier
        self.page = page

        # Instancia os componentes da UI
        self.files_card = FilesCard(self.page)
        self.config_card = ConfigCard()
        self.log_views = LogViews()
        self.results_card = ResultsCard(self.page, self.notifier) 
        
        # Conecta os callbacks de executar e parar
        self.execution_card = ExecutionCard(
            on_execute_callback=self.on_execute_clicked,
            on_stop_callback=self.on_stop_clicked # NOVO
        )

        # Inscreve os métodos da view nos eventos
        self.notifier.subscribe('log_message', self.log_views.add_log_message)
        self.notifier.subscribe('status_update', self.re_enable_button_on_completion)
        self.notifier.subscribe('execution_complete', self.on_execution_complete) # NOVO

        # Configura a Coluna base
        self.controls = [
            self.files_card,
            self.config_card,
            self.execution_card,
            ft.Divider(),
            ft.Row([
                ft.Text("Logs da Aplicação:", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    tooltip="Opções de Log",
                    items=[
                        ft.PopupMenuItem(
                            text="Limpar Logs",
                            icon=ft.Icons.CLEAR,
                            on_click=lambda e: self.clear_logs()
                        ),
                        ft.PopupMenuItem(
                            text="Exportar Logs",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=lambda e: self.export_logs()
                        )
                    ]
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.log_views,
            self.results_card
        ]
        self.scroll = ft.ScrollMode.ADAPTIVE
        self.expand = True

    def on_execute_clicked(self, e):
        """Callback para o botão de execução."""
        self.results_card.visible = False 
        self.execution_card.set_busy(True)
        self.controller.handle_sintese_execution(
            caminho_entrada=self.files_card.get_selected_path(),
            secao_alvo=self.config_card.get_target_section(),
            metodo_busca=self.config_card.get_search_method(),
            limiar_similaridade=self.config_card.get_similarity_threshold()
        )

    def on_stop_clicked(self, e):
        """Callback para o botão de parada."""
        self.controller.handle_sintese_cancellation()

    def on_execution_complete(self, results: list):
        """Callback para quando a execução termina (com sucesso, falha ou cancelamento)."""
        self.results_card.populate_results(results)
        self.update()

    def re_enable_button_on_completion(self, status: str):
        """Callback para reativar o botão quando a tarefa termina."""
        if status.endswith("concluído.") or status.startswith("Falha") or status.endswith("cancelado pelo usuário."):
            if self and self.page:
                self.execution_card.set_busy(False)

    def clear_logs(self):
        """Limpa todos os logs da aplicação."""
        self.log_views.clear_logs()
        self.notifier.info("Logs limpos com sucesso!")

    def export_logs(self):
        """Exporta os logs para um arquivo de texto."""
        import os
        from datetime import datetime

        # Coleta todos os textos dos logs
        logs_text = []
        for control in self.log_views.log_list_view.controls:
            if hasattr(control, 'content') and hasattr(control.content, 'value'):
                logs_text.append(control.content.value)

        if logs_text:
            # Cria o conteúdo do arquivo
            content = f"Logs da Aplicação - Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            content += "=" * 80 + "\n\n"
            content += "\n".join(logs_text)

            # Salva no diretório de export
            export_dir = "storage/export"
            os.makedirs(export_dir, exist_ok=True)

            filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(export_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.notifier.success(f"Logs exportados para: {filepath}")
        else:
            self.notifier.warning("Não há logs para exportar.")