import flet as ft
import logging
import json
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LogViews:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None

        # Inicializa controles básicos
        self._inicializar_controles()

    def _inicializar_controles(self):
        """Inicializa controles básicos"""
        self.log_output = ft.TextField(
            multiline=True,
            read_only=True,
            min_lines=10,
            max_lines=20,
            label="Log em Tempo Real",
            hint_text="Os logs aparecerão aqui...",
            filled=True,
            border_color=ft.Colors.GREY_300
        )

        # ✅ NOVO: Área de exibição de tempos
        self.tempos_output = ft.TextField(
            multiline=True,
            read_only=True,
            min_lines=8,
            max_lines=15,
            label="⏱️ Tempos de Análise",
            hint_text="Clique em '📊 Carregar Tempos' para ver os tempos...",
            filled=True,
            border_color=ft.Colors.BLUE_300,
            text_size=11
        )

    def set_page(self, page: ft.Page):
        """Define a página do componente"""
        self.page = page

    def build(self) -> ft.Card:
        """Constrói o card - versão super simplificada"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.BLUE_500),
                        title=ft.Text(
                            "Logs e Visualizações",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        subtitle=ft.Text("Card de logs funcional")
                    ),
                    ft.Divider(height=1),

                    # Seção de logs
                    ft.Text(
                        "📝 Logs do Sistema",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.log_output,

                    # Seção de tempos
                    ft.Text(
                        "⏱️ Tempos de Análise",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.tempos_output,

                    # Botões de ação
                    ft.Row([
                        ft.ElevatedButton(
                            "Limpar Logs",
                            icon=ft.Icons.CLEAR,
                            on_click=self._limpar_log,
                            bgcolor=ft.Colors.RED_600,
                            color=ft.Colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Exportar Logs",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=self._exportar_log,
                            bgcolor=ft.Colors.BLUE_600,
                            color=ft.Colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "📊 Carregar Tempos",
                            icon=ft.Icons.TIMER,
                            on_click=self._carregar_tempos,
                            bgcolor=ft.Colors.GREEN_600,
                            color=ft.Colors.WHITE
                        )
                    ], spacing=10)
                ]),
                padding=15
            ),
            elevation=3
        )

    # Métodos funcionais básicos
    def _limpar_log(self, e):
        """Limpa o log"""
        try:
            self.log_output.value = ""
            if self.page:
                self.page.update()
            self.adicionar_log("✅ Log limpo", "SUCCESS")
        except Exception as ex:
            logger.error(f"Erro ao limpar log: {ex}")

    def _exportar_log(self, e):
        """Exporta o log para arquivo"""
        try:
            if not self.log_output.value.strip():
                self.notifier.warning("Nenhum conteúdo para exportar")
                return

            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"log_analise_{timestamp}.txt"

            os.makedirs("storage/export", exist_ok=True)
            filepath = os.path.join("storage/export", filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write(f"LOG DE ANÁLISE - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(self.log_output.value)

            self.notifier.success(f"Log exportado: {filename}")
            self.adicionar_log(f"📁 Log exportado: {filename}", "SUCCESS")
        except Exception as ex:
            logger.error(f"Erro ao exportar log: {ex}")
            self.notifier.error(f"Erro ao exportar: {str(ex)}")

    def _carregar_tempos(self, e):
        """Carrega tempos de análise diretamente no campo de texto"""
        try:
            self.adicionar_log("🔄 Carregando tempos de análise...", "INFO")

            # Obtém resultados do controller - método robusto
            resultados = []

            # Tenta método direto primeiro
            try:
                resultados = self.controller.obter_resultados_analise()
                self.adicionar_log(f"📋 Via método direto: {len(resultados)} resultados", "INFO")
            except Exception as e:
                self.adicionar_log(f"⚠️ Erro método direto: {e}", "WARNING")

            # Se não funcionou, tenta via status
            if not resultados:
                try:
                    status = self.controller.get_status_analise()
                    self.adicionar_log(f"🔍 Chaves no status: {list(status.keys())}", "INFO")

                    # Tenta diferentes chaves
                    for chave in ['resultado', 'resultados', 'results', 'analysis_results']:
                        if chave in status and status[chave]:
                            resultados = status[chave]
                            self.adicionar_log(f"✅ Encontrados na chave '{chave}': {len(resultados)} itens", "SUCCESS")
                            break
                except Exception as e:
                    self.adicionar_log(f"❌ Erro via status: {e}", "ERROR")

            if not resultados:
                self.tempos_output.value = "⚠️ Nenhuma análise encontrada.\nExecute uma análise primeiro."
                if self.page:
                    self.page.update()
                self.adicionar_log("❌ Nenhuma análise encontrada", "WARNING")
                return

            # Prepara texto dos tempos
            tempos_texto = f"📊 TEMPOS DE ANÁLISE ({len(resultados)} arquivos)\n"
            tempos_texto += "=" * 50 + "\n\n"

            tempos_llm = []
            total_nodes = 0
            total_edges = 0

            for resultado in resultados:
                arquivo = resultado.get('arquivo', 'N/A')
                tempo_llm = resultado.get('tempo_llm', 0)
                stats = resultado.get('estatisticas', {})
                nodes = stats.get('nodes_count', 0)
                edges = stats.get('edges_count', 0)
                status_result = resultado.get('status', 'unknown')

                # Ícone baseado no tempo
                if tempo_llm > 0:
                    cor_icon = "🟢" if tempo_llm < 10 else ("🟡" if tempo_llm < 30 else "🔴")
                    tempo_str = f"{tempo_llm:.1f}s"
                    tempos_llm.append(tempo_llm)
                else:
                    cor_icon = "⚪"
                    tempo_str = "sem tempo"

                total_nodes += nodes
                total_edges += edges

                # Formatação legível
                tempos_texto += f"{cor_icon} {os.path.basename(arquivo):<25} "
                tempos_texto += f"{tempo_str:>8} "
                tempos_texto += f"({nodes:>3} nodes, {edges:>3} edges) [{status_result}]\n"

            # Estatísticas
            tempos_texto += "\n" + "=" * 50 + "\n"
            tempos_texto += "📈 ESTATÍSTICAS GERAIS:\n\n"
            tempos_texto += f"🔢 Total de arquivos: {len(resultados)}\n"
            tempos_texto += f"🔗 Total de nodes: {total_nodes}\n"
            tempos_texto += f"🔗 Total de edges: {total_edges}\n"
            tempos_texto += f"📊 Média nodes/arquivo: {total_nodes/len(resultados):.1f}\n"

            if tempos_llm:
                tempos_texto += f"\n⏱️ TEMPOS LLM:\n"
                tempos_texto += f"   • Total: {sum(tempos_llm):.1f}s\n"
                tempos_texto += f"   • Médio: {sum(tempos_llm)/len(tempos_llm):.1f}s\n"
                tempos_texto += f"   • Mais rápido: {min(tempos_llm):.1f}s\n"
                tempos_texto += f"   • Mais lento: {max(tempos_llm):.1f}s\n"
            else:
                tempos_texto += f"\n⚠️ Nenhum tempo LLM registrado.\n"

            # Adiciona timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            tempos_texto += f"\n🕐 Gerado em: {timestamp}\n"

            # Atualiza o campo de tempos
            self.tempos_output.value = tempos_texto
            if self.page:
                self.page.update()

            self.adicionar_log(f"✅ Tempos carregados: {len(resultados)} arquivos, {len(tempos_llm)} com tempos LLM", "SUCCESS")

            # Notificação resumida
            if tempos_llm:
                resumo = f"⏱️ {len(tempos_llm)} tempos LLM carregados (total: {sum(tempos_llm):.1f}s)"
            else:
                resumo = f"📊 {len(resultados)} arquivos analisados (sem tempos LLM)"

            self.notifier.success(resumo)

        except Exception as ex:
            logger.error(f"Erro ao carregar tempos: {ex}")
            self.adicionar_log(f"❌ Erro ao carregar tempos: {str(ex)}", "ERROR")
            self.notifier.error(f"Erro: {str(ex)}")

            # Mostra erro no campo
            self.tempos_output.value = f"❌ Erro ao carregar tempos:\n{str(ex)}"
            if self.page:
                self.page.update()

    def adicionar_log(self, mensagem: str, nivel: str = "INFO"):
        """Adiciona mensagem ao log"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            # Ícone baseado no nível
            icon_map = {
                "INFO": "📝",
                "ERROR": "❌",
                "WARNING": "⚠️",
                "SUCCESS": "✅"
            }
            icon = icon_map.get(nivel, "📝")

            # Adiciona ao log_output
            if self.log_output.value:
                self.log_output.value += f"\n[{timestamp}] {icon} {mensagem}"
            else:
                self.log_output.value = f"[{timestamp}] {icon} {mensagem}"

            # Atualiza UI
            if self.page:
                self.page.update()
        except Exception as e:
            logger.error(f"Erro ao adicionar log: {e}")

    def cleanup(self):
        """Limpa recursos"""
        try:
            logger.info("LogViews cleanup realizado")
        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")

    def __del__(self):
        """Destrutor"""
        try:
            self.cleanup()
        except:
            pass