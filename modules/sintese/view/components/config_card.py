# ./modules/sintese/view/components/config_card.py
import flet as ft

class ConfigCard(ft.Card):
    def __init__(self):
        super().__init__()
        
        # --- Define os Controles como Atributos da Classe ---
        
        self.target_section_tf = ft.TextField(
            label="Seção Alvo no arquivo .txt",
            # CORREÇÃO: Adicionado o ":" para corresponder exatamente ao formato do arquivo
            value="SEÇÃO 1: FORMATO OBRIGATÓRIO DO GRAFO JSON"
        )
        
        self.search_method_dd = ft.Dropdown(
            label="Método de Busca",
            value="flexivel",
            options=[
                ft.dropdown.Option(key="flexivel", text="Busca Flexível (Rápida)"),
                ft.dropdown.Option(key="similaridade", text="Similaridade de Texto (Precisa)"),
            ],
            on_change=self._toggle_slider,
            expand=1,
        )
        
        self.similarity_slider = ft.Slider(
            min=0.1, 
            max=1.0, 
            divisions=9, 
            value=0.7, 
            label="Limiar: {value}",
            disabled=True,
            expand=2,
        )

        # --- Constrói o Conteúdo do Card ---

        self.content = ft.Container(
            padding=10,
            content=ft.Column([
                ft.Text("Configurações da Extração", style=ft.TextThemeStyle.TITLE_MEDIUM),
                self.target_section_tf,
                ft.Row(
                    controls=[
                        self.search_method_dd, 
                        self.similarity_slider
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ])
        )

    def _toggle_slider(self, e):
        is_similar = self.search_method_dd.value == "similaridade"
        self.similarity_slider.disabled = not is_similar
        self.update()

    def get_target_section(self) -> str:
        return self.target_section_tf.value

    def get_search_method(self) -> str:
        return self.search_method_dd.value
    
    def get_similarity_threshold(self) -> float:
        return self.similarity_slider.value