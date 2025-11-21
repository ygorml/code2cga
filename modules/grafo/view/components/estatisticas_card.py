# grafo/view/estatisticas_card.py


import flet as ft

class EstatisticasCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.estatisticas = {}
        
    def build(self) -> ft.Card:
        self.conteudo_estatisticas = ft.Column([
            ft.Text("Estatísticas do Grafo", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Processe os grafos para ver estatísticas", 
                   size=14, color=ft.Colors.GREY_600)
        ])
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ANALYTICS),
                        title=ft.Text("Estatísticas"),
                        subtitle=ft.Text("Métricas e análises do grafo")
                    ),
                    ft.Divider(),
                    self.conteudo_estatisticas
                ]),
                padding=20
            )
        )
    
    def atualizar_estatisticas(self, estatisticas: dict):
        """Atualiza as estatísticas exibidas"""
        self.estatisticas = estatisticas
        
        if not estatisticas:
            self.conteudo_estatisticas.controls = [
                ft.Text("Estatísticas do Grafo", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Nenhum dado disponível", size=14, color=ft.Colors.GREY_600)
            ]
            return
            
        # Cria grid de estatísticas
        metricas = ft.GridView(
            expand=1,
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        # Adiciona métricas
        metricas_display = [
            ("Nós", estatisticas.get("num_nos", 0), ft.Icons.CIRCLE),
            ("Arestas", estatisticas.get("num_arestas", 0), ft.Icons.LINE_STYLE),
            ("Comunidades", estatisticas.get("num_comunidades", 0), ft.Icons.GROUP_WORK),
            ("Densidade", f"{estatisticas.get('densidade', 0):.3f}", ft.Icons.DENSITY_MEDIUM),
        ]
        
        for nome, valor, icone in metricas_display:
            metricas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(icone, size=30, color=ft.Colors.BLUE_400),
                        ft.Text(str(valor), size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(nome, size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50,
                )
            )
        
        self.conteudo_estatisticas.controls = [
            ft.Text("Estatísticas do Grafo", size=16, weight=ft.FontWeight.BOLD),
            metricas
        ]