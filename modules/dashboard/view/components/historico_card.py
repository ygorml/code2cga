# modules/dashboard/view/components/historico_card.py

import flet as ft
import logging

logger = logging.getLogger(__name__)

class HistoricoCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        
    def build(self) -> ft.Card:
        self.tabela_historico = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data")),
                ft.DataColumn(ft.Text("Nós")),
                ft.DataColumn(ft.Text("Arestas")),
                ft.DataColumn(ft.Text("Comunidades")),
                ft.DataColumn(ft.Text("Acoplamento")),
                ft.DataColumn(ft.Text("Modularidade")),
            ],
            rows=[]
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_500),
                        title=ft.Text("Histórico de Execuções", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Evolução temporal das métricas")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column([
                            ft.ElevatedButton(
                                "Carregar Histórico",
                                icon=ft.Icons.REFRESH,
                                on_click=self._carregar_historico
                            ),
                            ft.Container(
                                content=ft.ListView(
                                    [self.tabela_historico],
                                    height=300
                                ),
                                padding=10
                            )
                        ])
                    )
                ]),
                padding=20
            )
        )
    
    def _carregar_historico(self, e=None):
        """Carrega o histórico de execuções"""
        try:
            historico = self.controller.obter_historico_analises_completas()
            self.tabela_historico.rows.clear()
            
            for execucao in historico[:10]:  # Mostra apenas últimas 10
                self.tabela_historico.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(execucao.get('timestamp', '')[:16])),
                        ft.DataCell(ft.Text(str(execucao.get('resultado_grafo', {}).get('estatisticas', {}).get('num_nos', 0)))),
                        ft.DataCell(ft.Text(str(execucao.get('resultado_grafo', {}).get('estatisticas', {}).get('num_arestas', 0)))),
                        ft.DataCell(ft.Text(str(execucao.get('resultado_grafo', {}).get('estatisticas', {}).get('num_comunidades', 0)))),
                        ft.DataCell(ft.Text(f"{execucao.get('metricas_resumidas', {}).get('acoplamento_medio', 0):.2f}")),
                        ft.DataCell(ft.Text(f"{execucao.get('metricas_resumidas', {}).get('modularidade', 0):.3f}")),
                    ])
                )
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao carregar histórico: {ex}")
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page