# grafo/view/grafo_card.py

import flet as ft
import os
import base64
import webbrowser
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GrafoCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.dashboard_controller = None 
        self.html_content = None
        self.webview = None
        self.estatisticas_card = None
        self.comunidades_card = None
        self.page = None  
        
    def set_componentes_relacionados(self, estatisticas_card, comunidades_card):
        """Define referências para os outros componentes"""
        self.estatisticas_card = estatisticas_card
        self.comunidades_card = comunidades_card
        
    def set_dashboard_controller(self, dashboard_controller): 
        """Define o controlador do dashboard para integração"""
        self.dashboard_controller = dashboard_controller
        
    def build(self) -> ft.Card:
        # Botão principal de processamento
        self.btn_processar = ft.ElevatedButton(
            "Processar Grafos",
            icon=ft.Icons.NETWORK_CHECK,
            on_click=self._processar_grafos,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600
            )
        )
        
        # Botão para abrir no navegador externo
        self.btn_abrir_externo = ft.ElevatedButton(
            "Abrir no Navegador",
            icon=ft.Icons.OPEN_IN_BROWSER,
            on_click=self._abrir_externo,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600
            )
        )
        
        # Botão de debug
        self.btn_debug = ft.ElevatedButton(
            "Debug Estrutura",
            icon=ft.Icons.BUG_REPORT,
            on_click=self._debug_estrutura,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_600
            )
        )
        
        # Botão de teste manual
        self.btn_teste_manual = ft.ElevatedButton(
            "Teste Manual",
            icon=ft.Icons.SEARCH,
            on_click=self._teste_manual,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.PURPLE_600
            )
        )
        
        #  Botão para dashboard analytics
        self.btn_dashboard = ft.ElevatedButton(
            "Abrir Dashboard",
            icon=ft.Icons.DASHBOARD,
            on_click=self._abrir_dashboard,
            disabled=True,  # Inicialmente desabilitado
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.DEEP_PURPLE_600
            )
        )
        
        # Indicador de progresso
        self.progress_ring = ft.ProgressRing(
            visible=False,
            width=20,
            height=20,
            stroke_width=2
        )
        
        # Texto de estatísticas
        self.estatisticas_text = ft.Text(
            "Clique em 'Processar Grafos' para gerar a visualização",
            size=14,
            color=ft.Colors.GREY_600
        )
        
        # Container para WebView
        self.webview_container = ft.Container(
            content=ft.Column([
                ft.Text("Visualização do Grafo", 
                       size=16, 
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.BLUE_700),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.ProgressBar(),
                        ft.Text("Carregando visualização do grafo...", 
                               size=14,
                               text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20
                )
            ]),
            height=600,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=10,
            visible=False
        )
        
        # Mensagem de status
        self.status_text = ft.Text(
            "Pronto para processar",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Cabeçalho
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ACCOUNT_TREE, color=ft.Colors.BLUE_500),
                        title=ft.Text(
                            "Visualização de Grafos",
                            weight=ft.FontWeight.BOLD,
                            size=18
                        ),
                        subtitle=ft.Text(
                            "Transforma análises JSON em grafos interativos - Integrado com Dashboard Analytics",
                            color=ft.Colors.GREY_600
                        )
                    ),
                    ft.Divider(height=1),
                    
                    # Controles
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Controles", 
                                   size=14, 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_700),
                            ft.Row([
                                self.btn_processar,
                                self.btn_abrir_externo,
                                self.btn_dashboard,  #   Botão do dashboard
                                self.btn_debug,
                                self.btn_teste_manual,
                                self.progress_ring
                            ], wrap=True),
                            self.status_text
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    ),
                    
                    ft.Divider(height=1),
                    
                    # Estatísticas rápidas
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Resumo", 
                                   size=14, 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_700),
                            self.estatisticas_text
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    ),
                    
                    ft.Divider(height=1),
                    
                    # Visualização
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Visualização Interativa", 
                                   size=14, 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_700),
                            ft.Text(
                                "O grafo será exibido aqui após o processamento",
                                size=12,
                                color=ft.Colors.GREY_600
                            ),
                            self.webview_container
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    )
                ]),
                padding=0
            ),
            elevation=3,
            margin=ft.margin.symmetric(vertical=5)
        )
    
    def _processar_grafos(self, e):
        """Processa os grafos e gera visualização - VERSÃO ATUALIZADA COM DASHBOARD"""
        # Atualiza UI para estado de processamento
        self._atualizar_ui_processamento(True)
        
        try:
            logger.info("🎯 Iniciando processamento de grafos...")
            
            # Processa grafo
            resultado = self.controller.processar_grafo()
            
            if resultado and resultado.get('grafo'):
                html_path = resultado.get("html_path")
                
                if html_path and os.path.exists(html_path):
                    # Atualiza estatísticas
                    estatisticas = resultado.get("estatisticas", {})
                    self._atualizar_estatisticas_ui(estatisticas, resultado)
                    
                    # Habilita botões
                    self.btn_abrir_externo.disabled = False
                    self.btn_dashboard.disabled = False  #  : Habilita botão do dashboard
                    
                    # Atualiza outros componentes
                    if self.estatisticas_card:
                        self.estatisticas_card.atualizar_estatisticas(estatisticas)
                    if self.comunidades_card:
                        self.comunidades_card.atualizar_comunidades(resultado.get('comunidades', {}))
                    
                    #   Processa análise para o dashboard se disponível (sem processar grafo novamente)
                    if self.dashboard_controller:
                        try:
                            logger.info("📊 Processando análise para dashboard...")
                            # Usa método direto para evitar reprocessamento
                            analise_dashboard = self.dashboard_controller.processar_analise_completa()
                            if analise_dashboard:
                                logger.info("✅ Análise do dashboard processada com sucesso")
                            else:
                                logger.info("ℹ️ Dashboard já tem análise em andamento ou sem dados suficientes")
                        except Exception as dashboard_ex:
                            logger.warning(f"⚠️ Dashboard não pôde processar análise: {dashboard_ex}")
                    
                    # Lê o conteúdo HTML
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Cria WebView para exibir o grafo
                    self._criar_webview(html_content, e.page)
                    
                    self._atualizar_status("✅ Grafo processado com sucesso! Dashboard atualizado.", ft.Colors.GREEN)
                    self.notifier.success("Grafo processado e exibido com sucesso! Dashboard atualizado.")
                    
                else:
                    self._atualizar_status("❌ Arquivo de visualização não foi gerado", ft.Colors.RED)
                    self.notifier.error("Arquivo de visualização não foi gerado")
            else:
                self._atualizar_status("❌ Nenhum grafo foi gerado a partir dos dados", ft.Colors.RED)
                self.notifier.error("Nenhum grafo foi gerado a partir dos dados")
            
        except Exception as ex:
            logger.error(f"💥 Erro ao processar grafos: {str(ex)}")
            self._atualizar_status(f"❌ Erro: {str(ex)}", ft.Colors.RED)
            self.notifier.error(f"Erro ao processar grafos: {str(ex)}")
        finally:
            self._atualizar_ui_processamento(False)
    
    def _atualizar_ui_processamento(self, processando: bool):
        """Atualiza a UI para o estado de processamento"""
        self.btn_processar.disabled = processando
        self.btn_processar.text = "Processando..." if processando else "Processar Grafos"
        self.progress_ring.visible = processando
        self.btn_debug.disabled = processando
        self.btn_teste_manual.disabled = processando
        self.btn_dashboard.disabled = processando or self.btn_dashboard.disabled  #   Mantém estado atual
        
        if self.page:
            self.page.update()
    
    def _atualizar_estatisticas_ui(self, estatisticas: dict, resultado: dict):
        """Atualiza as estatísticas na UI"""
        if estatisticas:
            stats_text = (
                f"📊 Grafo: {estatisticas.get('num_nos', 0)} nós, "
                f"{estatisticas.get('num_arestas', 0)} arestas, "
                f"{estatisticas.get('num_comunidades', 0)} comunidades\n"
                f"⏱️ Processado em {resultado.get('tempo_processamento', 0)}s | "
                f"📁 {resultado.get('arquivos_processados', 0)} arquivos"
            )
            self.estatisticas_text.value = stats_text
            self.estatisticas_text.color = ft.Colors.GREEN_700
            
            #   Adiciona indicador de dashboard se disponível
            if self.dashboard_controller:
                stats_text += f"\n📈 Dashboard: Análise completa disponível"
                self.estatisticas_text.value = stats_text
                
        else:
            self.estatisticas_text.value = "❌ Nenhuma estatística disponível"
            self.estatisticas_text.color = ft.Colors.RED_600
    
    def _atualizar_status(self, mensagem: str, cor: str = ft.Colors.GREY_600):
        """Atualiza a mensagem de status"""
        self.status_text.value = mensagem
        self.status_text.color = cor
        if self.page:
            self.page.update()
    
    def _criar_webview(self, html_content: str, page: ft.Page):
        """Cria WebView para exibir o grafo"""
        try:
            # Para modo web, usa Embedded HTML (iframe via Dart)
            html_url = "http://localhost:8550/grafo_gerado/grafo_visualizacao.html"

            logger.info(f"📄 Tentando carregar via URL: {html_url}")

            # Tenta diferentes abordagens para exibir HTML no Flet
            try:
                # Abordagem 1: Tentar usar ft.Image com SVG (não funciona para HTML)
                # Abordagem 2: Usar Container com borda e indicador
                self.webview = ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.VISIBILITY, color=ft.Colors.BLUE_600),
                                ft.Text("Visualização Interativa do Grafo",
                                       size=16,
                                       weight=ft.FontWeight.BOLD,
                                       color=ft.Colors.BLUE_700)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Text("O grafo foi gerado com sucesso!",
                                   size=14,
                                   color=ft.Colors.GREEN_600),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "🌐 Abrir Grafo em Nova Aba",
                                    icon=ft.Icons.OPEN_IN_NEW,
                                    on_click=self._abrir_externo,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.BLUE_600
                                    )
                                ),
                                ft.ElevatedButton(
                                    "📊 Ver Dashboard",
                                    icon=ft.Icons.DASHBOARD,
                                    on_click=self._abrir_dashboard,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.DEEP_PURPLE_600
                                    )
                                )
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=10),
                            ft.Text(
                                "💡 Dica: Use 'Abrir Grafo em Nova Aba' para visualização interativa completa",
                                size=12,
                                color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            )
                        ]),
                        padding=20,
                        border=ft.border.all(2, ft.Colors.BLUE_200),
                        border_radius=10,
                        bgcolor=ft.Colors.GREY_50
                    )
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

                self.webview_container.content = self.webview
                self.webview_container.visible = True

                logger.info("✅ Interface de visualização criada com sucesso")

            except Exception as inner_ex:
                logger.error(f"💥 Erro na abordagem principal: {str(inner_ex)}")
                self._fallback_visualizacao(html_content, page)

        except Exception as ex:
            logger.error(f"💥 Erro ao criar WebView: {str(ex)}")
            self._fallback_visualizacao(html_content, page)
    
    def _fallback_visualizacao(self, html_content: str, page: ft.Page):
        """Fallback quando WebView não está disponível"""
        self.webview_container.content = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO, size=40, color=ft.Colors.BLUE),
                    ft.Text("Visualização do Grafo",
                           size=16,
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.BLUE_700),
                    ft.Text(
                        "Use uma das opções abaixo para visualizar o grafo interativo",
                        size=14,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=20),
                    ft.Row([
                        ft.ElevatedButton(
                            "Abrir em Nova Aba",
                            icon=ft.Icons.OPEN_IN_NEW,
                            on_click=self._abrir_externo,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.BLUE_600
                            )
                        ),
                        ft.ElevatedButton(
                            "Abrir Dashboard",
                            icon=ft.Icons.DASHBOARD,
                            on_click=self._abrir_dashboard,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.DEEP_PURPLE_600
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    ft.Text(
                        "💡 Dica: O HTML foi gerado em grafo_gerado/grafo_visualizacao.html",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                alignment=ft.alignment.center
            )
        ])
        self.webview_container.visible = True
        
        if page:
            page.update()
    
    def _abrir_externo(self, e=None):
        """Abre a visualização do grafo no navegador externo"""
        try:
            resultado = self.controller.get_resultado_atual()
            html_path = resultado.get('html_path', '')

            if html_path and os.path.exists(html_path):
                # Para modo web, usa URL relativa se disponível
                if hasattr(self, 'page') and self.page:
                    # Tenta abrir via URL do servidor web
                    webbrowser.open(f'http://localhost:8550/grafo_gerado/grafo_visualizacao.html')
                    self._atualizar_status("🌐 Abrindo visualização via servidor web...", ft.Colors.BLUE)
                else:
                    # Fallback para file://
                    abs_path = os.path.abspath(html_path)
                    webbrowser.open(f'file://{abs_path}')
                    self._atualizar_status("🌐 Abrindo visualização no navegador...", ft.Colors.BLUE)
                self.notifier.info("Abrindo visualização do grafo no navegador...")
                
                # Log para debug
                logger.info(f"📂 Arquivo aberto: {abs_path}")
            else:
                self._atualizar_status("❌ Arquivo de visualização não encontrado", ft.Colors.RED)
                self.notifier.error("Arquivo de visualização não encontrado")
                
                # Tenta gerar novamente
                if not html_path:
                    self.notifier.info("Tentando gerar visualização novamente...")
                    self._processar_grafos(e)
                    
        except Exception as ex:
            logger.error(f"💥 Erro ao abrir visualização externa: {str(ex)}")
            self._atualizar_status(f"❌ Erro ao abrir: {str(ex)}", ft.Colors.RED)
            self.notifier.error(f"Erro ao abrir no navegador: {str(ex)}")
    
    def _abrir_dashboard(self, e=None):  #   Método para abrir dashboard
        """Navega para a aba do Dashboard Analytics"""
        try:
            if self.page:
                # Encontra a aba do dashboard (índice 3)
                tabs = self.page.controls[0]  # Assume que o primeiro controle são as abas
                if hasattr(tabs, 'tabs') and len(tabs.tabs) > 3:
                    tabs.selected_index = 3
                    self.page.update()
                    self._atualizar_status("📊 Navegando para Dashboard Analytics...", ft.Colors.DEEP_PURPLE)
                    self.notifier.info("Abrindo Dashboard Analytics...")
                else:
                    self._atualizar_status("❌ Dashboard não disponível", ft.Colors.RED)
                    self.notifier.error("Aba do Dashboard não encontrada")
        except Exception as ex:
            logger.error(f"💥 Erro ao abrir dashboard: {str(ex)}")
            self._atualizar_status(f"❌ Erro ao abrir dashboard: {str(ex)}", ft.Colors.RED)
            self.notifier.error(f"Erro ao abrir dashboard: {str(ex)}")
    
    def _debug_estrutura(self, e):
        """Executa debug da estrutura de pastas"""
        try:
            self._atualizar_status("🔍 Executando debug...", ft.Colors.BLUE)
            self.controller.debug_estrutura_pastas()
            self._atualizar_status("✅ Debug executado - verifique os logs", ft.Colors.GREEN)
            self.notifier.info("Debug executado - verifique os logs do terminal")
        except Exception as ex:
            logger.error(f"💥 Erro no debug: {ex}")
            self._atualizar_status(f"❌ Erro no debug: {str(ex)}", ft.Colors.RED)
            self.notifier.error(f"Erro no debug: {str(ex)}")
    
    def _teste_manual(self, e):
        """Executa teste manual dos arquivos"""
        try:
            self._atualizar_status("🧪 Executando teste manual...", ft.Colors.BLUE)
            arquivos_validos = self.controller.testar_arquivos_manualmente()
            
            if arquivos_validos:
                self._atualizar_status(f"✅ Teste: {len(arquivos_validos)} arquivos válidos", ft.Colors.GREEN)
                self.notifier.success(f"Teste manual: {len(arquivos_validos)} arquivos válidos encontrados")
            else:
                self._atualizar_status("❌ Teste: Nenhum arquivo válido", ft.Colors.RED)
                self.notifier.warning("Teste manual: Nenhum arquivo válido encontrado")
                
        except Exception as ex:
            logger.error(f"💥 Erro no teste manual: {ex}")
            self._atualizar_status(f"❌ Erro no teste: {str(ex)}", ft.Colors.RED)
            self.notifier.error(f"Erro no teste manual: {str(ex)}")
    
    def limpar_visualizacao(self):
        """Limpa a visualização atual"""
        self.webview_container.visible = False
        self.btn_abrir_externo.disabled = True
        self.btn_dashboard.disabled = True  #   Desabilita botão do dashboard também
        self.estatisticas_text.value = "Clique em 'Processar Grafos' para gerar a visualização"
        self.estatisticas_text.color = ft.Colors.GREY_600
        self._atualizar_status("Pronto para processar", ft.Colors.GREY_600)
        
        if self.estatisticas_card:
            self.estatisticas_card.atualizar_estatisticas({})
        if self.comunidades_card:
            self.comunidades_card.atualizar_comunidades({})
        
        if self.page:
            self.page.update()
    
    def atualizar_componentes(self):
        """Atualiza todos os componentes com os dados atuais"""
        resultado = self.controller.get_resultado_atual()
        if resultado:
            estatisticas = resultado.get('estatisticas', {})
            comunidades = resultado.get('comunidades', {})
            html_path = resultado.get('html_path', '')
            
            # Atualiza estatísticas
            self._atualizar_estatisticas_ui(estatisticas, resultado)
            
            # Habilita botões se há visualização
            self.btn_abrir_externo.disabled = not (html_path and os.path.exists(html_path))
            self.btn_dashboard.disabled = not resultado  #   Habilita se há resultado
            
            # Atualiza componentes relacionados
            if self.estatisticas_card:
                self.estatisticas_card.atualizar_estatisticas(estatisticas)
            if self.comunidades_card:
                self.comunidades_card.atualizar_comunidades(comunidades)
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações da UI"""
        self.page = page