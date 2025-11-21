# modules/dashboard/view/components/storytelling_card.py

import flet as ft
from typing import Dict

class StorytellingCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        
    def build(self) -> ft.Card:
        self.conteudo_storytelling = ft.Column([
            ft.Text("Análise Contextual", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Execute a análise para ver insights sobre a arquitetura...", 
                   color=ft.Colors.GREY_600)
        ], scroll=ft.ScrollMode.ADAPTIVE)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.PURPLE_500),
                        title=ft.Text("Storytelling & Insights", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Narrativa contextual das métricas")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.conteudo_storytelling,
                        padding=15,
                        height=400
                    )
                ]),
                padding=20
            ),
            width=600
        )
    
    def atualizar_storytelling(self, storytelling: Dict[str, str]):
        """Atualiza o conteúdo de storytelling"""
        self.conteudo_storytelling.controls.clear()
        
        if not storytelling:
            self.conteudo_storytelling.controls.extend([
                ft.Text("📊 Análise Contextual", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Execute a análise completa para ver insights detalhados...", 
                       color=ft.Colors.GREY_600)
            ])
            return
        
        self.conteudo_storytelling.controls.extend([
            ft.Text("📊 Resumo da Arquitetura", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(storytelling.get('resumo_geral', ''), size=14),
            
            ft.Divider(),
            
            ft.Text("💡 Insights Técnicos", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(storytelling.get('insights_tecnicos', ''), size=14),
            
            ft.Divider(),
            
            ft.Text("⚠️ Pontos de Atenção", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(storytelling.get('pontos_atencao', ''), size=14),
        ])
        
        if self.page:
            self.page.update()
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page