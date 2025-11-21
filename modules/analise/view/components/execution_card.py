import flet as ft
import logging
import os
import time

logger = logging.getLogger(__name__)

class ExecutionCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        self.tarefa_ativa = None

        # 🔥 NOVO: Referência para container do botão de retry
        self.btn_retry_container = None

        # Inicializa os controles no __init__
        self._inicializar_controles()
    
    def _inicializar_controles(self):
        """Inicializa todos os controles da UI"""
        # Botões de controle
        self.btn_iniciar = ft.ElevatedButton(
            "Iniciar Análise",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._iniciar_analise,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            tooltip="Iniciar análise dos arquivos selecionados"
        )

        self.btn_pausar = ft.ElevatedButton(
            "Pausar",
            icon=ft.Icons.PAUSE,
            on_click=self._pausar_analise,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_600,
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            tooltip="Pausar análise em andamento"
        )

        self.btn_retomar = ft.ElevatedButton(
            "Retomar",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._retomar_analise,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            tooltip="Retomar análise pausada"
        )

        self.btn_parar = ft.ElevatedButton(
            "Parar",
            icon=ft.Icons.STOP,
            on_click=self._parar_analise,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_600,
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            ),
            tooltip="Parar análise em andamento"
        )

        # 🔥 NOVO: Botão para forçar retentativa de API
        self.btn_forcar_retry = ft.ElevatedButton(
            "Forçar Retry",
            icon=ft.Icons.REFRESH,
            on_click=self._forcar_retry_api,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.PURPLE_600,
                padding=ft.padding.symmetric(horizontal=15, vertical=12)
            ),
            tooltip="Forçar tentativa imediata de conexão com API"
        )

        # Indicadores de progresso
        self.progress_bar = ft.ProgressBar(
            value=0, 
            width=400,
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.GREY_300
        )
        
        self.progress_text = ft.Text(
            "Pronto para iniciar análise", 
            size=12,
            color=ft.Colors.GREY_700
        )
        
        self.status_text = ft.Text(
            "Status: Ocioso", 
            size=14, 
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_700
        )
        
        self.info_text = ft.Text(
            "Selecione arquivos e configure as opções para iniciar", 
            size=12, 
            color=ft.Colors.GREY_600, 
            text_align=ft.TextAlign.CENTER
        )
        
        # Estatísticas rápidas
        self.stats_text = ft.Text(
            "",
            size=11,
            color=ft.Colors.BLUE_600,
            text_align=ft.TextAlign.CENTER
        )

        # Tempo de análise em tempo real (agora mostra tempo da LLM)
        self.timer_text = ft.Text(
            "Tempo LLM: --s",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_600,
            text_align=ft.TextAlign.CENTER
        )

        # Controle para atualização do timer
        self.timer_running = False
        self.current_llm_time = 0

    def build(self) -> ft.Card:
        """Constrói o card de execução"""
        # 🔥 Cria container do botão de retry separadamente
        self.btn_retry_container = ft.Container(
            content=self.btn_forcar_retry,
            padding=ft.padding.only(top=5),
            visible=False  # Inicialmente invisível
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED_OUTLINED, color=ft.Colors.BLUE_500),
                        title=ft.Text(
                            "Controle de Execução",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        subtitle=ft.Text("Execute, pause ou pare a análise de código")
                    ),
                    ft.Divider(height=1),

                    # Status e progresso
                    ft.Container(
                        content=ft.Column([
                            self.status_text,
                            ft.Container(height=5),
                            self.progress_text,
                            ft.Container(height=10),
                            ft.Row([
                                self.progress_bar,
                                ft.Container(
                                    content=ft.Icon(ft.Icons.AUTO_MODE, color=ft.Colors.BLUE_300),
                                    padding=ft.padding.only(left=10)
                                )
                            ], alignment=ft.MainAxisAlignment.START),
                            ft.Container(height=5),
                            self.timer_text,
                            ft.Container(height=2),
                            self.stats_text,
                            self.info_text
                        ], spacing=0),
                        padding=15
                    ),

                    ft.Divider(height=1),

                    # Botões de controle
                    ft.Container(
                        content=ft.Column([
                            # Primeira linha de botões principais
                            ft.Row([
                                self.btn_iniciar,
                                self.btn_pausar,
                                self.btn_retomar,
                                self.btn_parar,
                                ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                                ft.IconButton(
                                    ft.Icons.INFO_OUTLINE,
                                    tooltip="Informações sobre a análise",
                                    on_click=self._mostrar_info_analise
                                ),
                                ft.IconButton(
                                    ft.Icons.TIMER,
                                    tooltip="Histórico de tempos de análise",
                                    on_click=self._mostrar_historico_tempos
                                ),
                                ft.IconButton(
                                    ft.Icons.BUG_REPORT,
                                    tooltip="Testar botão retry (debug)",
                                    on_click=self._testar_botao_retry
                                )
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            # Segunda linha com botão de retry (visível quando necessário)
                            self.btn_retry_container
                        ]),
                        padding=15
                    )
                ]),
                padding=0
            ),
            elevation=3,
            margin=ft.margin.symmetric(vertical=5)
        )

    def _iniciar_analise(self, e):
        """Inicia análise em thread separada"""
        try:
            logger.info("Solicitando início de análise...")
            
            # Obtém arquivos do BANCO DE DADOS
            arquivos = self._obter_arquivos_selecionados()
            config = self._obter_configuracao()
            
            # Atualiza texto informativo
            self.info_text.value = f"Preparando análise de {len(arquivos)} arquivos..."
            self._safe_update_ui()
            
            if not arquivos:
                self.notifier.error("Nenhum arquivo selecionado para análise")
                self.info_text.value = "Nenhum arquivo selecionado. Use a aba 'Arquivos' para selecionar arquivos."
                self._safe_update_ui()
                return
            
            # Verifica se os arquivos existem
            arquivos_validos = []
            arquivos_inexistentes = []
            
            for arquivo in arquivos:
                if os.path.exists(arquivo):
                    arquivos_validos.append(arquivo)
                else:
                    arquivos_inexistentes.append(arquivo)
                    logger.warning(f"Arquivo não encontrado: {arquivo}")
            
            if not arquivos_validos:
                self.notifier.error("Nenhum arquivo válido selecionado")
                self.info_text.value = "Nenhum arquivo válido encontrado. Verifique os caminhos dos arquivos."
                self._safe_update_ui()
                return
            
            # Avisa sobre arquivos inexistentes
            if arquivos_inexistentes:
                self.notifier.warning(f"{len(arquivos_inexistentes)} arquivo(s) não encontrado(s)")
                logger.warning(f"Arquivos não encontrados: {arquivos_inexistentes}")
            
            # 🔥 NOVO: Mostra informações EXATAMENTE como no console
            total_arquivos = len(arquivos_validos)
            self.info_text.value = f"🔍 Verificando {total_arquivos} arquivos para análise..."
            self._safe_update_ui()

            # Obtém status completo do checkpoint
            try:
                status = self.controller.verificar_status_completo()
                if status.get('status') == 'sucesso':
                    resumo = status.get('resumo', {})
                    economia = status.get('economia', {})

                    # 🔥 MOSTRA EXATAMENTE COMO NO CONSOLE
                    concluidos = resumo.get('sucesso', 0)
                    pendentes = resumo.get('pendente', 0)
                    erros = resumo.get('falha', 0)
                    incompativeis = resumo.get('incompativel', 0)
                    total_status = status.get('total_arquivos', 0)

                    # Linha 1: Status da análise (como no console)
                    self.info_text.value = f"📊 Status: {concluidos} concluídos, {pendentes} pendentes, {erros} erros, {incompativeis} incompatíveis"

                    # Linha 2: Identificados para análise (como no console)
                    self.progress_text.value = f"🎯 Identificados {pendentes} arquivos para análise (de {total_status} totais)"

                    # Linha 3: Iniciando análise (como no console)
                    self.stats_text.value = f"▶️ Iniciando análise de {pendentes} arquivos pendentes"

                    # Se não há arquivos pendentes, mostra mensagem diferente
                    if pendentes == 0:
                        self.info_text.value = f"✅ Análise completa! {concluidos} arquivos já analisados"
                        self.progress_text.value = "Nenhum arquivo pendente para análise"
                        self.stats_text.value = f"Economia: {economia.get('requisicoes_economizadas', 0)} requisições poupadas"
                        self.notifier.success(f"✅ Todos os {total_status} arquivos já foram analisados!")

                    # Mostra economia se for relevante
                    elif economia.get('requisicoes_economizadas', 0) > 0:
                        economia_info = f"💰 Economia: {economia.get('requisicoes_economizadas', 0)} req poupadas ({economia.get('tempo_economizado_segundos', 0):.0f}s)"
                        # Adiciona informação como tooltip ou texto secundário

                        # Notificação se economia for significativa
                        if economia.get('requisicoes_economizadas', 0) > 10:
                            self.notifier.success(f"✅ Checkpoint ativo! {economia.get('requisicoes_economizadas', 0)} arquivos já analisados")

                    # Verifica se há pausa automática ativa
                    pausa_auto = status.get('pausa_automatica', {})
                    if pausa_auto.get('ativa', False):
                        self.status_text.value = f"⚠️ Pausa automática: {pausa_auto.get('motivo', 'API limitada')}"
                        self.status_text.color = ft.Colors.ORANGE_700
                        prox_tentativa = pausa_auto.get('proxima_tentativa_segundos', 0)
                        minutos = prox_tentativa // 60
                        segundos = prox_tentativa % 60
                        # Adiciona informação de pausa no progress text
                        self.progress_text.value = f"⏳ Pausado - Próxima tentativa em {minutos}min {segundos}s | {pendentes} arquivos pendentes"

                        # Ativa botão de retry
                        if self.btn_retry_container:
                            self.btn_forcar_retry.disabled = False
                            self.btn_retry_container.visible = True
                            logger.info("🔥 Botão retry ativado por pausa automática detectada")

                else:
                    # Fallback se status completo falhar
                    self.info_text.value = f"🔍 Verificando {total_arquivos} arquivos para análise..."
                    self.progress_text.value = "Analizando status das análises do projeto..."
                    self.stats_text.value = f"Preparando análise de {total_arquivos} arquivos"

            except Exception as e:
                logger.warning(f"Erro ao obter status do checkpoint: {e}")
                # Fallback com informações básicas
                self.info_text.value = f"🔍 Verificando {total_arquivos} arquivos para análise..."
                self.progress_text.value = f"Preparando análise de {total_arquivos} arquivos..."
                self.stats_text.value = "Status: Aguardando verificação"

            # Atualiza UI
            self._atualizar_ui_analise_iniciada()
            self._safe_update_ui()
            
            # ✅ CORREÇÃO: Salva a análise no histórico se o database estiver disponível
            try:
                tarefa_id = f"analise_{int(time.time())}"
                if hasattr(self.notifier, 'database') and self.notifier.database:
                    self.notifier.database.salvar_analise(
                        tarefa_id,
                        "iniciada",
                        config
                    )
                    logger.info(f"Análise salva no histórico: {tarefa_id}")
            except Exception as db_error:
                logger.warning(f"Erro ao salvar análise no histórico: {db_error}")
            
            # Inicia análise em thread - registra callback personalizado para receber tempo_llm
            logger.info(f"Iniciando análise com {len(arquivos_validos)} arquivos válidos")
            # ✅ CORREÇÃO: Registra callback personalizado para receber tempo_llm na UI
            self.tarefa_ativa = self.controller.iniciar_analise(
                arquivos=arquivos_validos,
                config=config,
                progress_callback=self._on_progresso_analise,  # Usa callback da UI que extrai tempo_llm
                completion_callback=None  # Usa o padrão do controller
            )
            
            if self.tarefa_ativa:
                self.notifier.success(f"Análise iniciada com {len(arquivos_validos)} arquivos")
                logger.info(f"Tarefa de análise iniciada: {self.tarefa_ativa}")
            else:
                self._atualizar_ui_analise_parada()
                self.info_text.value = "Falha ao iniciar análise - verifique os logs"
                self._safe_update_ui()
                logger.error("Falha ao iniciar análise - controller retornou None")
                
        except Exception as ex:
            logger.error(f"Erro ao iniciar análise: {ex}", exc_info=True)
            self.notifier.error(f"Erro ao iniciar análise: {str(ex)}")
            self._atualizar_ui_analise_parada()
            self.info_text.value = f"Erro: {str(ex)}"
            self._safe_update_ui()

    def _pausar_analise(self, e):
        """Pausa a análise atual"""
        try:
            logger.info("Solicitando pausa da análise...")
            if self.controller.pausar_analise():
                self._atualizar_ui_analise_pausada()
                self._safe_update_ui()
                logger.info("Análise pausada com sucesso")
            else:
                self.notifier.warning("Não foi possível pausar a análise")
                logger.warning("Falha ao pausar análise - controller retornou False")
        except Exception as ex:
            logger.error(f"Erro ao pausar análise: {ex}", exc_info=True)
            self.notifier.error(f"Erro ao pausar análise: {str(ex)}")

    def _retomar_analise(self, e):
        """Retoma a análise pausada"""
        try:
            logger.info("Solicitando retomada da análise...")
            if self.controller.retomar_analise():
                self._atualizar_ui_analise_executando()
                self._safe_update_ui()
                logger.info("Análise retomada com sucesso")
            else:
                self.notifier.warning("Não foi possível retomar a análise")
                logger.warning("Falha ao retomar análise - controller retornou False")
        except Exception as ex:
            logger.error(f"Erro ao retomar análise: {ex}", exc_info=True)
            self.notifier.error(f"Erro ao retomar análise: {str(ex)}")

    def _parar_analise(self, e):
        """Para a análise atual"""
        try:
            logger.info("Solicitando parada da análise...")
            if self.controller.parar_analise():
                self._atualizar_ui_analise_parada()
                self._safe_update_ui()
                logger.info("Análise parada com sucesso")
            else:
                self.notifier.warning("Não foi possível parar a análise")
                logger.warning("Falha ao parar análise - controller retornou False")
        except Exception as ex:
            logger.error(f"Erro ao parar análise: {ex}", exc_info=True)
            self.notifier.error(f"Erro ao parar análise: {str(ex)}")

    def _on_progresso_analise(self, progresso: float, arquivo: str, resultado: any):
        """
        Callback para atualizar progresso na UI e registrar métricas de timing.

        Este método serve como um proxy que:
        1. Registra métricas de análise através do callback do controller
        2. Atualiza a interface do usuário com progresso e estatísticas

        Args:
            progresso (float): Percentual de progresso (0.0 a 100.0)
            arquivo (str): Caminho do arquivo sendo analisado
            resultado (any): Resultado da análise contendo:
                - status (str): 'sucesso', 'erro', etc.
                - checkpoint (bool): Se análise foi reaproveitada
                - tempo_llm (float): Tempo gasto na chamada LLM
                - estatisticas (dict): Nodes e edges extraídos

        Note:
            Este callback substitui o callback padrão do controller para permitir
            atualizações específicas da UI enquanto mantém o registro de métricas.
            As métricas são registradas PRIMEIRO para garantir persistência mesmo
            se a atualização da UI falhar.
        """

        # 🔥 CRÍTICO: PRIMEIRO registra métricas usando o callback do controller
        try:
            # Chama o callback do controller para registrar as métricas
            if hasattr(self.controller, '_on_progresso_analise'):
                self.controller._on_progresso_analise(progresso, arquivo, resultado)
                logger.info(f"✅ [UI] Métricas registradas via controller callback para {arquivo}")
        except Exception as metric_error:
            logger.error(f"❌ [UI] Erro ao registrar métricas: {metric_error}")

        # Depois atualiza a UI
        def update_ui():
            try:
                # Atualiza barra de progresso
                self.progress_bar.value = progresso / 100

                # 🔥 MELHORIA: Mantém informações dinâmicas durante progresso
                nome_arquivo = os.path.basename(arquivo)

                if resultado and isinstance(resultado, dict):
                    if resultado.get('checkpoint', False):
                        # Checkpoint reaproveitado
                        self.progress_text.value = f"✅ Checkpoint: {nome_arquivo} ({progresso:.1f}%)"
                        self.status_text.value = f"Status: Executando ({progresso:.1f}%) - Checkpoint ativo"
                    else:
                        # Análise normal
                        self.progress_text.value = f"🔄 Analisando: {nome_arquivo} ({progresso:.1f}%)"
                        self.status_text.value = f"Status: Executando ({progresso:.1f}%)"
                else:
                    # Fallback
                    self.progress_text.value = f"🔄 Processando: {nome_arquivo} ({progresso:.1f}%)"
                    self.status_text.value = f"Status: Executando ({progresso:.1f}%)"

                self.status_text.color = ft.Colors.BLUE_700

                # 🔥 NOVO: Verifica se há checkpoint para mostrar estatísticas dinâmicas
                if resultado and isinstance(resultado, dict):
                    if resultado.get('checkpoint', False):
                        # Mostra info de checkpoint reaproveitado
                        self.progress_text.value = f"✅ Checkpoint: {os.path.basename(arquivo)} ({progresso:.1f}%)"
                        self.timer_text.value = "⚡ Checkpoint (0s)"
                        self.timer_text.color = ft.Colors.GREEN_500
                        self.stats_text.value = "🔄 Análise reaproveitada"
                    else:
                        # Análise normal - atualiza com tempo da LLM
                        tempo_llm = resultado.get('tempo_llm')
                        if tempo_llm is not None:
                            self.current_llm_time = tempo_llm
                            self.timer_text.value = f"Tempo LLM: {tempo_llm:.1f}s"

                            # Muda a cor baseado no tempo
                            if tempo_llm > 30:  # 30 segundos
                                self.timer_text.color = ft.Colors.RED_600
                            elif tempo_llm > 10:  # 10 segundos
                                self.timer_text.color = ft.Colors.ORANGE_600
                            else:
                                self.timer_text.color = ft.Colors.GREEN_600

                        # Atualiza estatísticas se disponível
                        status = resultado.get('status', '')
                        if status == 'sucesso':
                            stats = resultado.get('estatisticas', {})
                            nodes = stats.get('nodes_count', 0)
                            edges = stats.get('edges_count', 0)
                            tempo_proc = stats.get('tempo_processamento', 0)
                            if tempo_proc:
                                self.stats_text.value = f"Último: {nodes} nodes, {edges} edges ({tempo_proc:.1f}s)"
                            else:
                                self.stats_text.value = f"Último: {nodes} nodes, {edges} edges"
                            logger.debug(f"Arquivo processado: {os.path.basename(arquivo)} - {nodes} nodes, {edges} edges")
                        elif status == 'erro':
                            erro = resultado.get('erro', 'Erro desconhecido')
                            self.stats_text.value = f"Erro no último arquivo"
                            logger.error(f"Erro ao processar {os.path.basename(arquivo)}: {erro}")

                # 🔥 NOVO: Verifica status de pausa automática periodicamente
                self._verificar_status_pausa_automatica()

                self._safe_update_ui()

            except Exception as e:
                logger.error(f"Erro ao atualizar UI de progresso: {e}")

        # ✅ CORREÇÃO: Chamada direta e segura
        self._safe_update_ui(update_ui)

    def _verificar_status_pausa_automatica(self):
        """Verifica e atualiza status de pausa automática se necessário"""
        try:
            # 🔥 MELHORIA: Verifica sempre que chamado durante pausas
            if hasattr(self.controller, 'obter_status_pausa_api'):
                status_pausa = self.controller.obter_status_pausa_api()
                logger.debug(f"Status pausa automática: {status_pausa}")

                if status_pausa.get('ativa', False):
                    self.status_text.value = f"⏸️ Pausa automática: {status_pausa.get('motivo', '')}"
                    self.status_text.color = ft.Colors.ORANGE_700

                    # 🔥 CORREÇÃO: Garante que o botão apareça
                    if self.btn_retry_container:
                        self.btn_forcar_retry.disabled = False
                        self.btn_retry_container.visible = True
                        logger.debug("Botão retry tornado visível")

                    prox_tentativa = status_pausa.get('proxima_tentativa_segundos', 0)
                    minutos = prox_tentativa // 60
                    segundos = prox_tentativa % 60
                    self.info_text.value = f"⏳ Próxima tentativa em {minutos}min {segundos}s"
                else:
                    # Esconde botão se não houver pausa
                    if self.btn_retry_container and self.btn_retry_container.visible:
                        self.btn_retry_container.visible = False
                        logger.debug("Botão retry escondido - sem pausa ativa")

        except Exception as e:
            logger.warning(f"Erro ao verificar status de pausa automática: {e}")

    def _mostrar_botao_retry_teste(self):
        """🔥 MÉTODO DE TESTE: Força exibição do botão retry para debug"""
        try:
            if self.btn_retry_container:
                self.btn_forcar_retry.disabled = False
                self.btn_retry_container.visible = True
                self.info_text.value = "🧪 Botão retry visível (teste)"
                self.status_text.value = "⚠️ Modo de teste ativo"
                self.status_text.color = ft.Colors.PURPLE_700
                self._safe_update_ui()
                logger.info("Botão retry forçado para modo de teste")
                return True
        except Exception as e:
            logger.error(f"Erro ao forçar botão retry: {e}")
            return False

    def _testar_botao_retry(self, e):
        """Handler para testar botão retry via ícone de debug"""
        try:
            logger.info("Testando exibição do botão retry...")
            sucesso = self._mostrar_botao_retry_teste()
            if sucesso:
                self.notifier.info("🧪 Botão retry ativado para teste")
            else:
                self.notifier.error("❌ Falha ao ativar botão retry")
        except Exception as ex:
            logger.error(f"Erro no teste do botão retry: {ex}")
            self.notifier.error(f"Erro no teste: {str(ex)}")

    def _on_conclusao_analise(self, resultados: list, erro: str = None):
        """Callback para conclusão da análise"""
        def update_ui():
            try:
                if erro:
                    # Caso de erro
                    self.status_text.value = f"Status: Erro - {erro}"
                    self.status_text.color = ft.Colors.RED_700
                    self.progress_text.value = "Análise falhou"
                    self.info_text.value = f"Erro durante a análise"
                    self.stats_text.value = "Análise interrompida com erro"
                    self.notifier.error(f"Análise falhou: {erro}")
                    logger.error(f"Análise falhou: {erro}")
                else:
                    # 🔥 MELHORIA: Análise detalhada dos resultados
                    total_analisados = len(resultados)
                    sucessos = sum(1 for r in resultados if r.get('status') == 'sucesso')
                    erros = sum(1 for r in resultados if r.get('status') == 'erro')
                    checkpoints = sum(1 for r in resultados if r.get('checkpoint', False))
                    total_nodes = sum(r.get('estatisticas', {}).get('nodes_count', 0) for r in resultados if r.get('status') == 'sucesso')
                    total_edges = sum(r.get('estatisticas', {}).get('edges_count', 0) for r in resultados if r.get('status') == 'sucesso')

                    self.status_text.value = f"✅ Status: Completo - {sucessos}/{total_analisados} arquivos"
                    self.status_text.color = ft.Colors.GREEN_700
                    self.progress_text.value = "Análise concluída com sucesso"

                    # 🔥 MOSTRA RESUMO COMO NO CONSOLE
                    if checkpoints > 0:
                        self.info_text.value = f"📊 Resultado: {sucessos} concluídos, {checkpoints} checkpoints, {erros} erros"
                    else:
                        self.info_text.value = f"📊 Resultado: {sucessos} concluídos, {erros} erros"

                    self.stats_text.value = f"📈 Total: {total_nodes} nodes, {total_edges} edges"

                    # Notificação detalhada
                    if checkpoints > 0:
                        self.notifier.success(f"✅ Análise completada! {sucessos} arquivos, {checkpoints} reaproveitados, {erros} erros")
                        logger.info(f"Análise concluída: {sucessos} sucessos ({checkpoints} checkpoints), {erros} erros, {total_nodes} nodes, {total_edges} edges")
                    else:
                        self.notifier.success(f"Análise completada! {sucessos} arquivos processados, {erros} erros")
                        logger.info(f"Análise concluída: {sucessos} sucessos, {erros} erros, {total_nodes} nodes, {total_edges} edges")
                
                self._atualizar_ui_analise_concluida()
                self._safe_update_ui()
                
            except Exception as e:
                logger.error(f"Erro ao atualizar UI de conclusão: {e}")
        
        # ✅ CORREÇÃO: Chamada direta e segura
        self._safe_update_ui(update_ui)

    def _atualizar_ui_analise_iniciada(self):
        """Atualiza UI quando análise é iniciada"""
        self.btn_iniciar.disabled = True
        self.btn_pausar.disabled = False
        self.btn_retomar.disabled = True
        self.btn_parar.disabled = False
        self.status_text.value = "Status: Executando"
        self.status_text.color = ft.Colors.BLUE_700
        self.progress_text.value = "Iniciando análise..."
        self.progress_bar.value = 0
        self.info_text.value = "Análise em andamento..."
        self.timer_text.value = "Tempo LLM: --s"
        self.timer_text.color = ft.Colors.GREEN_600
        self.current_llm_time = 0
        self.timer_running = True
        self._start_timer()
        logger.debug("UI atualizada para estado: análise iniciada")

    def _atualizar_ui_analise_pausada(self):
        """Atualiza UI quando análise é pausada"""
        self.btn_iniciar.disabled = True
        self.btn_pausar.disabled = True
        self.btn_retomar.disabled = False
        self.btn_parar.disabled = False
        self.status_text.value = "Status: Pausado"
        self.status_text.color = ft.Colors.ORANGE_700
        self.progress_text.value = "Análise pausada"
        self.info_text.value = "Análise pausada - clique em Retomar para continuar"
        self.timer_text.color = ft.Colors.ORANGE_600
        self.timer_running = False
        logger.debug("UI atualizada para estado: análise pausada")

    def _atualizar_ui_analise_executando(self):
        """Atualiza UI quando análise está executando"""
        self.btn_iniciar.disabled = True
        self.btn_pausar.disabled = False
        self.btn_retomar.disabled = True
        self.btn_parar.disabled = False
        self.status_text.value = "Status: Executando"
        self.status_text.color = ft.Colors.BLUE_700
        self.info_text.value = "Análise em andamento..."
        self.timer_text.color = ft.Colors.GREEN_600
        self.timer_running = True
        logger.debug("UI atualizada para estado: análise executando")

    def _atualizar_ui_analise_parada(self):
        """Atualiza UI quando análise é parada"""
        self.btn_iniciar.disabled = False
        self.btn_pausar.disabled = True
        self.btn_retomar.disabled = True
        self.btn_parar.disabled = True
        self.status_text.value = "Status: Parado"
        self.status_text.color = ft.Colors.RED_700
        self.progress_bar.value = 0
        self.progress_text.value = "Análise interrompida"
        self.info_text.value = "Análise parada - pronto para nova execução"
        self.stats_text.value = ""
        self.timer_text.value = "Tempo LLM: --s"
        self.timer_text.color = ft.Colors.GREY_600
        self.current_llm_time = 0
        self.timer_running = False

        # 🔥 NOVO: Esconde botão de retry
        if self.btn_retry_container:
            self.btn_retry_container.visible = False

        self._stop_timer()  # Para o timer quando a análise é parada
        logger.debug("UI atualizada para estado: análise parada")

    def _atualizar_ui_analise_concluida(self):
        """Atualiza UI quando análise é concluída"""
        self.btn_iniciar.disabled = False
        self.btn_pausar.disabled = True
        self.btn_retomar.disabled = True
        self.btn_parar.disabled = True
        self.progress_bar.value = 1.0
        self.timer_text.color = ft.Colors.BLUE_600
        self.timer_running = False

        # 🔥 NOVO: Esconde botão de retry
        if self.btn_retry_container:
            self.btn_retry_container.visible = False

        self._stop_timer()  # Para o timer quando a análise é concluída
        logger.debug("UI atualizada para estado: análise concluída")

    def _obter_arquivos_selecionados(self) -> list:
        """Retorna lista de arquivos selecionados do BANCO DE DADOS"""
        try:
            if hasattr(self.notifier, 'database') and self.notifier.database:
                arquivos = self.notifier.database.obter_arquivos_selecionados()
                logger.debug(f"Obtidos {len(arquivos)} arquivos selecionados do banco")
                return arquivos
            else:
                logger.warning("Serviço de banco de dados não disponível")
                return []
        except Exception as e:
            logger.error(f"Erro ao obter arquivos selecionados do banco: {e}")
            return []
    
    def _obter_configuracao(self) -> dict:
        """Retorna configuração da análise"""
        try:
            config = self.controller.get_config()
            logger.debug("Configuração obtida do controller")
            return config
        except Exception as e:
            logger.error(f"Erro ao obter configuração: {e}")
            return {}

    def _safe_update_ui(self, update_function=None):
        """✅ CORREÇÃO: Método seguro para atualizar a UI que funciona com qualquer versão do Flet"""
        try:
            if update_function:
                # Se uma função de atualização foi fornecida, execute-a
                update_function()
            else:
                # Se não, apenas atualize a página
                if self.page:
                    self.page.update()
                    
        except Exception as e:
            logger.warning(f"Erro na atualização direta da UI: {e}")
            try:
                # Tentativa alternativa
                if self.page:
                    # Força atualização mesmo com erro
                    self.page.update()
            except Exception as e2:
                logger.error(f"Falha na atualização alternativa da UI: {e2}")

    def _mostrar_info_analise(self, e):
        """Mostra informações sobre a análise atual"""
        try:
            status = self.controller.get_status_analise()
            
            info_mensagem = f"""
📊 Status da Análise:

• Executando: {status.get('executando', False)}
• Pausada: {status.get('pausada', False)}
• Parada: {status.get('parada', True)}
• Completada: {status.get('completada', False)}

📈 Progresso: {status.get('progresso', 0):.1f}%
📁 Arquivo Atual: {os.path.basename(status.get('arquivo_atual', 'Nenhum'))}
📊 Resultados: {status.get('resultados_count', 0)} arquivos processados
"""
            
            self.notifier.info("Informações da análise atual")
            logger.debug(f"Status da análise: {status}")
            
        except Exception as ex:
            logger.error(f"Erro ao mostrar informações da análise: {ex}")
            self.notifier.error("Erro ao obter informações da análise")

    def _mostrar_historico_tempos(self, e):
        """Mostra o histórico de tempos de análise"""
        try:
            # Obtém o histórico do timer service
            historico = self.controller.timer_service.get_analysis_history(limit=20)
            estatisticas = self.controller.timer_service.get_statistics()

            if not historico:
                self.notifier.info("Nenhuma análise registrada ainda")
                return

            # Cria o conteúdo do diálogo
            dialog_content = ft.Column([
                # Estatísticas gerais
                ft.Container(
                    content=ft.Column([
                        ft.Text("Estatísticas Gerais", weight=ft.FontWeight.BOLD, size=16),
                        ft.Row([
                            ft.Text(f"Total: {estatisticas.get('total_analyses', 0)}"),
                            ft.Text(f"Sucesso: {estatisticas.get('completed_analyses', 0)}"),
                            ft.Text(f"Falhas: {estatisticas.get('failed_analyses', 0)}")
                        ]),
                        ft.Row([
                            ft.Text(f"Taxa de sucesso: {estatisticas.get('success_rate', 0):.1f}%"),
                            ft.Text(f"Tempo médio: {estatisticas.get('average_analysis_time', 'N/A')}")
                        ])
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=5
                ),
                ft.Divider(),
                # Lista de análises
                ft.Text("Análises Recentes", weight=ft.FontWeight.BOLD, size=14),
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"Projeto: {analise['project_name']}", weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        analise['status'],
                                        color=ft.Colors.GREEN if analise['status'] == 'completed' else ft.Colors.RED,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Row([
                                    ft.Text(f"Arquivos: {analise['file_count']}"),
                                    ft.Text(f"Duração: {analise.get('total_duration_formatted', 'N/A')}")
                                ]),
                                ft.Row([
                                    ft.Text(f"Tempo efetivo: {analise.get('effective_analysis_formatted', 'N/A')}"),
                                    ft.Text(f"Média por arquivo: {analise.get('average_time_per_file_formatted', 'N/A')}")
                                ]),
                                ft.Text(f"Data: {analise['start_time'][:19].replace('T', ' ')}", size=10, color=ft.Colors.GREY_600)
                            ], spacing=2),
                            padding=10,
                            bgcolor=ft.Colors.WHITE,
                            border=ft.border.all(1, ft.Colors.OUTLINE),
                            border_radius=5,
                            margin=ft.margin.only(bottom=5)
                        )
                        for analise in reversed(historico[-10:])  # Últimas 10 análises
                    ], scroll=ft.ScrollMode.AUTO),
                    height=400
                ),
                ft.Divider(),
                ft.Row([
                    ft.ElevatedButton(
                        "Exportar Relatório",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=self._exportar_relatorio_tempos
                    ),
                    ft.TextButton(
                        "Fechar",
                        on_click=lambda e: self._fechar_dialogo_tempos()
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ], scroll=ft.ScrollMode.AUTO, spacing=10)

            # Cria e mostra o diálogo
            self.dialogo_tempos = ft.AlertDialog(
                modal=True,
                title=ft.Text("Histórico de Tempos de Análise"),
                content=dialog_content,
                padding=20,
                width=700,
                height=600
            )

            self.page.dialog = self.dialogo_tempos
            self.dialogo_tempos.open = True
            self.page.update()

        except Exception as ex:
            logger.error(f"Erro ao mostrar histórico de tempos: {ex}")
            self.notifier.error("Erro ao carregar histórico de tempos")

    def _exportar_relatorio_tempos(self, e):
        """Exporta um relatório completo dos tempos de análise"""
        try:
            export_path = self.controller.timer_service.export_report()
            self.notifier.success(f"Relatório exportado para: {export_path}")
        except Exception as ex:
            logger.error(f"Erro ao exportar relatório: {ex}")
            self.notifier.error("Erro ao exportar relatório")

    def _fechar_dialogo_tempos(self):
        """Fecha o diálogo de tempos"""
        if hasattr(self, 'dialogo_tempos'):
            self.dialogo_tempos.open = False
            self.page.update()

    def set_page(self, page: ft.Page):
        """Define a página para atualizações da UI"""
        self.page = page
        # ✅ CORREÇÃO: Conectar os componentes de UI ao controller
        if hasattr(self.controller, 'set_ui_components'):
            self.controller.set_ui_components(
                progress_bar=self.progress_bar,
                progress_text=self.progress_text, 
                status_text=self.status_text,
                info_text=self.info_text,
                page=self.page
            )
            logger.info("Componentes de UI conectados ao controller")
        else:
            logger.warning("Controller não possui método set_ui_components")

    def update(self):
        """Atualiza o componente manualmente"""
        try:
            self._safe_update_ui()
        except Exception as e:
            logger.error(f"Erro ao atualizar ExecutionCard: {e}")

    def reset_ui(self):
        """Reseta a UI para o estado inicial"""
        try:
            self._atualizar_ui_analise_parada()
            self.progress_bar.value = 0
            self.progress_text.value = "Pronto para iniciar análise"
            self.status_text.value = "Status: Ocioso"
            self.status_text.color = ft.Colors.GREY_700
            self.info_text.value = "Selecione arquivos e configure as opções para iniciar"
            self.stats_text.value = ""
            self.timer_text.value = "Tempo LLM: --s"
            self.timer_text.color = ft.Colors.GREY_600
            self.current_llm_time = 0
            self.timer_running = False
            self._safe_update_ui()
            logger.debug("UI resetada para estado inicial")
        except Exception as e:
            logger.error(f"Erro ao resetar UI: {e}")

    def _start_timer(self):
        """Inicia a atualização do timer em tempo real"""
        try:
            # Para o timer anterior se existir
            if hasattr(self, '_timer_task') and self._timer_task is not None:
                self._stop_timer()

            # Inicia novo timer se a página estiver disponível
            if self.page and hasattr(self.page, 'set_interval'):
                self._timer_task = self.page.set_interval(
                    1000,  # Atualiza a cada 1 segundo
                    self._update_timer
                )
                logger.debug(f"Timer de análise iniciado: {self._timer_task}")
            else:
                logger.warning("Página não disponível para iniciar timer")
        except Exception as e:
            logger.error(f"Erro ao iniciar timer: {e}", exc_info=True)

    def _update_timer(self):
        """Atualiza o display do tempo decorrido (mantém o tempo da LLM)"""
        try:
            # Como agora mostramos apenas o tempo da LLM que é atualizado via callback,
            # este método não precisa fazer nada, apenas manter o timer rodando
            if self.timer_running and hasattr(self, 'timer_text'):
                # Se não houver tempo LLM definido, mostra aguardando
                if self.current_llm_time == 0:
                    self.timer_text.value = "Tempo LLM: aguardando..."
                # A UI é atualizada pelo callback _on_progresso_analise
        except Exception as e:
            logger.error(f"Erro ao atualizar timer: {e}", exc_info=True)

    def _forcar_retry_api(self, e):
        """Força tentativa imediata de conexão com API"""
        try:
            logger.info("Usuário solicitou retentativa forçada da API...")
            self.info_text.value = "🔄 Testando conexão com API..."
            self._safe_update_ui()

            resultado = self.controller.forcar_retentativa_api()

            if resultado.get('status') == 'sucesso':
                self.notifier.success("✅ API respondeu! Análise retomada.")
                self.info_text.value = "✅ API disponível! Análise retomada."
                self.status_text.value = "Status: Executando"
                self.status_text.color = ft.Colors.BLUE_700

                # Esconde botão de retry
                if self.btn_retry_container:
                    self.btn_retry_container.visible = False

                self._safe_update_ui()
            else:
                self.notifier.warning("❌ API ainda não respondeu. Continuando aguardo...")
                self.info_text.value = "❌ API ainda indisponível. Aguardando retentativa automática..."
                self._safe_update_ui()

        except Exception as ex:
            logger.error(f"Erro ao forçar retry da API: {ex}")
            self.notifier.error(f"Erro ao forçar retry: {str(ex)}")
            self.info_text.value = "Erro ao testar API. Verifique logs."
            self._safe_update_ui()

    def _stop_timer(self):
        """Para a atualização do timer"""
        try:
            if hasattr(self, '_timer_task') and self._timer_task is not None:
                if hasattr(self.page, 'unset_interval'):
                    self.page.unset_interval(self._timer_task)
                self._timer_task = None
                logger.debug("Timer de análise parado")
        except Exception as e:
            logger.error(f"Erro ao parar timer: {e}")