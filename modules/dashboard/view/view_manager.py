# modules/dashboard/view/view_manager.py

import flet as ft
import logging
from .components.metricas_card import MetricasCard
from .components.storytelling_card import StorytellingCard
from .components.recomendacoes_card import RecomendacoesCard
from .components.nos_criticos_card import NosCriticosCard
from .components.historico_card import HistoricoCard
from .components.rag_analyser import RagAnalyserCard

logger = logging.getLogger(__name__)

class ViewManager:
    def __init__(self, controller, notifier, page: ft.Page):
        self.controller = controller
        self.notifier = notifier
        self.page = page
        
        # Inicializa todos os componentes


        self.metricas_card = MetricasCard(controller, notifier)
        self.storytelling_card = StorytellingCard(controller, notifier)
        self.recomendacoes_card = RecomendacoesCard(controller, notifier)
        self.nos_criticos_card = NosCriticosCard(controller, notifier)
        self.historico_card = HistoricoCard(controller, notifier)
        self.rag_analyser_card = RagAnalyserCard(controller, notifier)
        
        # Define a página em todos os componentes
        self._set_page_in_components()
        
    def _set_page_in_components(self):
        """Define a página em todos os componentes filhos"""
        # Adicione verificações mais robustas
        componentes = [
            self.metricas_card, self.storytelling_card, self.recomendacoes_card,
            self.nos_criticos_card, self.historico_card, self.rag_analyser_card
        ]
        
        for componente in componentes:
            if hasattr(componente, 'set_page'):
                try:
                    componente.set_page(self.page)
                except Exception as e:
                    logger.error(f"Erro ao definir página no componente {type(componente).__name__}: {e}")
        
    def __call__(self) -> ft.Container:
        """Retorna a view principal do dashboard"""
        return ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DASHBOARD, size=32, color=ft.Colors.BLUE_700),
                        ft.Text("Dashboard Analytics", 
                               size=28, 
                               weight=ft.FontWeight.BOLD,
                               color=ft.Colors.BLUE_700),
                    ]),
                    padding=20
                ),
                
                ft.Divider(),
                
                # Botão principal de análise
                ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.GREEN_500),
                                    title=ft.Text("Análise Completa do Sistema", 
                                                 size=18, 
                                                 weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text("Processe todas as métricas e prepare o contexto para análise com IA")
                                ),
                                ft.Container(
                                    content=ft.Row([
                                        ft.ElevatedButton(
                                            "🚀 Executar Análise Completa",
                                            icon=ft.Icons.PLAY_ARROW,
                                            on_click=self._executar_analise_completa,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.WHITE,
                                                bgcolor=ft.Colors.GREEN_600,
                                                padding=ft.padding.symmetric(horizontal=25, vertical=15)
                                            )
                                        ),
                                        ft.ElevatedButton(
                                            "🔄 Atualizar Dashboard",
                                            icon=ft.Icons.REFRESH,
                                            on_click=self._atualizar_dashboard,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.WHITE,
                                                bgcolor=ft.Colors.BLUE_600
                                            )
                                        )
                                    ]),
                                    padding=15
                                )
                            ]),
                            padding=10
                        )
                    ),
                    padding=10
                ),
                
                # Primeira linha: Métricas e Storytelling
                ft.Row([
                    self.metricas_card.build(),
                    self.storytelling_card.build()
                ], expand=True),
                
                # Segunda linha: Recomendações e Nós Críticos
                ft.Row([
                    self.recomendacoes_card.build(),
                    self.nos_criticos_card.build()
                ], expand=True),
                
                # RAG Analyser (ocupando linha completa)
                ft.Container(
                    content=self.rag_analyser_card.build(),
                    padding=10
                ),
                
                # Histórico
                ft.Container(
                    content=self.historico_card.build(),
                    padding=10
                )
                
            ], scroll=ft.ScrollMode.ADAPTIVE),
            padding=20,
            expand=True
        )
    
    def _executar_analise_completa(self, e):
        """Executa análise completa"""
        try:
            resultado = self.controller.processar_analise_completa()
            if resultado:
                self._atualizar_todos_componentes(resultado)
                self.notifier.success("✅ Análise completa concluída! Dashboard atualizado.")
            else:
                self.notifier.error("❌ Falha na análise. Verifique se há dados de grafo disponíveis.")
        except Exception as ex:
            logger.error(f"Erro na análise completa: {ex}")
            self.notifier.error(f"Erro na análise: {str(ex)}")
    
    def _atualizar_dashboard(self, e):
        """Atualiza o dashboard com dados existentes"""
        try:
            # Verifica se há análise atual disponível
            analise_atual = self.controller.get_analise_atual()
            if analise_atual:
                self._atualizar_todos_componentes(analise_atual)
                self.notifier.info("📊 Dashboard atualizado com análise existente")
            else:
                self.notifier.warning("Nenhuma análise disponível. Execute a análise completa primeiro.")
        except Exception as ex:
            logger.error(f"Erro ao atualizar dashboard: {ex}")
            self.notifier.error(f"Erro ao atualizar: {str(ex)}")
    
    def _atualizar_todos_componentes(self, analise: dict):
        """Atualiza todos os componentes com os dados da análise"""
        try:
            # Atualiza métricas
            if hasattr(self.metricas_card, 'atualizar_metricas'):
                metricas = analise.get('metricas_avancadas', {})
                self.metricas_card.atualizar_metricas(metricas)
            
            # Atualiza storytelling
            if hasattr(self.storytelling_card, 'atualizar_storytelling'):
                storytelling = analise.get('storytelling', {})
                self.storytelling_card.atualizar_storytelling(storytelling)
            
            # Atualiza recomendações
            if hasattr(self.recomendacoes_card, 'atualizar_recomendacoes'):
                recomendacoes = storytelling.get('recomendacoes', '') if storytelling else ''
                self.recomendacoes_card.atualizar_recomendacoes(recomendacoes)
            
            # Atualiza nós críticos
            if hasattr(self.nos_criticos_card, 'atualizar_nos_criticos'):
                resultado_grafo = analise.get('resultado_grafo', {})
                nos_criticos = resultado_grafo.get('nos_criticos', [])
                self.nos_criticos_card.atualizar_nos_criticos(nos_criticos)
            
            # Atualiza histórico
            if hasattr(self.historico_card, '_carregar_historico'):
                self.historico_card._carregar_historico()
            
            # Força atualização da página
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao atualizar componentes: {ex}")