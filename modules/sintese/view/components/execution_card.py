# ./modules/sintese/view/components/execution_card.py
import flet as ft

class ExecutionCard(ft.Card):
    def __init__(self, on_execute_callback, on_stop_callback):
        super().__init__()

        self.execute_button = ft.ElevatedButton(
            text="Executar Extração",
            icon=ft.Icons.PLAY_ARROW,
            on_click=on_execute_callback,
     
        )
    
        self.stop_button = ft.ElevatedButton(
            text="Parar",
            icon=ft.Icons.CANCEL,
            on_click=on_stop_callback,
            visible=False, # Começa invisível
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700
        )
        self.progress_bar = ft.ProgressBar(value=None, visible=False)

        self.content = ft.Container(
            padding=10,
            content=ft.Column(
                [
                    ft.Stack([self.execute_button, self.stop_button]), # Bota um em cima do outro
                    self.progress_bar
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

    def set_busy(self, is_busy: bool):
        self.progress_bar.visible = is_busy
        self.execute_button.visible = not is_busy
        self.stop_button.visible = is_busy
        self.update()