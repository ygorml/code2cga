# grafo/view/view_manager.py

import flet as ft
from .components import GrafoCard, EstatisticasCard, ComunidadesCard
import logging

logger = logging.getLogger(__name__)

class ViewManager:
    def __init__(self, controller, notifier, page: ft.Page):
        self.controller = controller
        self.notifier = notifier
        self.page = page
        
        # Inicializa componentes
        self.grafo_card = GrafoCard(controller, notifier)
        self.estatisticas_card = EstatisticasCard(controller, notifier)
        self.comunidades_card = ComunidadesCard(controller, notifier)

    def set_dashboard_controller(self, dashboard_controller):  # NOVO: Método para conectar com dashboard
        """Define o controlador do dashboard para integração"""
        self.dashboard_controller = dashboard_controller
        self.grafo_card.dashboard_controller = dashboard_controller
        logger.info("Dashboard controller conectado ao módulo de grafos")

    def __call__(self) -> ft.Container:
        """Retorna a view principal do módulo"""
        return ft.Container(
            content=ft.Column([
                self.grafo_card.build(),
                ft.Row([
                    self.estatisticas_card.build(),
                    self.comunidades_card.build()
                ], expand=True),
            ], scroll=ft.ScrollMode.ADAPTIVE),
            padding=20,
            expand=True
        )