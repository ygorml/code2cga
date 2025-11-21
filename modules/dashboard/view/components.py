# modules/dashboard/view/components.py

import flet as ft
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class MetricasCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.analise_atual = None
         self.page = None
        
    def build(self) -> ft.Card:
        self.btn_analisar = ft.ElevatedButton(
            "Executar Análise Completa",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._executar_analise,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600
            )
        )
        
        self.progress_ring = ft.ProgressRing(visible=False)
        
        # Grid de métricas
        self.grid_metricas = ft.GridView(
            expand=1,
            runs_count=3,
            max_extent=200,
            child_aspect_ratio=1.2,
            spacing=10,
            run_spacing=10,
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.GREEN_500),
                        title=ft.Text("Métricas de Arquitetura", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Indicadores de qualidade e complexidade")
                    ),
                    ft.Divider(),
                    
                    ft.Container(
                        content=ft.Row([
                            self.btn_analisar,
                            self.progress_ring,
                            ft.Text("Clique para analisar", style=ft.TextStyle(italic=True))
                        ]),
                        padding=10
                    ),
                    
                    ft.Container(
                        content=self.grid_metricas,
                        height=300,
                        padding=10
                    )
                ]),
                padding=20
            ),
            width=600,
            height=500
        )
    
    def _executar_analise(self, e):
        """Executa análise completa"""
        self._atualizar_ui_analise(True)
        
        try:
            self.analise_atual = self.controller.processar_analise_completa()
            self._atualizar_metricas()
            self.notifier.success("Análise concluída!")
            
        except Exception as ex:
            logger.error(f"Erro na análise: {ex}")
            self.notifier.error(f"Erro: {str(ex)}")
        finally:
            self._atualizar_ui_analise(False)
    
    def _atualizar_ui_analise(self, analisando: bool):
        """Atualiza UI durante análise"""
        self.btn_analisar.disabled = analisando
        self.btn_analisar.text = "Analisando..." if analisando else "Executar Análise Completa"
        self.progress_ring.visible = analisando
        self.page.update()
    
    def _atualizar_metricas(self):
        """Atualiza o grid de métricas"""
        if not self.analise_atual:
            return
            
        metricas = self.analise_atual.get('metricas_avancadas', {})
        self.grid_metricas.controls.clear()
        
        metricas_display = [
            ("Acoplamento Médio", f"{metricas.acoplamento_medio:.2f}", ft.Icons.LINK, 
             self._get_cor_metrica(metricas.acoplamento_medio, 2, 5)),
            
            ("Coesão Média", f"{metricas.coesao_media:.3f}", ft.Icons.GROUP_WORK,
             self._get_cor_metrica(metricas.coesao_media, 0.3, 0.6, invertido=True)),
            
            ("Modularidade", f"{metricas.modularidade:.3f}", ft.Icons.VIEW_MODULE,
             self._get_cor_metrica(metricas.modularidade, 0.3, 0.6)),
            
            ("Densidade", f"{metricas.densidade:.3f}", ft.Icons.DENSITY_MEDIUM,
             self._get_cor_metrica(metricas.densidade, 0.1, 0.3)),
            
            ("Centralidade Máx", f"{metricas.centralidade_intermediacao_maxima:.3f}", ft.Icons.HUB,
             self._get_cor_metrica(metricas.centralidade_intermediacao_maxima, 0.1, 0.3, invertido=True)),
            
            ("Componentes", str(metricas.numero_componentes), ft.Icons.ACCOUNT_TREE,
             ft.Colors.BLUE_400),
        ]
        
        for nome, valor, icone, cor in metricas_display:
            self.grid_metricas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(icone, size=30, color=cor),
                        ft.Text(valor, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(nome, size=12, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                    border_radius=8,
                    bgcolor=ft.Colors.BLUE_50 if cor == ft.Colors.BLUE_400 else self._get_cor_fundo(cor),
                    border=ft.border.all(2, cor)
                )
            )
        
        self.page.update()
    
    def _get_cor_metrica(self, valor: float, bom: float, otimo: float, invertido: bool = False) -> str:
        """Retorna cor baseada no valor da métrica"""
        if invertido:
            if valor <= bom: return ft.Colors.GREEN
            elif valor <= otimo: return ft.Colors.ORANGE
            else: return ft.Colors.RED
        else:
            if valor >= otimo: return ft.Colors.GREEN
            elif valor >= bom: return ft.Colors.ORANGE  
            else: return ft.Colors.RED
    
    def _get_cor_fundo(self, cor: str) -> str:
        """Retorna cor de fundo suave baseada na cor principal"""
        cores_fundo = {
            ft.Colors.GREEN: ft.Colors.GREEN_50,
            ft.Colors.ORANGE: ft.Colors.ORANGE_50, 
            ft.Colors.RED: ft.Colors.RED_50,
            ft.Colors.BLUE_400: ft.Colors.BLUE_50
        }
        return cores_fundo.get(cor, ft.Colors.GREY_50)

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
        ])
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.STORIES, color=ft.Colors.PURPLE_500),
                        title=ft.Text("Storytelling & Insights", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Narrativa contextual das métricas")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.conteudo_storytelling,
                        padding=15
                    )
                ]),
                padding=20
            ),
            width=600,
            height=500
        )
    
    def atualizar_storytelling(self, storytelling: Dict[str, str]):
        """Atualiza o conteúdo de storytelling"""
        self.conteudo_storytelling.controls.clear()
        
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

# ... (implementar RecomendacoesCard, NosCriticosCard, HistoricoCard similarmente)

class RecomendacoesCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
         self.page = None
        
    def build(self) -> ft.Card:
        self.lista_recomendacoes = ft.Column()
        
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
        for line in recomendacoes.split('\n • '):
            if line.strip():
                self.lista_recomendacoes.controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.BLUE_500),
                        ft.Text(line, size=14, expand=True)
                    ])
                )

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
                    title=ft.Text(no['node_id'], size=14),
                    subtitle=ft.Text(
                        f"Intermediação: {no['centralidade_intermediacao']:.3f} | "
                        f"Tipo: {no['tipo']}",
                        size=12
                    ),
                    leading=ft.Icon(
                        ft.Icons.CIRCLE,
                        color=ft.Colors.RED if no['centralidade_intermediacao'] > 0.3 
                        else ft.Colors.ORANGE
                    )
                )
            )

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
    
    def _carregar_historico(self, e):
        """Carrega o histórico de execuções"""
        historico = self.controller.obter_historico()
        self.tabela_historico.rows.clear()
        
        for execucao in historico[:10]:  # Mostra apenas últimas 10
            self.tabela_historico.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(execucao['timestamp'][:16])),
                    ft.DataCell(ft.Text(str(execucao['nos_total']))),
                    ft.DataCell(ft.Text(str(execucao['arestas_total']))),
                    ft.DataCell(ft.Text(str(execucao['comunidades_total']))),
                    ft.DataCell(ft.Text(f"{execucao.get('acoplamento_medio', 0):.2f}")),
                    ft.DataCell(ft.Text(f"{execucao.get('modularidade', 0):.3f}")),
                ])
            )
        
        self.page.update()