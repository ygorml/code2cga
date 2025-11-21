# modules/dashboard/view/components/nos_criticos_card.py

import flet as ft
from typing import Dict, List

class NosCriticosCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        
    def build(self) -> ft.Card:
        self.lista_nos_criticos = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED_500),
                        title=ft.Text("Nós Críticos", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Componentes com alta centralidade")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.lista_nos_criticos,
                        height=200
                    )
                ]),
                padding=20
            ),
            width=400
        )
    
    def atualizar_nos_criticos(self, nos_criticos: List[Dict]):
        """Atualiza a lista de nós críticos"""
        self.lista_nos_criticos.controls.clear()
        
        if not nos_criticos:
            self.lista_nos_criticos.controls.append(
                ft.Text("Nenhum nó crítico identificado", color=ft.Colors.GREY_600)
            )
            return
            
        for no in nos_criticos[:5]:  # Mostra apenas top 5
            self.lista_nos_criticos.controls.append(
                ft.ListTile(
                    title=ft.Text(no.get('node_id', 'Unknown'), size=14),
                    subtitle=ft.Text(
                        f"Intermediação: {no.get('centralidade_intermediacao', 0):.3f} | "
                        f"Tipo: {no.get('tipo', 'Unknown')}",
                        size=12
                    ),
                    leading=ft.Icon(
                        ft.Icons.CIRCLE,
                        color=ft.Colors.RED if no.get('centralidade_intermediacao', 0) > 0.3 
                        else ft.Colors.ORANGE
                    )
                )
            )
        
        if self.page:
            self.page.update()
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page