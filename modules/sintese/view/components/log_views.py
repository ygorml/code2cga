# ./modules/sintese/view/components/log_views.py
from datetime import datetime
import flet as ft

class LogViews(ft.Container):
    def __init__(self):
    
        self.log_list_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        
        # Configura o Container base usando super().__init__()
        super().__init__(
            content=self.log_list_view,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=ft.border_radius.all(5),
            padding=10,
            height=300,
            expand=True # Permite que o log ocupe o espaço disponível
        )

    def add_log_message(self, message: str, level: str = "INFO"):
        color = {
            "INFO": ft.Colors.BLACK,
            "WARNING": ft.Colors.ORANGE_700,
            "ERROR": ft.Colors.RED_700
        }.get(level, ft.Colors.BLACK)

        log_entry = ft.Text(
            f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}",
            color=color,
            size=12,
            selectable=True  # Permite selecionar o texto
        )
        self.log_list_view.controls.append(log_entry)

        # Adiciona fundo para melhor legibilidade
        log_container = ft.Container(
            content=log_entry,
            bgcolor=ft.Colors.GREY_50 if level == "INFO" else
                     ft.Colors.AMBER_50 if level == "WARNING" else
                     ft.Colors.RED_50,
            padding=ft.padding.symmetric(horizontal=5, vertical=2),
            border_radius=3
        )
        self.log_list_view.controls[-1] = log_container

        # Limita o número de logs para evitar problemas de performance
        if len(self.log_list_view.controls) > 100:
            self.log_list_view.controls.pop(0)

        self.update()

    def clear_logs(self):
        """Limpa todos os logs da view."""
        self.log_list_view.controls.clear()
        self.update()