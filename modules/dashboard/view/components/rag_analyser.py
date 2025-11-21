import flet as ft
import logging
import time
import threading
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RagAnalyserCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.analises_historico = []
        self.estatisticas_contexto = ""
        self.analise_thread = None
        self.analise_em_andamento = False
        self.page = None
        
    def build(self) -> ft.Card:
        """Constrói o card completo do RAG Analyser"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    self._build_header(),
                    ft.Divider(),
                    self._build_stats_section(),
                    ft.Divider(),
                    self._build_quick_question_section(),
                    ft.Divider(),
                    self._build_full_prompt_section(),
                    self._build_analysis_controls(),
                    self._build_result_section(),
                    ft.Divider(),
                    self._build_history_section()
                ], scroll=ft.ScrollMode.ADAPTIVE),
                padding=20
            ),
            width=900,
            margin=10
        )
    
    def _build_header(self) -> ft.Container:
        """Cabeçalho do card"""
        return ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.DEEP_PURPLE_500, size=32),
                title=ft.Text("Analisador RAG com IA", 
                             size=20, 
                             weight=ft.FontWeight.BOLD,
                             color=ft.Colors.DEEP_PURPLE_700),
                subtitle=ft.Text("Faça perguntas sobre a arquitetura usando o contexto das métricas",
                               color=ft.Colors.GREY_600),
                trailing=ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_color=ft.Colors.BLUE_500,
                    tooltip="Este analisador combina métricas da arquitetura com IA para fornecer insights contextualizados",
                    on_click=self._show_info
                )
            )
        )
    
    def _build_stats_section(self) -> ft.Container:
        """Seção de estatísticas e contexto"""
        # Botão para carregar estatísticas
        self.btn_carregar_stats = ft.ElevatedButton(
            "📊 Carregar Estatísticas",
            icon=ft.Icons.DATA_USAGE,
            on_click=self._carregar_estatisticas,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            )
        )
        
        # Status das estatísticas
        self.stats_status = ft.Text(
            "Estatísticas não carregadas",
            size=12,
            color=ft.Colors.ORANGE_600,
            italic=True
        )
        
        # Indicador de métricas disponíveis
        self.metrics_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.ORANGE),
                ft.Text("0 métricas", size=10)
            ]),
            visible=False
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Contexto das Métricas", 
                           size=16, 
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.BLUE_700),
                    self.metrics_indicator
                ]),
                ft.Text("Carregue as métricas da análise atual para usar como contexto na análise com IA",
                       size=12,
                       color=ft.Colors.GREY_600),
                ft.Container(height=5),
                ft.Row([
                    self.btn_carregar_stats,
                    self.stats_status,
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color=ft.Colors.BLUE_500,
                        tooltip="Recarregar contexto",
                        on_click=self._recarregar_contexto
                    )
                ])
            ]),
            padding=10
        )
    
    def _build_quick_question_section(self) -> ft.Container:
        """Seção de pergunta rápida"""
        self.prompt_simples_field = ft.TextField(
            label="Digite sua pergunta sobre a arquitetura",
            multiline=True,
            min_lines=2,
            max_lines=4,
            hint_text="Ex: Analise o acoplamento do sistema e sugira melhorias...\nEx: Quais são os pontos críticos da arquitetura?\nEx: Como melhorar a modularidade?",
            expand=True,
            on_change=self._atualizar_prompt_completo,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Pergunta Rápida", 
                       size=16, 
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.GREEN_700),
                ft.Text("Digite sua pergunta abaixo. O contexto das métricas será automaticamente incluído:",
                       size=12,
                       color=ft.Colors.GREY_600),
                ft.Container(height=5),
                self.prompt_simples_field
            ]),
            padding=10
        )
    
    def _build_full_prompt_section(self) -> ft.Container:
        """Seção de prompt completo"""
        self.prompt_completo_field = ft.TextField(
            label="Prompt Completo (Editável)",
            multiline=True,
            min_lines=8,
            max_lines=15,
            hint_text="Aqui você pode ver e editar o prompt completo que será enviado para a IA...",
            expand=True,
            border_color=ft.Colors.PURPLE_300,
            focused_border_color=ft.Colors.PURPLE_500
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Prompt Completo", 
                           size=16, 
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.PURPLE_700),
                    ft.IconButton(
                        icon=ft.Icons.INFO_OUTLINE,
                        icon_size=16,
                        icon_color=ft.Colors.PURPLE_500,
                        tooltip="""Este é o prompt completo que será enviado para a IA. 
Inclui o contexto das métricas + sua pergunta.
Você pode editá-lo livremente para refinar a análise.""",
                    )
                ]),
                ft.Text("Contexto + Sua pergunta (editável):",
                       size=12,
                       color=ft.Colors.GREY_600),
                ft.Container(height=5),
                self.prompt_completo_field,
                ft.Container(height=5),
                ft.Row([
                    ft.ElevatedButton(
                        "🧹 Limpar",
                        icon=ft.Icons.CLEAR,
                        on_click=self._limpar_prompt,
                        style=ft.ButtonStyle(
                            color=ft.Colors.GREY_700,
                            bgcolor=ft.Colors.GREY_200
                        )
                    ),
                    ft.ElevatedButton(
                        "📝 Exemplo",
                        icon=ft.Icons.LIGHTBULB,
                        on_click=self._carregar_exemplo,
                        style=ft.ButtonStyle(
                            color=ft.Colors.ORANGE_700,
                            bgcolor=ft.Colors.ORANGE_100
                        )
                    )
                ])
            ]),
            padding=10
        )
    
    def _build_analysis_controls(self) -> ft.Container:
        """Controles de análise"""
        # Botão de análise
        self.btn_analisar = ft.ElevatedButton(
            "🤖 Gerar Análise com IA",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self._gerar_analise,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.DEEP_PURPLE_600,
                padding=ft.padding.symmetric(horizontal=25, vertical=15)
            )
        )
        
        # Barra de progresso
        self.progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.GREY_300,
            height=8
        )
        
        # Status do progresso
        self.progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.BLUE_600,
            visible=False
        )
        
        # Status da conexão Ollama
        self.ollama_status = ft.Text(
            "🔴 Ollama não verificado",
            size=11,
            color=ft.Colors.RED_600
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    self.btn_analisar,
                    ft.VerticalDivider(width=20),
                    ft.Column([
                        self.progress_bar,
                        self.progress_text
                    ], expand=True)
                ]),
                ft.Container(height=5),
                ft.Row([
                    self.ollama_status,
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Testar Conexão Ollama",
                        icon=ft.Icons.WIFI,
                        on_click=self._testar_conexao_ollama
                    )
                ])
            ]),
            padding=10
        )
    
    def _build_result_section(self) -> ft.Container:
        """Seção de resultados"""
        self.resultado_area = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            visible=False,
            spacing=10
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Resultado da Análise", 
                           size=16, 
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.GREEN_700),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.EXPAND_MORE,
                        icon_color=ft.Colors.GREEN_500,
                        tooltip="Expandir/Recolher",
                        on_click=self._toggle_resultado
                    )
                ]),
                ft.Container(
                    content=self.resultado_area,
                    padding=15,
                    height=400,
                    border=ft.border.all(2, ft.Colors.GREEN_200),
                    border_radius=10,
                    bgcolor=ft.Colors.GREEN_50
                )
            ]),
            padding=10
        )
    
    def _build_history_section(self) -> ft.Container:
        """Seção de histórico"""
        self.historico_list = ft.ListView(
            spacing=5,
            padding=10,
            height=200
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📚 Histórico de Análises", 
                           size=16, 
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.BROWN_700),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Atualizar",
                        icon=ft.Icons.REFRESH,
                        on_click=self._carregar_historico,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BROWN_500
                        )
                    )
                ]),
                ft.Container(
                    content=self.historico_list,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8
                )
            ]),
            padding=10
        )
    
    def _carregar_estatisticas(self, e):
        """Carrega as estatísticas atuais para usar como contexto"""
        try:
            # ✅ CORREÇÃO: Obter análise atual do controller
            analise_atual = self.controller.get_analise_atual()
            
            if not analise_atual:
                self.notifier.warning("Nenhuma análise disponível. Execute a análise completa primeiro!")
                self._reset_stats_ui()
                return
                
            # Desabilita o botão durante o carregamento
            self.btn_carregar_stats.disabled = True
            self.btn_carregar_stats.text = "⏳ Carregando..."
            if self.page:
                self.page.update()

            # Obtém métricas e estatísticas da análise atual
            metricas = analise_atual.get('metricas_avancadas', {})
            estatisticas = analise_atual.get('resultado_grafo', {}).get('estatisticas', {})
            storytelling = analise_atual.get('storytelling', {})

            # Verifica se temos dados suficientes
            if not estatisticas or estatisticas.get('num_nos', 0) == 0:
                self.notifier.warning("Dados de análise insuficientes ou vazios")
                self._reset_stats_ui()
                return

            # Constrói o contexto com as estatísticas
            contexto = self._construir_contexto_estatisticas(metricas, estatisticas, storytelling)
            self.estatisticas_contexto = contexto

            # Atualiza a UI
            self.stats_status.value = f"✅ {estatisticas.get('num_nos', 0)} componentes carregados"
            self.stats_status.color = ft.Colors.GREEN_600

            # Atualiza indicador de métricas
            self.metrics_indicator.visible = True
            self.metrics_indicator.content.controls[1].value = f"{estatisticas.get('num_nos', 0)} componentes"
            self.metrics_indicator.content.controls[0].color = ft.Colors.GREEN

            # Atualiza o prompt completo com o contexto
            self._atualizar_prompt_completo()

            self.notifier.success("Estatísticas carregadas com sucesso!")

        except Exception as ex:
            logger.error(f"Erro ao carregar estatísticas: {ex}")
            self.notifier.error(f"Erro ao carregar estatísticas: {str(ex)}")
            self._reset_stats_ui()
        finally:
            self.btn_carregar_stats.disabled = False
            self.btn_carregar_stats.text = "📊 Carregar Estatísticas"
            if self.page:
                self.page.update()
    
    def _reset_stats_ui(self):
        """Reseta a UI das estatísticas"""
        self.btn_carregar_stats.disabled = False
        self.btn_carregar_stats.text = "📊 Carregar Estatísticas"
        self.stats_status.value = "Estatísticas não carregadas"
        self.stats_status.color = ft.Colors.ORANGE_600
        self.metrics_indicator.visible = False
    
    def _construir_contexto_estatisticas(self, metricas, estatisticas, storytelling) -> str:
        """Constrói o contexto com as estatísticas formatadas"""
        contexto = "CONTEXTO DA ANÁLISE DE ARQUITETURA:\n\n"
        
        # Estatísticas básicas
        contexto += "=== ESTATÍSTICAS GERAIS DO SISTEMA ===\n"
        contexto += f"• Total de componentes (nós): {estatisticas.get('num_nos', 'N/A')}\n"
        contexto += f"• Total de dependências (arestas): {estatisticas.get('num_arestas', 'N/A')}\n"
        contexto += f"• Comunidades detectadas: {estatisticas.get('num_comunidades', 'N/A')}\n"
        contexto += f"• Componentes isolados: {estatisticas.get('nos_isolados', 'N/A')}\n"
        contexto += f"• Densidade do grafo: {estatisticas.get('densidade', 'N/A')}\n"
        contexto += f"• Grau médio (conexões por componente): {estatisticas.get('grau_medio', 'N/A')}\n\n"
        
        # Métricas avançadas
        if hasattr(metricas, 'acoplamento_medio'):
            contexto += "=== MÉTRICAS DE QUALIDADE ARQUITETURAL ===\n"
            contexto += f"• Acoplamento médio: {metricas.acoplamento_medio:.3f} (0-1, menor é melhor)\n"
            contexto += f"• Coesão média: {getattr(metricas, 'coesao_media', 0):.3f} (0-1, maior é melhor)\n"
            contexto += f"• Modularidade: {getattr(metricas, 'modularidade', 0):.3f} (0-1, maior é melhor)\n"
            contexto += f"• Densidade: {getattr(metricas, 'densidade', 0):.3f} (0-1)\n"
            if hasattr(metricas, 'complexidade_ciclomatica_media'):
                contexto += f"• Complexidade ciclomática média: {metricas.complexidade_ciclomatica_media:.1f}\n"
            if hasattr(metricas, 'centralidade_intermediacao_maxima'):
                contexto += f"• Centralidade máxima (intermediação): {metricas.centralidade_intermediacao_maxima:.3f}\n"
            contexto += f"• Componentes conectados: {getattr(metricas, 'numero_componentes', 0)}\n\n"
        
        # Insights do storytelling
        if storytelling:
            contexto += "=== ANÁLISE CONTEXTUAL ===\n"
            contexto += f"Resumo: {storytelling.get('resumo_geral', 'N/A')}\n"
            contexto += f"Insights técnicos: {storytelling.get('insights_tecnicos', 'N/A')}\n"
            contexto += f"Pontos de atenção: {storytelling.get('pontos_atencao', 'N/A')}\n"
            contexto += f"Recomendações: {storytelling.get('recomendacoes', 'N/A')}\n\n"
        
        contexto += "INSTRUÇÃO: Com base nestas métricas, analise a arquitetura do sistema considerando:\n"
        contexto += "1. Qualidade arquitetural (acoplamento, coesão, modularidade)\n"
        contexto += "2. Complexidade e manutenibilidade\n"
        contexto += "3. Pontos críticos e gargalos\n"
        contexto += "4. Recomendações de melhoria específicas\n"
        contexto += "5. Padrões arquiteturais aplicáveis\n\n"
        
        contexto += "PERGUNTA DO USUÁRIO:\n"
        
        return contexto
    
    def _atualizar_prompt_completo(self, e=None):
        """Atualiza o prompt completo combinando contexto e pergunta do usuário"""
        pergunta_usuario = self.prompt_simples_field.value.strip()
        
        if not self.estatisticas_contexto:
            # Se não há estatísticas carregadas, mostra apenas a pergunta
            self.prompt_completo_field.value = pergunta_usuario
        else:
            # Combina contexto + pergunta do usuário
            prompt_completo = f"{self.estatisticas_contexto}{pergunta_usuario}\n\nRESPOSTA:"
            self.prompt_completo_field.value = prompt_completo
        
        if self.page:
            self.page.update()
    
    def _gerar_analise(self, e):
        """Gera análise baseada no prompt completo"""
        if not self.estatisticas_contexto:
            self.notifier.warning("Carregue as estatísticas primeiro!")
            return
            
        prompt_completo = self.prompt_completo_field.value.strip()
        
        if not prompt_completo:
            self.notifier.warning("O prompt completo está vazio!")
            return
        
        # Valida o prompt (se o método existir no controller)
        if hasattr(self.controller, 'validar_prompt_rag'):
            validacao = self.controller.validar_prompt_rag(prompt_completo)
            if not validacao['valido']:
                self.notifier.error(validacao['erro'])
                return
        
        # Verifica se já há uma análise em andamento
        if self.analise_em_andamento:
            self.notifier.warning("Já existe uma análise em andamento!")
            return
        
        # Inicia a análise
        self._iniciar_analise()
        
        # Executa em thread separada para não travar a UI
        self.analise_thread = threading.Thread(
            target=self._executar_analise_llm,
            args=(prompt_completo,),
            daemon=True
        )
        self.analise_thread.start()
    
    def _executar_analise_llm(self, prompt_completo: str):
        """Executa a análise LLM em uma thread separada"""
        try:
            # ✅ CORREÇÃO: Use page.update() em vez de page.run_task() para funções síncronas
            self._atualizar_progresso_sincrono(0.1, "🔍 Conectando com o servidor LLM...")
            time.sleep(0.5)
            
            self._atualizar_progresso_sincrono(0.3, "⚙️ Processando prompt e contexto...")
            time.sleep(0.7)
            
            self._atualizar_progresso_sincrono(0.5, "🤖 Gerando análise com IA...")
            
            # Chama o controller para gerar a análise
            resultado = self.controller.gerar_analise_personalizada(prompt_completo)
            
            self._atualizar_progresso_sincrono(0.8, "📥 Recebendo resposta...")
            time.sleep(0.5)
            
            if resultado and resultado.get("sucesso"):
                self._atualizar_progresso_sincrono(1.0, "✅ Análise concluída!")
                time.sleep(0.5)
                
                # Exibe o resultado na UI
                self._exibir_resultado_sincrono(
                    resultado["analise"], 
                    prompt_completo, 
                    resultado.get("modelo")
                )
                self._carregar_historico_sincrono()
                self._finalizar_analise_sincrono()
            else:
                erro_msg = resultado.get('erro', 'Erro desconhecido') if resultado else 'Nenhum resultado retornado'
                self._exibir_erro_sincrono(f"Erro na análise: {erro_msg}")
                self._finalizar_analise_sincrono()
                
        except Exception as ex:
            logger.error(f"Erro ao executar análise LLM: {ex}")
            self._exibir_erro_sincrono(f"Erro: {str(ex)}")
            self._finalizar_analise_sincrono()
    
    #  Métodos síncronos para atualização da UI a partir de threads
    def _atualizar_progresso_sincrono(self, valor: float, mensagem: str):
        """Atualiza a barra de progresso de forma síncrona"""
        if self.page:
            #  Atualiza os controles do próprio componente, não da página
            self.progress_bar.value = valor
            self.progress_text.value = mensagem
            self.progress_bar.visible = True
            self.progress_text.visible = True
            self.page.update()
    
    def _exibir_resultado_sincrono(self, analise: str, prompt: str, modelo: str = None):
        """Exibe o resultado de forma síncrona"""
        if self.page:
            self._exibir_resultado(analise, prompt, modelo)
    
    def _exibir_erro_sincrono(self, mensagem: str):
        """Exibe erro de forma síncrona"""
        if self.page:
            self.notifier.error(mensagem)
    
    def _finalizar_analise_sincrono(self):
        """Finaliza a análise de forma síncrona"""
        if self.page:
            self._finalizar_analise()
    
    def _carregar_historico_sincrono(self):
        """Carrega histórico de forma síncrona"""
        if self.page:
            self._carregar_historico()
    
    def _iniciar_analise(self):
        """Prepara a UI para início da análise"""
        self.analise_em_andamento = True
        self.btn_analisar.disabled = True
        self.btn_carregar_stats.disabled = True
        self.btn_analisar.text = "⏳ Analisando..."
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.resultado_area.visible = False
        
        # Limpa resultado anterior
        self.resultado_area.controls.clear()
        
        if self.page:
            self.page.update()
    
    def _finalizar_analise(self):
        """Finaliza a análise e restaura a UI"""
        self.analise_em_andamento = False
        self.btn_analisar.disabled = False
        self.btn_carregar_stats.disabled = False
        self.btn_analisar.text = "🤖 Gerar Análise com IA"
        self.progress_bar.visible = False
        self.progress_text.visible = False
        
        if self.page:
            self.page.update()
    
    def _exibir_resultado(self, analise: str, prompt: str, modelo: str = None):
        """Exibe o resultado da análise"""
        self.resultado_area.controls.clear()
        
        # Cabeçalho do resultado
        header_controls = [
            ft.Row([
                ft.Icon(ft.Icons.INSIGHTS, color=ft.Colors.GREEN_500, size=24),
                ft.Text("Análise Gerada com IA", 
                       size=18, 
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.GREEN_700)
            ])
        ]
        
        # Informações do modelo (se disponível)
        if modelo:
            header_controls.append(
                ft.Text(f"Modelo: {modelo}", 
                       size=12, 
                       color=ft.Colors.GREY_600,
                       italic=True)
            )
        
        header_controls.extend([
            ft.Divider(),
            ft.Text("Contexto utilizado:", size=12, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(
                    self._resumir_contexto(prompt),
                    size=11, 
                    color=ft.Colors.GREY_600,
                    selectable=True
                ),
                padding=10,
                bgcolor=ft.Colors.GREY_100,
                border_radius=5
            ),
            ft.Divider()
        ])
        
        # Área de análise
        analysis_controls = [
            ft.Markdown(
                analise,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme="atom-one-dark",
                on_tap_link=lambda e: print(f"Link clicado: {e.data}")
            )
        ]
        
        # Botões de ação
        action_controls = [
            ft.Row([
                ft.ElevatedButton(
                    "📋 Copiar Análise",
                    icon=ft.Icons.CONTENT_COPY,
                    on_click=lambda _: self._copiar_analise(analise),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    )
                ),
                ft.ElevatedButton(
                    "💾 Salvar", 
                    icon=ft.Icons.SAVE,
                    on_click=lambda _: self._salvar_analise(analise, prompt, modelo),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600
                    )
                ),
                ft.ElevatedButton(
                    "🔄 Nova Análise", 
                    icon=ft.Icons.CLEAR,
                    on_click=self._limpar_resultado,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_600
                    )
                )
            ])
        ]
        
        self.resultado_area.controls.extend(header_controls + analysis_controls + action_controls)
        self.resultado_area.visible = True
        
        if self.page:
            self.page.update()
    
    def _resumir_contexto(self, prompt: str) -> str:
        """Resume o contexto para exibição"""
        linhas = prompt.split('\n')
        if len(linhas) <= 10:
            return prompt
        
        # Mostra primeiras 5 linhas e últimas 2 linhas
        primeiras = '\n'.join(linhas[:5])
        ultimas = '\n'.join(linhas[-2:])
        return f"{primeiras}\n...\n{ultimas}"
    
    def _copiar_analise(self, analise: str):
        """Copia a análise para a área de transferência"""
        try:
            if self.page:
                self.page.set_clipboard(analise)
                self.notifier.success("Análise copiada para a área de transferência!")
        except Exception as ex:
            logger.error(f"Erro ao copiar análise: {ex}")
            self.notifier.error("Erro ao copiar análise")
    
    def _salvar_analise(self, analise: str, prompt: str, modelo: str):
        """Salva a análise em arquivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analise_rag_{timestamp}.txt"
            
            conteudo = f"""ANÁLISE RAG - {timestamp}
Modelo: {modelo or 'N/A'}

=== PROMPT ORIGINAL ===
{prompt}

=== ANÁLISE GERADA ===
{analise}

=== METADADAS ===
Gerado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            # Em uma implementação real, isso salvaria em arquivo
            # Por enquanto, apenas copia para clipboard
            self.page.set_clipboard(conteudo)
            self.notifier.success("Conteúdo preparado para salvar (copiado para clipboard)")
            
        except Exception as ex:
            logger.error(f"Erro ao salvar análise: {ex}")
            self.notifier.error("Erro ao salvar análise")
    
    def _limpar_resultado(self, e=None):
        """Limpa o resultado atual"""
        self.resultado_area.visible = False
        self.prompt_simples_field.value = ""
        self.prompt_completo_field.value = ""
        if self.page:
            self.page.update()
    
    def _limpar_prompt(self, e):
        """Limpa os campos de prompt"""
        self.prompt_simples_field.value = ""
        self.prompt_completo_field.value = ""
        if self.page:
            self.page.update()
    
    def _carregar_exemplo(self, e):
        """Carrega um exemplo de prompt"""
        exemplo = """Com base nas métricas fornecidas, analise a qualidade geral da arquitetura e identifique:

1. Os 3 principais pontos fortes
2. Os 3 principais problemas 
3. Sugestões específicas de refatoração
4. Recomendações para melhorar a manutenibilidade

Forneça a análise em formato de relatório técnico."""
        
        self.prompt_simples_field.value = exemplo
        self._atualizar_prompt_completo()
        self.notifier.info("Exemplo de prompt carregado!")
    
    def _carregar_historico(self, e=None):
        """Carrega o histórico de análises"""
        try:
            if hasattr(self.controller, 'obter_historico_analises'):
                self.analises_historico = self.controller.obter_historico_analises()
            else:
                self.analises_historico = []
                
            self.historico_list.controls.clear()
            
            if not self.analises_historico:
                self.historico_list.controls.append(
                    ft.ListTile(
                        title=ft.Text("Nenhuma análise no histórico"),
                        subtitle=ft.Text("As análises geradas aparecerão aqui"),
                        leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.GREY_400),
                    )
                )
            else:
                for analise in self.analises_historico[:8]:  # Mostra até 8 análises
                    prompt_resumo = analise.get('prompt', '')[:60] + "..." if len(analise.get('prompt', '')) > 60 else analise.get('prompt', '')
                    timestamp = analise.get('timestamp', '')[:16] if analise.get('timestamp') else ''
                    
                    self.historico_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(prompt_resumo, size=12),
                            subtitle=ft.Text(f"{timestamp} | {analise.get('modelo_utilizado', 'N/A')}", 
                                           size=10,
                                           color=ft.Colors.GREY_600),
                            leading=ft.Icon(ft.Icons.AUTO_AWESOME_MOSAIC, color=ft.Colors.BLUE_400),
                            on_click=lambda e, a=analise: self._ver_analise_historico(a),
                            dense=True
                        )
                    )
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao carregar histórico: {ex}")
            self.notifier.error(f"Erro ao carregar histórico: {str(ex)}")
    
    def _carregar_historico_sincrono(self):
        """Versão síncrona para chamada a partir de threads"""
        if self.page:
            self._carregar_historico()
    
    def _ver_analise_historico(self, analise: Dict[str, Any]):
        """Exibe uma análise do histórico"""
        self.prompt_completo_field.value = analise.get('prompt', '')
        self._exibir_resultado(
            analise.get('analise_gerada', ''), 
            analise.get('prompt', ''), 
            analise.get('modelo_utilizado')
        )
        
        # Tenta extrair a pergunta do usuário do prompt completo
        prompt = analise.get('prompt', '')
        if "PERGUNTA DO USUÁRIO:" in prompt:
            partes = prompt.split("PERGUNTA DO USUÁRIO:")
            if len(partes) > 1:
                pergunta = partes[1].split("RESPOSTA:")[0].strip()
                self.prompt_simples_field.value = pergunta
        
        self.notifier.info("Análise do histórico carregada!")
    
    def _testar_conexao_ollama(self, e):
        """Testa a conexão com o Ollama"""
        try:
            self.ollama_status.value = "🟡 Testando conexão..."
            self.ollama_status.color = ft.Colors.ORANGE_600
            if self.page:
                self.page.update()
            
            resultado = self.controller.testar_conexao_ollama()
            
            if resultado['conectado']:
                self.ollama_status.value = f"🟢 Conectado! {resultado['quantidade_modelos']} modelos"
                self.ollama_status.color = ft.Colors.GREEN_600
                self.notifier.success(f"Conexão Ollama OK! {resultado['quantidade_modelos']} modelos disponíveis")
            else:
                self.ollama_status.value = "🔴 Falha na conexão"
                self.ollama_status.color = ft.Colors.RED_600
                self.notifier.error("Falha na conexão com Ollama")
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao testar conexão Ollama: {ex}")
            self.ollama_status.value = "🔴 Erro no teste"
            self.ollama_status.color = ft.Colors.RED_600
            if self.page:
                self.page.update()
    
    def _recarregar_contexto(self, e):
        """Recarrega o contexto atual"""
        if self.controller.get_analise_atual():
            self._carregar_estatisticas(e)
        else:
            self.notifier.warning("Nenhuma análise disponível para recarregar")
    
    def _toggle_resultado(self, e):
        """Alterna a visibilidade da área de resultado"""
        self.resultado_area.visible = not self.resultado_area.visible
        e.control.icon = ft.Icons.EXPAND_LESS if self.resultado_area.visible else ft.Icons.EXPAND_MORE
        if self.page:
            self.page.update()
    
    def _show_info(self, e):
        """Mostra informações sobre o RAG Analyser"""
        info_text = """
🤖 **RAG Analyser**

Este componente combina Retrieval-Augmented Generation (RAG) com análise de arquitetura:

**Como funciona:**
1. Carrega métricas da análise arquitetural
2. Combina com sua pergunta em um prompt contextualizado  
3. Envia para um modelo de LLM (Ollama)
4. Retorna análise específica baseada no contexto

**Contexto incluído:**
• Estatísticas do sistema (componentes, dependências)
• Métricas de qualidade (acoplamento, coesão, modularidade)
• Análise contextual e pontos de atenção

**Use para:**
• Análises técnicas detalhadas
• Sugestões de refatoração
• Identificação de problemas
• Recomendações de melhorias
"""
        self.notifier.info(info_text)
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page
        # Carrega histórico inicial
        self._carregar_historico()
        # Testa conexão Ollama inicial
        self._testar_conexao_ollama(None)