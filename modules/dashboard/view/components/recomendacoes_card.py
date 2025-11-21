# modules/dashboard/view/components/recomendacoes_card.py

import flet as ft

class RecomendacoesCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        
    def build(self) -> ft.Card:
        self.lista_recomendacoes = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LIGHTBULB, color=ft.Colors.ORANGE_500),
                        title=ft.Text("Recomendações", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Ações sugeridas para melhoria")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.lista_recomendacoes,
                        height=200
                    )
                ]),
                padding=20
            ),
            width=400
        )
    
    def atualizar_recomendacoes(self, recomendacoes: str):
        """Atualiza a lista de recomendações"""
        self.lista_recomendacoes.controls.clear()
        
        if not recomendacoes:
            self.lista_recomendacoes.controls.append(
                ft.Text("Nenhuma recomendação no momento", color=ft.Colors.GREY_600)
            )
            return
            
        # Divide as recomendações por bullet points
        for line in recomendacoes.split('• '):
            if line.strip():
                self.lista_recomendacoes.controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.BLUE_500),
                        ft.Text(line.strip(), size=14, expand=True)
                    ])
                )
        
        if self.page:
            self.page.update()
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page