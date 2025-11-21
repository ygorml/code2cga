# grafo/view/comunidades_card.py

import flet as ft

class ComunidadesCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.comunidades = {}
        
    def build(self) -> ft.Card:
        self.lista_comunidades = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.GROUP_WORK),
                        title=ft.Text("Comunidades Detectadas"),
                        subtitle=ft.Text("Grupos de nós densamente conectados")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.lista_comunidades,
                        height=300
                    )
                ]),
                padding=20
            )
        )
    
    def atualizar_comunidades(self, comunidades: dict):
        """Atualiza a lista de comunidades"""
        self.comunidades = comunidades
        self.lista_comunidades.controls.clear()
        
        if not comunidades:
            self.lista_comunidades.controls.append(
                ft.Text("Nenhuma comunidade detectada", 
                       color=ft.Colors.GREY_600)
            )
            return
            
        for cid, membros in sorted(comunidades.items(), 
                                 key=lambda item: len(item[1]), 
                                 reverse=True)[:10]:  # Mostra apenas top 10
            expandable = ft.ExpansionTile(
                title=ft.Text(f"Comunidade {cid}"),
                subtitle=ft.Text(f"{len(membros)} membros"),
                controls=[
                    ft.ListTile(
                        title=ft.Text(membro),
                        dense=True
                    ) for membro in membros[:10]  # Mostra apenas primeiros 10 membros
                ]
            )
            self.lista_comunidades.controls.append(expandable)