import flet as ft
import logging

logger = logging.getLogger(__name__)

class PromptCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        
    def build(self) -> ft.Card:
        """Constrói o card de customização do prompt"""
        # Campo principal do prompt
        self.txt_prompt_principal = ft.TextField(
            label="Template do Prompt Principal",
            multiline=True,
            min_lines=10,
            max_lines=20,
            value=self._get_prompt_padrao(),
            on_change=self._on_prompt_change,
            tooltip="Use {filename}, {lang} e {code} como placeholders."
        )
        
        # Modo semi-automático
        self.chk_semi_automatico = ft.Checkbox(
            label="Habilitar modo Semi-Automático (pausa em arquivos específicos)",
            value=False,
            on_change=self._on_semi_automatic_toggle
        )
        
        # Arquivos para pausa
        self.txt_breakpoint_files = ft.TextField(
            label="Arquivos para Pausa (separados por vírgula)",
            hint_text="ex: main.c, utils.py, config.h",
            expand=True,
            disabled=True,
            on_change=self._on_breakpoint_files_change
        )
        
        # Botão para restaurar prompt padrão
        self.btn_restaurar_prompt = ft.OutlinedButton(
            "Restaurar Prompt Padrão",
            icon=ft.Icons.RESTORE,
            on_click=self._restaurar_prompt_padrao
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CHAT, color=ft.Colors.GREEN_500),
                        title=ft.Text(
                            "Customização do Prompt",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        subtitle=ft.Text(
                            "Configure o prompt para análise de código",
                            color=ft.Colors.GREY_600
                        )
                    ),
                    ft.Divider(height=1),
                    
                    # Prompt principal
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Prompt de Análise", size=14, weight=ft.FontWeight.BOLD),
                            self.txt_prompt_principal,
                            ft.Row([
                                self.btn_restaurar_prompt,
                                ft.Container(expand=True),
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_300, size=20)
                            ])
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    ),
                    
                    ft.Divider(height=1),
                    
                    # Modo semi-automático
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Modo Semi-Automático", size=14, weight=ft.FontWeight.BOLD),
                            self.chk_semi_automatico,
                            ft.Row([
                                self.txt_breakpoint_files,
                                ft.IconButton(
                                    ft.Icons.HELP_OUTLINE,
                                    tooltip="Quando a análise encontrar um destes arquivos, ela pausará e pedirá um prompt customizado."
                                )
                            ])
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    )
                ]),
                padding=0
            ),
            elevation=2,
            margin=ft.margin.symmetric(vertical=5)
        )
    
    def _get_prompt_padrao(self) -> str:
        """Retorna o prompt padrão para análise"""
        return (
            "Você é um engenheiro de software sênior especializado em análise de código-fonte e arquitetura de sistemas.\n"
            "Sua missão é realizar uma análise completa do arquivo de código fornecido e estruturar sua resposta em duas seções distintas, conforme detalhado abaixo.\n\n"
            "--------------------------------\n"
            "### SEÇÃO 1: FORMATO OBRIGATÓRIO DO GRAFO JSON\n"
            "Para a tarefa de geração do grafo, você DEVE gerar o JSON seguindo ESTRITAMENTE o formato, a estrutura e a riqueza de detalhes do exemplo a seguir. Preencha todos os campos possíveis com base na sua análise do código, incluindo `group`, `shape`, `color` e especialmente os `metadata`.\n\n"
            "```json\n"
            "{{\n"
            '  "nodes": [],\n'
            '  "edges": [],\n'
            '  "meta": {{}}\n'
            "}}\n"
            "```\n\n"
            "--------------------------------\n"
            "### SEÇÃO 2: SUAS TAREFAS\n\n"
            "Com base no código-fonte fornecido, execute as seguintes tarefas:\n\n"
            "1.  **ANÁLISE TÉCNICA:**\n"
            "    - Escreva uma análise clara e técnica sobre o propósito e a funcionalidade do código.\n"
            "    - Descreva as responsabilidades principais da classe/função.\n"
            "    - Explique as lógicas de negócio e o fluxo de execução de ponta a ponta.\n\n"
            "2.  **GRAFO DE FLUXO (JSON):**\n"
            "    - Gere um grafo completo em formato JSON que mapeia as interações e chamadas no código.\n"
            "    - Siga rigorosamente o formato rico do exemplo na SEÇÃO 1.\n\n"
            "--- CÓDIGO DO ARQUIVO: {filename} ---\n"
            "```{lang}\n{code}\n```\n\n"
            "--- ANÁLISE COMPLETA ---\n"
        )
    
    def _on_prompt_change(self, e):
        """Callback quando o prompt é alterado"""
        try:
            novo_prompt = e.control.value
            # Aqui você pode salvar o prompt no controller se necessário
            logger.debug("Prompt alterado")
        except Exception as ex:
            logger.error(f"Erro ao alterar prompt: {ex}")
    
    def _on_semi_automatic_toggle(self, e):
        """Callback quando o modo semi-automático é alternado"""
        try:
            habilitado = e.control.value
            self.txt_breakpoint_files.disabled = not habilitado
            
            if self.page:
                self.page.update()
                
            logger.debug(f"Modo semi-automático: {habilitado}")
            
        except Exception as ex:
            logger.error(f"Erro ao alternar modo semi-automático: {ex}")
    
    def _on_breakpoint_files_change(self, e):
        """Callback quando os arquivos de pausa são alterados"""
        try:
            arquivos = e.control.value
            # Aqui você pode processar a lista de arquivos
            logger.debug(f"Arquivos para pausa: {arquivos}")
        except Exception as ex:
            logger.error(f"Erro ao alterar arquivos de pausa: {ex}")
    
    def _restaurar_prompt_padrao(self, e):
        """Restaura o prompt padrão"""
        try:
            self.txt_prompt_principal.value = self._get_prompt_padrao()
            
            if self.page:
                self.page.update()
                
            self.notifier.info("Prompt restaurado para o padrão")
            logger.info("Prompt restaurado para o padrão")
            
        except Exception as ex:
            logger.error(f"Erro ao restaurar prompt padrão: {ex}")
            self.notifier.error(f"Erro ao restaurar prompt: {str(ex)}")
    
    def get_prompt_atual(self) -> str:
        """Retorna o prompt atual"""
        return self.txt_prompt_principal.value
    
    def get_arquivos_pausa(self) -> list:
        """Retorna a lista de arquivos para pausa"""
        if self.txt_breakpoint_files.value:
            return [arquivo.strip() for arquivo in self.txt_breakpoint_files.value.split(',')]
        return []
    
    def is_modo_semi_automatico(self) -> bool:
        """Verifica se o modo semi-automático está ativo"""
        return self.chk_semi_automatico.value
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações da UI"""
        self.page = page
    
    def update(self):
        """Atualiza o componente"""
        # Pode ser usado para atualizações manuais
        pass