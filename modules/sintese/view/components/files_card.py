# ./modules/sintese/view/components/files_card.py
import flet as ft
import os

class FilesCard(ft.Card):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        
        # --- Lógica para encontrar o caminho padrão e suas estatísticas ---
        default_path = ""
        default_stats = ""
        explicabilidade_path = r"C:\Users\wmlim\Downloads\Projetos\analisador\explicabilidade"
        
        if os.path.exists(explicabilidade_path) and os.path.isdir(explicabilidade_path):
            default_path = os.path.abspath(explicabilidade_path)
            # Chama a nova função para obter as estatísticas do diretório padrão
            default_stats = self._get_path_stats(default_path)
        
        self.selected_path = default_path
        
        # --- Definição dos Controles da UI ---
        
        self.path_textfield = ft.TextField(
            label="Caminho do Arquivo ou Pasta",
            value=default_path,
            helper_text=default_stats,  # Exibe a contagem inicial aqui
            expand=True,
            read_only=False,  # Permite edição direta
            on_submit=self.on_path_submitted  # Adiciona callback para Enter
        )
        
        self.file_picker = ft.FilePicker(on_result=self.on_dialog_result)
        self.page.overlay.append(self.file_picker)

        # --- Constrói o Conteúdo do Card ---
        
        self.content = ft.Container(
            padding=10,
            content=ft.Column([
                ft.Text("Seleção de Entrada", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Row([
                    self.path_textfield,
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        tooltip="Selecionar Pasta",
                        on_click=lambda _: self.file_picker.get_directory_path(dialog_title="Selecione a pasta de entrada")
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ATTACH_FILE,
                        tooltip="Selecionar Arquivo",
                        on_click=lambda _: self.file_picker.pick_files(dialog_title="Selecione o arquivo .txt", allowed_extensions=["txt"])
                    )
                ]),
            ])
        )

    def _get_path_stats(self, directory_path: str) -> str:
        """
        Conta os arquivos e subdiretórios no primeiro nível de um caminho.
        Retorna uma string formatada com a contagem.
        """
        if not directory_path or not os.path.isdir(directory_path):
            return ""
        try:
            items = os.listdir(directory_path)
            # Conta apenas os arquivos .txt para ser mais relevante
            file_count = sum(1 for item in items if item.endswith('.txt') and os.path.isfile(os.path.join(directory_path, item)))
            dir_count = sum(1 for item in items if os.path.isdir(os.path.join(directory_path, item)))
            
            # Formata a mensagem de forma amigável
            file_plural = "arquivo .txt" if file_count == 1 else "arquivos .txt"
            dir_plural = "subpasta" if dir_count == 1 else "subpastas"

            return f"Contém {file_count} {file_plural} e {dir_count} {dir_plural}."
            
        except OSError:
            # Lida com possíveis erros de permissão de acesso
            return "Não foi possível ler o conteúdo do diretório."

    def on_dialog_result(self, e: ft.FilePickerResultEvent):
        """
        Callback chamado quando o usuário seleciona um arquivo ou pasta.
        Atualiza o campo de texto e a contagem de itens.
        """
        path = ""
        stats = ""
        
        if e.files and len(e.files) > 0:
            path = e.files[0].path
        elif e.path:
            path = e.path
        
        if path:
            self.selected_path = path
            self.path_textfield.value = path
            
            if os.path.isdir(path):
                stats = self._get_path_stats(path)
            elif os.path.isfile(path):
                stats = "1 arquivo selecionado."
            
            self.path_textfield.helper_text = stats
            self.update()
    
    def on_path_submitted(self, e):
        """
        Callback chamado quando o usuário pressiona Enter no campo de caminho.
        """
        path = e.control.value.strip()
        if path:
            self.selected_path = path
            stats = ""

            if os.path.isdir(path):
                stats = self._get_path_stats(path)
            elif os.path.isfile(path):
                stats = "1 arquivo selecionado."
            else:
                stats = "Caminho não encontrado."

            self.path_textfield.helper_text = stats
            self.update()

    def get_selected_path(self) -> str:
        return self.selected_path