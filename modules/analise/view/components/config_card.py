import flet as ft
import logging

logger = logging.getLogger(__name__)

class ConfigCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.config_controls = {}

    def build(self) -> ft.Card:
        """Constrói o card de configuração"""
        try:
            # Obtém configuração padrão do controller
            default_config = self.controller.get_default_config()
            logger.info("Configuração padrão obtida com sucesso")
            
            # Cria os controles de configuração
            config_controls = self._criar_controles_configuracao(default_config)
            
            # Botão para testar conexão Ollama
            btn_testar_ollama = ft.ElevatedButton(
                "Testar Conexão Ollama",
                icon=ft.Icons.CLOUD_QUEUE,
                on_click=self._testar_conexao_ollama,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.PURPLE_600
                )
            )
            
            # Botão para salvar configuração
            btn_salvar = ft.ElevatedButton(
                "Salvar Configuração",
                icon=ft.Icons.SAVE,
                on_click=self._salvar_configuracao,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_600
                )
            )
            
            # Botão para restaurar padrão
            btn_restaurar = ft.OutlinedButton(
                "Restaurar Padrão",
                icon=ft.Icons.RESTORE,
                on_click=self._restaurar_padrao
            )
            
            # Status da conexão Ollama
            self.status_ollama = ft.Text("Clique em 'Testar Conexão' para verificar", 
                                        size=12, color=ft.Colors.GREY_600)
            
            return ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLUE_500),
                            title=ft.Text(
                                "Configurações de Análise",
                                weight=ft.FontWeight.BOLD,
                                size=16
                            ),
                            subtitle=ft.Text(
                                "Configure os parâmetros da análise de código e LLM",
                                color=ft.Colors.GREY_600
                            )
                        ),
                        ft.Divider(height=1),
                        
                        # Configurações do LLM
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Configurações do LLM (Ollama)", 
                                       size=14, weight=ft.FontWeight.BOLD,
                                       color=ft.Colors.PURPLE_700),
                                *self._criar_controles_llm(default_config),
                                ft.Row([btn_testar_ollama]),
                                self.status_ollama
                            ]),
                            padding=ft.padding.symmetric(horizontal=15, vertical=10)
                        ),
                        
                        ft.Divider(height=1),
                        
                        # Configurações gerais
                        ft.Container(
                            content=ft.Column(
                                controls=config_controls,
                                spacing=15
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=15)
                        ),
                        
                        ft.Divider(height=1),
                        
                        # Botões de ação
                        ft.Container(
                            content=ft.Row([
                                btn_salvar,
                                btn_restaurar,
                                ft.Container(expand=True),
                                ft.Icon(ft.Icons.SETTINGS_SUGGEST, color=ft.Colors.BLUE_300)
                            ]),
                            padding=ft.padding.symmetric(horizontal=10, vertical=10)
                        )
                    ]),
                    padding=0
                ),
                elevation=2,
                margin=ft.margin.symmetric(vertical=5)
            )
            
        except Exception as e:
            logger.error(f"Erro ao construir card de configuração: {e}")
            return self._build_fallback_card()
 
    def _criar_controles_llm(self, config: dict) -> list:
        """Cria controles para configurações do LLM"""
        controls = []
        
        # URL da API
        llm_url = ft.TextField(
            label="URL da API Ollama",
            value=config.get('llm_url', 'http://localhost:11434'),
            hint_text="http://localhost:11434",
            on_change=lambda e: self._on_config_change('llm_url', e.control.value)
        )
        self.config_controls['llm_url'] = llm_url
        controls.append(llm_url)
        
        # Modelo
        llm_modelo = ft.Dropdown(
            label="Modelo",
            value=config.get('llm_modelo', 'codellama:7b'),  # Use um modelo mais comum
            options=[
                ft.dropdown.Option("codellama:7b", "Code Llama 7B"),
                ft.dropdown.Option("llama2", "Llama 2"),
                ft.dropdown.Option("mistral", "Mistral"),
                ft.dropdown.Option("phi", "Phi-2"),
            ],
            on_change=lambda e: self._on_config_change('llm_modelo', e.control.value)
        )
        self.config_controls['llm_modelo'] = llm_modelo
        controls.append(llm_modelo)
        
        # Tamanho do contexto
        llm_contexto = ft.Slider(
            label="Tamanho do Contexto",
            value=config.get('llm_tamanho_contexto', 4096),
            min=1024,
            max=16384,
            divisions=15,
            on_change=lambda e: self._on_config_change('llm_tamanho_contexto', int(e.control.value))
        )
        self.config_controls['llm_tamanho_contexto'] = llm_contexto
        controls.append(llm_contexto)
        
        # Indicador de contexto
        controls.append(
            ft.Text(
                f"Contexto: {config.get('llm_tamanho_contexto', 4096)} tokens",
                size=12,
                color=ft.Colors.GREY_600,
                italic=True
            )
        )
        
        # Temperatura
        llm_temperatura = ft.Slider(
            label="Temperatura (criatividade)",
            value=config.get('llm_temperatura', 0.7),
            min=0.1,
            max=1.0,
            divisions=9,
            on_change=lambda e: self._on_config_change('llm_temperatura', round(e.control.value, 2))
        )
        self.config_controls['llm_temperatura'] = llm_temperatura
        controls.append(llm_temperatura)
        
        # Indicador de temperatura
        controls.append(
            ft.Text(
                f"Temperatura: {config.get('llm_temperatura', 0.7):.2f}",
                size=12,
                color=ft.Colors.GREY_600,
                italic=True
            )
        )
        
        return controls
           
    def _criar_controles_configuracao(self, config: dict) -> list:
        """Cria os controles de configuração baseados no dicionário de config"""
        controls = []
        self.config_controls.clear()
        
        # Grupo: Configurações Gerais
        controls.append(
            ft.Text(
                "Configurações Gerais",
                weight=ft.FontWeight.BOLD,
                size=14,
                color=ft.Colors.BLUE_700
            )
        )
        
        # Nível de Análise
        nivel_analise = ft.Dropdown(
            label="Nível de Análise",
            value=config.get('nivel_analise', 'detalhado'),
            options=[
                ft.dropdown.Option("basico", "Básico"),
                ft.dropdown.Option("intermediario", "Intermediário"),
                ft.dropdown.Option("detalhado", "Detalhado"),
            ],
            on_change=lambda e: self._on_config_change('nivel_analise', e.control.value)
        )
        self.config_controls['nivel_analise'] = nivel_analise
        controls.append(nivel_analise)
        
        # Linguagem
        linguagem = ft.Dropdown(
            label="Linguagem",
            value=config.get('linguagem', 'c'),
            options=[
                ft.dropdown.Option("c", "C"),
                ft.dropdown.Option("cpp", "C++"),
                ft.dropdown.Option("cs", "Csharp"),
                ft.dropdown.Option("python", "Python"),
                ft.dropdown.Option("go", "Go"),
                ft.dropdown.Option("java", "Java"),
            ],
            on_change=lambda e: self._on_config_change('linguagem', e.control.value)
        )
        self.config_controls['linguagem'] = linguagem
        controls.append(linguagem)
        
        # Limite de Linhas
        limite_linhas = ft.TextField(
            label="Limite de Linhas por Arquivo",
            value=str(config.get('limite_linhas', 1000)),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._on_config_change('limite_linhas', int(e.control.value) if e.control.value.isdigit() else 1000)
        )
        self.config_controls['limite_linhas'] = limite_linhas
        controls.append(limite_linhas)
        
        # Grupo: Opções de Saída
        controls.append(
            ft.Container(
                content=ft.Text(
                    "Opções de Saída",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                    color=ft.Colors.BLUE_700
                ),
                padding=ft.padding.only(top=20)
            )
        )
        
        # Switches para opções booleanas
        opcoes_booleanas = [
            ('incluir_comentarios', 'Incluir Comentários', config.get('incluir_comentarios', True)),
            ('analisar_dependencias', 'Analisar Dependências', config.get('analisar_dependencias', True)),
            ('gerar_json', 'Gerar JSON', config.get('gerar_json', True)),
            ('gerar_explicabilidade', 'Gerar Explicabilidade', config.get('gerar_explicabilidade', True)),
        ]
        
        for key, label, value in opcoes_booleanas:
            switch = ft.Switch(
                label=label,
                value=value,
                label_position=ft.LabelPosition.LEFT,
                on_change=lambda e, k=key: self._on_config_change(k, e.control.value)
            )
            self.config_controls[key] = switch
            controls.append(
                ft.Row([
                    switch,
                    ft.Container(expand=True)
                ])
            )
        
        # Configuração de Threads
        controls.append(
            ft.Container(
                content=ft.Text(
                    "Configurações de Performance",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                    color=ft.Colors.BLUE_700
                ),
                padding=ft.padding.only(top=20)
            )
        )
        
        threads = ft.Slider(
            label="Número de Threads",
            value=config.get('threads', 1),
            min=1,
            max=8,
            divisions=7,
            on_change=lambda e: self._on_config_change('threads', int(e.control.value))
        )
        self.config_controls['threads'] = threads
        controls.append(threads)
        
        # Indicador de threads
        controls.append(
            ft.Text(
                f"Threads: {config.get('threads', 1)}",
                size=12,
                color=ft.Colors.GREY_600,
                italic=True
            )
        )
        
        return controls

    def _testar_conexao_ollama(self, e):
        """Testa a conexão com o Ollama e atualiza modelos disponíveis"""
        try:
            self.status_ollama.value = "Testando conexão com Ollama..."
            self.status_ollama.color = ft.Colors.BLUE
            if hasattr(e, 'page'):
                e.page.update()
            
            # Testa conexão
            resultado = self.controller.testar_conexao_ollama()
            
            if resultado.get('conectado'):
                modelos = resultado.get('modelos', [])
                
                # Atualiza a lista de modelos no dropdown
                if 'llm_modelo' in self.config_controls:
                    dropdown = self.config_controls['llm_modelo']
                    # Limpa opções antigas
                    dropdown.options.clear()
                    
                    # Adiciona modelos disponíveis
                    for modelo in modelos:
                        dropdown.options.append(ft.dropdown.Option(modelo, modelo))
                    
                    # Seleciona o primeiro modelo se não houver seleção
                    if not dropdown.value and modelos:
                        dropdown.value = modelos[0]
                        self._on_config_change('llm_modelo', modelos[0])
                    
                    # Se o modelo atual não estiver disponível, seleciona o primeiro
                    elif dropdown.value not in modelos and modelos:
                        dropdown.value = modelos[0]
                        self._on_config_change('llm_modelo', modelos[0])
                        self.notifier.info(f"Modelo alterado para {modelos[0]} (modelo anterior não disponível)")
                
                self.status_ollama.value = f"✅ Conectado! {len(modelos)} modelos disponíveis"
                self.status_ollama.color = ft.Colors.GREEN
                self.notifier.success("Conexão com Ollama estabelecida com sucesso!")
            else:
                self.status_ollama.value = f"❌ Erro: {resultado.get('erro', 'Não foi possível conectar')}"
                self.status_ollama.color = ft.Colors.RED
                self.notifier.error("Falha na conexão com Ollama")
            
            if hasattr(e, 'page'):
                e.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao testar conexão Ollama: {ex}")
            self.status_ollama.value = f"❌ Erro: {str(ex)}"
            self.status_ollama.color = ft.Colors.RED
            if hasattr(e, 'page'):
                e.page.update()
            self.notifier.error(f"Erro ao testar conexão: {str(ex)}")

    def _on_config_change(self, key: str, value: any):
        """Callback quando uma configuração é alterada"""
        try:
            # Atualiza o controlador
            self.controller.update_config({key: value})
            
            # Log para debugging
            logger.debug(f"Configuração alterada: {key} = {value}")
            
            # Atualiza indicadores visuais se necessário
            if key == 'threads' and 'threads' in self.config_controls:
                # Encontra o texto do indicador de threads (próximo controle após o slider)
                pass  # Poderia implementar atualização em tempo real aqui
                
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração {key}: {e}")
            self.notifier.error(f"Erro ao atualizar {key}: {str(e)}")

    def _salvar_configuracao(self, e):
        """Salva a configuração atual"""
        try:
            # Coleta todos os valores atuais dos controles
            config_atual = {}
            
            for key, control in self.config_controls.items():
                if isinstance(control, ft.Dropdown):
                    config_atual[key] = control.value
                elif isinstance(control, ft.TextField):
                    if key == 'limite_linhas':
                        config_atual[key] = int(control.value) if control.value.isdigit() else 1000
                    else:
                        config_atual[key] = control.value
                elif isinstance(control, ft.Switch):
                    config_atual[key] = control.value
                elif isinstance(control, ft.Slider):
                    config_atual[key] = int(control.value)
            
            # Atualiza no controller
            self.controller.update_config(config_atual)
            
            # Notifica sucesso
            self.notifier.success("Configuração salva com sucesso!")
            logger.info("Configuração salva com sucesso")
            
        except Exception as ex:
            logger.error(f"Erro ao salvar configuração: {ex}")
            self.notifier.error(f"Erro ao salvar configuração: {str(ex)}")

    def _restaurar_padrao(self, e):
        """Restaura as configurações padrão"""
        try:
            # Obtém configuração padrão
            config_padrao = self.controller.get_default_config()
            
            # Atualiza os controles
            for key, control in self.config_controls.items():
                valor_padrao = config_padrao.get(key)
                
                if isinstance(control, ft.Dropdown) and valor_padrao is not None:
                    control.value = valor_padrao
                elif isinstance(control, ft.TextField) and valor_padrao is not None:
                    control.value = str(valor_padrao)
                elif isinstance(control, ft.Switch) and valor_padrao is not None:
                    control.value = valor_padrao
                elif isinstance(control, ft.Slider) and valor_padrao is not None:
                    control.value = valor_padrao
            
            # Atualiza no controller
            self.controller.update_config(config_padrao)
            
            # Notifica sucesso
            self.notifier.info("Configurações restauradas para o padrão")
            logger.info("Configurações restauradas para o padrão")
            
            # Força atualização da UI
            if hasattr(e, 'page') and e.page:
                e.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao restaurar configurações padrão: {ex}")
            self.notifier.error(f"Erro ao restaurar configurações: {str(ex)}")

    def _build_fallback_card(self) -> ft.Card:
        """Constrói um card de fallback em caso de erro"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED),
                        title=ft.Text(
                            "Configurações de Análise",
                            weight=ft.FontWeight.BOLD
                        ),
                        subtitle=ft.Text(
                            "Erro ao carregar configurações",
                            color=ft.Colors.RED
                        )
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Não foi possível carregar as configurações. "
                            "Verifique os logs para mais detalhes.",
                            color=ft.Colors.GREY_600
                        ),
                        padding=15
                    ),
                    ft.ElevatedButton(
                        "Tentar Recarregar",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: self._recarregar_configuracoes(e)
                    )
                ]),
                padding=10
            )
        )

    def _recarregar_configuracoes(self, e):
        """Tenta recarregar as configurações"""
        try:
            if hasattr(e, 'page') and e.page:
                # Remove o card atual
                e.page.controls[0].content.controls[0] = self.build()
                e.page.update()
                self.notifier.info("Configurações recarregadas")
        except Exception as ex:
            logger.error(f"Erro ao recarregar configurações: {ex}")
            self.notifier.error("Erro ao recarregar configurações")

    def atualizar_ui(self):
        """Atualiza a UI com os valores atuais do controller"""
        try:
            config_atual = self.controller.get_config()
            
            for key, control in self.config_controls.items():
                valor_atual = config_atual.get(key)
                
                if isinstance(control, ft.Dropdown) and valor_atual is not None:
                    control.value = valor_atual
                elif isinstance(control, ft.TextField) and valor_atual is not None:
                    control.value = str(valor_atual)
                elif isinstance(control, ft.Switch) and valor_atual is not None:
                    control.value = valor_atual
                elif isinstance(control, ft.Slider) and valor_atual is not None:
                    control.value = valor_atual
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar UI das configurações: {e}")

    def get_configuracao_atual(self) -> dict:
        """Retorna a configuração atual dos controles"""
        config = {}
        for key, control in self.config_controls.items():
            if hasattr(control, 'value'):
                config[key] = control.value
        return config