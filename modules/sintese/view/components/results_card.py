# ./modules/sintese/view/components/results_card.py
import flet as ft
import os
import io
import zipfile
import shutil
import logging
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class ResultsCard(ft.Card):
    def __init__(self, page: ft.Page, notifier: NotificationService):
        super().__init__(visible=False)
        self.page = page
        self.notifier = notifier
        self.all_files = []
        
        self.pending_single_download_path = None
        self.pending_zip_bytes = None
        
        self.save_picker = ft.FilePicker(on_result=self._on_save_result)
        self.page.overlay.append(self.save_picker)


        self.filter_tf = ft.TextField(
            label="Filtrar arquivos...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._filter_changed
        )
        self.results_dt = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Arquivo Extraído")),
                ft.DataColumn(ft.Text("Ação"), numeric=True),
            ],
            rows=[],
            expand=True,
        )
        self.content = ft.Container(
            padding=15,
            content=ft.Column(
                controls=[
                    ft.Text("Resultados da Extração", style=ft.TextThemeStyle.TITLE_MEDIUM),
                    self.filter_tf,
                    ft.Row([
                        ft.ElevatedButton(
                            "Baixar Todos (.zip)",
                            icon=ft.Icons.ARCHIVE_OUTLINED,
                            on_click=self._download_all_zip
                        ),
                    ]),
                    ft.Container(
                        content=self.results_dt,
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        border_radius=ft.border_radius.all(5),
                        expand=True,
                        height=400,
                    )
                ],
                expand=True
            )
        )

    def populate_results(self, files: list):

        self.all_files = sorted(files)
        self.results_dt.rows.clear()
        if not files:
            self.results_dt.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("Nenhum arquivo JSON foi gerado.")), ft.DataCell(ft.Text(""))]))
        else:
            for file_path in self.all_files:
                self.results_dt.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(os.path.basename(file_path), data=file_path)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                tooltip="Baixar este arquivo",
                                data=file_path,
                                on_click=self._download_selected
                            )
                        ),
                    ])
                )
        self.visible = True
        self.page.update()

    def _filter_changed(self, e):

        search_term = self.filter_tf.value.lower()
        for row in self.results_dt.rows:
            file_name = row.cells[0].content.value.lower()
            row.visible = search_term in file_name
        self.page.update()

    def _download_selected(self, e):
        try:
            self.notifier.notify('log_message', "Botão 'Baixar Arquivo' clicado. Preparando...", "INFO")
            file_path = e.control.data
            if os.path.exists(file_path):
                self.pending_single_download_path = file_path
                self.pending_zip_bytes = None
                
                self.notifier.notify('log_message', "Enviando comando para abrir o diálogo 'Salvar Como...'", "INFO")
                self.save_picker.save_file(
                    dialog_title="Salvar Arquivo",
                    file_name=os.path.basename(file_path)
                )
        except Exception as ex:
            logger.error(f"Erro ao preparar download de arquivo único: {ex}", exc_info=True)
            self.notifier.notify('log_message', f"Erro ao preparar download: {ex}", "ERROR")

    def _download_all_zip(self, e):
        if not self.all_files: return
        try:
            self.notifier.notify('log_message', "Botão 'Baixar Todos' clicado. Gerando ZIP...", "INFO")
            memory_zip = io.BytesIO()
            with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in self.all_files:
                    if os.path.exists(file_path):
                        zf.write(file_path, os.path.basename(file_path))
            
            self.pending_zip_bytes = memory_zip.getvalue()
            self.pending_single_download_path = None

            self.notifier.notify('log_message', "Enviando comando para abrir o diálogo 'Salvar Como...'", "INFO")
            self.save_picker.save_file(
                dialog_title="Salvar Arquivo ZIP",
                file_name="extracao_grafos.zip",
            )
        except Exception as ex:
            logger.error(f"Erro ao criar arquivo ZIP: {ex}", exc_info=True)
            self.notifier.notify('log_message', f"Erro ao criar arquivo ZIP: {ex}", "ERROR")

    def _on_save_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            self.notifier.notify('log_message', "Download cancelado pelo usuário.", "WARNING")
            return

        save_path = e.path
        self.notifier.notify('log_message', f"Diálogo fechado. Salvando arquivo em: {save_path}", "INFO")
        try:
            if self.pending_zip_bytes:
                with open(save_path, "wb") as f:
                    f.write(self.pending_zip_bytes)
            
            elif self.pending_single_download_path:
                shutil.copy2(self.pending_single_download_path, save_path)
            
            self.notifier.notify('log_message', f"Arquivo salvo com sucesso!", "INFO")

        except Exception as ex:
            logger.error(f"Falha ao salvar o arquivo em disco: {ex}", exc_info=True)
            self.notifier.notify('log_message', f"Falha ao salvar o arquivo: {ex}", "ERROR")
        finally:
            self.pending_single_download_path = None
            self.pending_zip_bytes = None