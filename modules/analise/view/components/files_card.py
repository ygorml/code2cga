import flet as ft
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

class FilesCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        self.arquivos_selecionados = []
        self.file_picker = None
        self.folder_picker = None
        self.pasta_base = "inspecao/"
        
        # Inicializa os controles no __init__
        self._inicializar_controles()
    
    def _inicializar_controles(self):
        """Inicializa todos os controles da UI"""
        # Campo para pasta de inspeção
        self.txt_pasta_inspecao = ft.TextField(
            label="Pasta de Inspeção",
            value=self.pasta_base,
            read_only=True,
            expand=True
        )
        
        # Estatísticas da pasta
        self.txt_folder_stats = ft.Text("Clique em atualizar para ver estatísticas", 
                                       italic=True, color=ft.Colors.GREY_600)
        
        # Botão para atualizar estatísticas e carregar arquivos
        self.btn_carregar_automatico = ft.ElevatedButton(
            "Carregar Todos os Arquivos",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._carregar_arquivos_automatico,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN)
        )
        
        # Botão para atualizar estatísticas
        self.btn_refresh_stats = ft.ElevatedButton(
            "Atualizar Estatísticas",
            icon=ft.Icons.REFRESH,
            on_click=self._atualizar_estatisticas
        )
        
        # Lista de arquivos com checkboxes
        self.lista_arquivos = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            auto_scroll=True
        )
        
        # Botão para selecionar arquivos/pastas adicionais
        self.btn_adicionar_arquivos = ft.ElevatedButton(
            "Adicionar Arquivos",
            icon=ft.Icons.ADD,
            on_click=self._selecionar_arquivos,
            tooltip="Adicionar arquivos específicos à análise"
        )
        
        self.btn_adicionar_pasta = ft.ElevatedButton(
            "Adicionar Pasta",
            icon=ft.Icons.CREATE_NEW_FOLDER,
            on_click=self._selecionar_pasta,
            tooltip="Adicionar pasta específica à análise"
        )
        
        # Botão para limpar seleção
        self.btn_limpar_selecao = ft.OutlinedButton(
            "Limpar Seleção",
            icon=ft.Icons.CLEAR,
            on_click=self._limpar_selecao
        )
        
        # Botão para desmarcar todos
        self.btn_desmarcar_todos = ft.OutlinedButton(
            "Desmarcar Todos",
            icon=ft.Icons.CHECK_BOX_OUTLINE_BLANK,
            on_click=self._desmarcar_todos
        )
        
        # Contador de arquivos selecionados
        self.contador_arquivos = ft.Text("Nenhum arquivo selecionado", size=12, color=ft.Colors.GREY_600)

    def build(self) -> ft.Card:
        """Constrói o card de gerenciamento de arquivos"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER_OPEN, color=ft.Colors.BLUE_500),
                        title=ft.Text(
                            "Arquivos para Análise",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        subtitle=ft.Text(
                            f"Todos os arquivos de {self.pasta_base} são incluídos automaticamente. Desmarque os que não deseja analisar.",
                            color=ft.Colors.GREY_600
                        )
                    ),
                    ft.Divider(height=1),
                    
                    # Pasta de inspeção
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Pasta Base", size=14, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                self.txt_pasta_inspecao,
                                self.btn_carregar_automatico,
                                self.btn_refresh_stats
                            ], vertical_alignment=ft.CrossAxisAlignment.END)
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    ),
                    
                    # Estatísticas
                    ft.Container(
                        content=self.txt_folder_stats,
                        padding=ft.padding.symmetric(horizontal=15)
                    ),
                    
                    ft.Divider(height=1),
                    
                    # Controles de seleção
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Controles de Seleção", size=14, weight=ft.FontWeight.BOLD),
                            ft.Row([
                                self.btn_adicionar_arquivos,
                                self.btn_adicionar_pasta,
                                self.btn_limpar_selecao,
                                self.btn_desmarcar_todos
                            ], wrap=True),
                            self.contador_arquivos
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10)
                    ),
                    
                    # Lista de arquivos selecionados
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Arquivos para Análise (marque/desmarque)", 
                                   size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=self.lista_arquivos,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=8,
                                padding=10,
                                height=300
                            )
                        ]),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                        expand=True
                    )
                ]),
                padding=0
            ),
            elevation=2,
            margin=ft.margin.symmetric(vertical=5)
        )
    
    def _carregar_arquivos_automatico(self, e=None):
        """Carrega automaticamente todos os arquivos da pasta inspecao"""
        try:
            # ✅ CORREÇÃO: Criar pasta se não existir
            if not os.path.exists(self.pasta_base):
                os.makedirs(self.pasta_base, exist_ok=True)
                self.notifier.info(f"Pasta {self.pasta_base} criada")
                self.txt_folder_stats.value = f"Pasta {self.pasta_base} criada. Adicione arquivos para análise."
                if self.page:
                    self.page.update()
                return
            
            # ✅ CORREÇÃO: Verificar se o database service está disponível
            if not hasattr(self.notifier, 'database') or self.notifier.database is None:
                self.notifier.error("Serviço de banco de dados não disponível")
                return

            # Encontra todos os arquivos analisáveis na pasta inspecao
            todos_arquivos = []
            for root, dirs, files in os.walk(self.pasta_base):
                for file in files:
                    if self._is_arquivo_analisavel(file):
                        full_path = os.path.join(root, file)
                        todos_arquivos.append(full_path)

            # ✅ CORREÇÃO: Verificar se há arquivos
            if not todos_arquivos:
                self.notifier.warning(f"Nenhum arquivo analisável encontrado em {self.pasta_base}")
                self.txt_folder_stats.value = f"Nenhum arquivo analisável encontrado em {self.pasta_base}"
                if self.page:
                    self.page.update()
                return

            # Salva no banco de dados
            self.notifier.database.salvar_arquivos(todos_arquivos)
            
            # Carrega do banco (para garantir que temos o estado correto)
            self.arquivos_selecionados = self.notifier.database.obter_arquivos_selecionados()
            
            # Atualiza a lista visual
            self._atualizar_lista_arquivos()
            
            # Atualiza contador
            count = len(self.arquivos_selecionados)
            total = len(todos_arquivos)
            self.contador_arquivos.value = f"{count} de {total} arquivos selecionados"
            
            if self.page:
                self.page.update()
                
            self.notifier.success(f"Carregados {total} arquivos de {self.pasta_base}")
            self._atualizar_estatisticas()
            
        except Exception as ex:
            logger.error(f"Erro ao carregar arquivos automaticamente: {ex}")
            self.notifier.error(f"Erro ao carregar arquivos: {str(ex)}")
    
    def _atualizar_estatisticas(self, e=None):
        """Atualiza as estatísticas da pasta"""
        try:
            pasta = self.pasta_base
            if not os.path.exists(pasta):
                self.txt_folder_stats.value = "Pasta não encontrada"
                if self.page:
                    self.page.update()
                return
            
            # Conta arquivos recursivamente
            total_arquivos = 0
            extensoes = {}
            
            for root, dirs, files in os.walk(pasta):
                for file in files:
                    if self._is_arquivo_analisavel(file):
                        total_arquivos += 1
                        ext = os.path.splitext(file)[1].lower()
                        extensoes[ext] = extensoes.get(ext, 0) + 1
            
            # Formata estatísticas
            stats_text = f"Total: {total_arquivos} arquivos analisáveis"
            if extensoes:
                ext_text = ", ".join([f"{ext}: {count}" for ext, count in extensoes.items()])
                stats_text += f" | Extensões: {ext_text}"
            
            self.txt_folder_stats.value = stats_text
            
            if self.page:
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Erro ao atualizar estatísticas: {ex}")
            self.notifier.error(f"Erro ao atualizar estatísticas: {str(ex)}")
    
    def _selecionar_arquivos(self, e):
        """Abre seletor de arquivos para adicionar arquivos específicos"""
        try:
            if not self.file_picker:
                self.file_picker = ft.FilePicker(on_result=self._on_files_selected)
                if self.page:
                    self.page.overlay.append(self.file_picker)
                    self.page.update()
            
            if self.file_picker and self.page:
                self.file_picker.pick_files(
                    allow_multiple=True,
                    dialog_title="Adicionar arquivos à análise",
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=self._get_extensoes_permitidas()
                )
                
        except Exception as ex:
            logger.error(f"Erro ao selecionar arquivos: {ex}")
            self.notifier.error(f"Erro ao selecionar arquivos: {str(ex)}")
    
    def _selecionar_pasta(self, e):
        """Abre seletor de pasta para adicionar pasta específica"""
        try:
            if not self.folder_picker:
                self.folder_picker = ft.FilePicker(on_result=self._on_folder_selected)
                if self.page:
                    self.page.overlay.append(self.folder_picker)
                    self.page.update()
            
            if self.folder_picker and self.page:
                self.folder_picker.get_directory_path(
                    dialog_title="Adicionar pasta à análise"
                )
                
        except Exception as ex:
            logger.error(f"Erro ao selecionar pasta: {ex}")
            self.notifier.error(f"Erro ao selecionar pasta: {str(ex)}")
    
    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        """Callback quando arquivos são selecionados"""
        if e.files:
            novos_arquivos = [file.path for file in e.files]
            self._adicionar_arquivos_manualmente(novos_arquivos)
    
    def _on_folder_selected(self, e: ft.FilePickerResultEvent):
        """Callback quando pasta é selecionada"""
        if e.path:
            try:
                # Encontra todos os arquivos analisáveis na pasta
                arquivos = []
                for root, dirs, files in os.walk(e.path):
                    for file in files:
                        if self._is_arquivo_analisavel(file):
                            full_path = os.path.join(root, file)
                            arquivos.append(full_path)
                
                self._adicionar_arquivos_manualmente(arquivos)
                self.notifier.info(f"Pasta adicionada: {len(arquivos)} arquivos")
                
            except Exception as ex:
                logger.error(f"Erro ao processar pasta: {ex}")
                self.notifier.error(f"Erro ao processar pasta: {str(ex)}")
    
    def _adicionar_arquivos_manualmente(self, novos_arquivos: List[str]):
        """Adiciona arquivos manualmente à lista de seleção"""
        try:
            # Filtra arquivos válidos
            arquivos_adicionados = []
            for arquivo in novos_arquivos:
                if (self._is_arquivo_analisavel(arquivo) and 
                    os.path.exists(arquivo) and
                    arquivo not in self.arquivos_selecionados):
                    self.arquivos_selecionados.append(arquivo)
                    arquivos_adicionados.append(arquivo)
            
            if not arquivos_adicionados:
                self.notifier.info("Nenhum arquivo novo para adicionar")
                return
            
            # Salva no banco
            self.notifier.database.salvar_arquivos(self.arquivos_selecionados)
            
            # Atualiza a lista visual
            self._atualizar_lista_arquivos()
            
            # Atualiza contador
            count = len(self.arquivos_selecionados)
            self.contador_arquivos.value = f"{count} arquivo(s) selecionado(s)"
            
            if self.page:
                self.page.update()
                
            self.notifier.info(f"{len(arquivos_adicionados)} arquivo(s) adicionado(s)")
            
        except Exception as ex:
            logger.error(f"Erro ao adicionar arquivos: {ex}")
            self.notifier.error(f"Erro ao adicionar arquivos: {str(ex)}")
    
    def _atualizar_lista_arquivos(self):
        """Atualiza a lista visual de arquivos com checkboxes"""
        self.lista_arquivos.controls.clear()
        
        if not self.arquivos_selecionados:
            self.lista_arquivos.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=40, color=ft.Colors.GREY_400),
                        ft.Text("Clique em 'Carregar Todos os Arquivos' para começar", 
                               color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            return
        
        for i, arquivo in enumerate(sorted(self.arquivos_selecionados)):
            # Verifica se o arquivo está marcado (não está na lista de excluídos)
            arquivos_selecionados_db = self.notifier.database.obter_arquivos_selecionados()
            esta_marcado = arquivo in arquivos_selecionados_db
            
            checkbox = ft.Checkbox(
                value=esta_marcado,
                on_change=lambda e, idx=i: self._on_checkbox_change(e, idx)
            )
            
            item = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        checkbox,
                        ft.Icon(ft.Icons.CODE, size=20, color=ft.Colors.BLUE_400),
                        ft.Column([
                            ft.Text(os.path.basename(arquivo), 
                                   weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(arquivo, size=10, color=ft.Colors.GREY_600),
                        ], expand=True, spacing=2),
                    ]),
                    padding=8
                ),
                elevation=1,
                margin=ft.margin.symmetric(vertical=1)
            )
            self.lista_arquivos.controls.append(item)
    
    def _on_checkbox_change(self, e, index: int):
        """Callback quando checkbox é alterado"""
        try:
            if index < len(self.arquivos_selecionados):
                arquivo = self.arquivos_selecionados[index]
                
                # Atualiza no banco de dados
                self.notifier.database.atualizar_selecao_arquivo(arquivo, e.control.value)
                
                # Atualiza contador
                arquivos_selecionados = self.notifier.database.obter_arquivos_selecionados()
                count = len(arquivos_selecionados)
                total = len(self.arquivos_selecionados)
                self.contador_arquivos.value = f"{count} de {total} arquivos selecionados"
                
                if self.page:
                    self.page.update()
                    
                status = "selecionado" if e.control.value else "desmarcado"
                logger.debug(f"Arquivo {os.path.basename(arquivo)} {status}")
            else:
                logger.error(f"Índice inválido: {index}")
                
        except Exception as ex:
            logger.error(f"Erro ao alterar checkbox: {ex}")
    
    def _limpar_selecao(self, e):
        """Limpa todos os arquivos selecionados"""
        try:
            self.arquivos_selecionados.clear()
            # Limpa o banco também
            self.notifier.database.salvar_arquivos([])
            self._atualizar_lista_arquivos()
            self.contador_arquivos.value = "Nenhum arquivo selecionado"
            
            if self.page:
                self.page.update()
                
            self.notifier.info("Seleção de arquivos limpa")
            
        except Exception as ex:
            logger.error(f"Erro ao limpar seleção: {ex}")
            self.notifier.error(f"Erro ao limpar seleção: {str(ex)}")
    
    def _desmarcar_todos(self, e):
        """Desmarca todos os arquivos"""
        try:
            for arquivo in self.arquivos_selecionados:
                self.notifier.database.atualizar_selecao_arquivo(arquivo, False)
            
            self._atualizar_lista_arquivos()
            
            count = 0  # Todos desmarcados
            total = len(self.arquivos_selecionados)
            self.contador_arquivos.value = f"{count} de {total} arquivos selecionados"
            
            if self.page:
                self.page.update()
                
            self.notifier.info("Todos os arquivos desmarcados")
            
        except Exception as ex:
            logger.error(f"Erro ao desmarcar todos: {ex}")
            self.notifier.error(f"Erro ao desmarcar todos: {str(ex)}")
    
    def _is_arquivo_analisavel(self, arquivo: str) -> bool:
        """Verifica se o arquivo é analisável"""
        extensoes_analisaveis = {'.c', '.cpp', '.h', '.hpp', '.py', '.java', '.js', '.ts', '.cs', '.php', '.rb', '.go', '.rs', '.swift'}
        ext = os.path.splitext(arquivo)[1].lower()
        return ext in extensoes_analisaveis
    
    def _get_extensoes_permitidas(self) -> List[str]:
        """Retorna lista de extensões permitidas para o file picker"""
        return [ext.lstrip('.') for ext in self._get_extensoes_analisaveis()]
    
    def _get_extensoes_analisaveis(self) -> set:
        """Retorna conjunto de extensões analisáveis"""
        return {'.c', '.cpp', '.h', '.hpp', '.py', '.java', '.js', '.ts', '.cs', '.php', '.rb', '.go', '.rs', '.swift'}
    
    def get_arquivos_selecionados(self) -> List[str]:
        """Retorna a lista de arquivos selecionados do banco de dados"""
        try:
            return self.notifier.database.obter_arquivos_selecionados()
        except Exception as e:
            logger.error(f"Erro ao obter arquivos selecionados do banco: {e}")
            return []
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações da UI"""
        self.page = page
        # Inicializa os file pickers quando a página é definida
        self.file_picker = ft.FilePicker(on_result=self._on_files_selected)
        self.folder_picker = ft.FilePicker(on_result=self._on_folder_selected)
        if self.page:
            self.page.overlay.extend([self.file_picker, self.folder_picker])
        
        # ✅ CORREÇÃO: Carrega automaticamente os arquivos ao iniciar, mas com tratamento de erro
        try:
            self._carregar_arquivos_automatico()
        except Exception as e:
            logger.error(f"Erro ao carregar arquivos automaticamente na inicialização: {e}")
    
    def update(self):
        """Atualiza o componente"""
        try:
            # Atualiza a lista de arquivos se necessário
            if hasattr(self, 'lista_arquivos') and self.lista_arquivos.controls:
                self._atualizar_lista_arquivos()
        except Exception as e:
            logger.error(f"Erro ao atualizar FilesCard: {e}")

    def on_arquivos_selecionados(self, arquivos: list):
        """Callback quando arquivos são selecionados via notificação"""
        try:
            self.arquivos_selecionados = arquivos
            self._atualizar_lista_arquivos()
            count = len(arquivos)
            self.contador_arquivos.value = f"{count} arquivo(s) selecionado(s)"
            
            if self.page:
                self.page.update()
                
        except Exception as e:
            logger.error(f"Erro no callback on_arquivos_selecionados: {e}")

    def on_arquivos_processados(self, arquivos: list):
        """Callback quando arquivos são processados"""
        try:
            # Poderia atualizar a UI para mostrar quais arquivos foram processados
            self.notifier.info(f"{len(arquivos)} arquivos processados")
        except Exception as e:
            logger.error(f"Erro no callback on_arquivos_processados: {e}")

    def on_analise_completada(self, resultados: list):
        """Callback quando análise é completada"""
        try:
            # Atualiza estatísticas ou marca arquivos como processados
            sucessos = sum(1 for r in resultados if r.get('status') == 'sucesso')
            self.notifier.success(f"Análise completada: {sucessos} arquivos processados com sucesso")
        except Exception as e:
            logger.error(f"Erro no callback on_analise_completada: {e}")