# modules/dashboard/view/components/metricas_card.py

import flet as ft
import logging

logger = logging.getLogger(__name__)

class MetricasCard:
    def __init__(self, controller, notifier):
        self.controller = controller
        self.notifier = notifier
        self.page = None
        
    def build(self) -> ft.Card:
        self.grid_metricas = ft.GridView(
            expand=1,
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=1.2,
            spacing=10,
            run_spacing=10,
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.GREEN_500),
                        title=ft.Text("Métricas de Arquitetura", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text("Indicadores de qualidade e complexidade")
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.grid_metricas,
                        padding=15,
                        height=300
                    )
                ]),
                padding=10
            ),
            width=400
        )
    
    def atualizar_metricas(self, metricas):
        """Atualiza o grid de métricas"""
        self.grid_metricas.controls.clear()
        
        if not metricas:
            self.grid_metricas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.WARNING, size=30, color=ft.Colors.ORANGE),
                        ft.Text("Nenhuma métrica", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("Execute a análise", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                    alignment=ft.alignment.center
                )
            )
            return
        
        metricas_display = [
            ("Acoplamento", f"{getattr(metricas, 'acoplamento_medio', 0):.2f}", ft.Icons.LINK, 
             self._get_cor_metrica(getattr(metricas, 'acoplamento_medio', 0), 0.3, 0.7)),
            
            ("Coesão", f"{getattr(metricas, 'coesao_media', 0):.2f}", ft.Icons.GROUP_WORK,
             self._get_cor_metrica(getattr(metricas, 'coesao_media', 0), 0.6, 0.8, invertido=True)),
            
            ("Modularidade", f"{getattr(metricas, 'modularidade', 0):.3f}", ft.Icons.VIEW_MODULE,
             self._get_cor_metrica(getattr(metricas, 'modularidade', 0), 0.3, 0.6)),
            
            ("Densidade", f"{getattr(metricas, 'densidade', 0):.3f}", ft.Icons.DENSITY_MEDIUM,
             self._get_cor_metrica(getattr(metricas, 'densidade', 0), 0.1, 0.3)),
            
            ("Complexidade", f"{getattr(metricas, 'complexidade_ciclomatica_media', 0):.1f}", ft.Icons.CODE,
             self._get_cor_metrica(getattr(metricas, 'complexidade_ciclomatica_media', 0), 10, 20, invertido=True)),
            
            ("Componentes", str(getattr(metricas, 'numero_componentes', 0)), ft.Icons.ACCOUNT_TREE,
             ft.Colors.BLUE_400),
        ]
        
        for nome, valor, icone, cor in metricas_display:
            self.grid_metricas.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(icone, size=30, color=cor),
                        ft.Text(valor, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(nome, size=12, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                    border_radius=8,
                    bgcolor=self._get_cor_fundo(cor),
                    border=ft.border.all(2, cor)
                )
            )
        
        if self.page:
            self.page.update()
    
    def _get_cor_metrica(self, valor: float, bom: float, otimo: float, invertido: bool = False) -> str:
        """Retorna cor baseada no valor da métrica"""
        if invertido:
            if valor <= bom: return ft.Colors.GREEN
            elif valor <= otimo: return ft.Colors.ORANGE
            else: return ft.Colors.RED
        else:
            if valor >= otimo: return ft.Colors.GREEN
            elif valor >= bom: return ft.Colors.ORANGE  
            else: return ft.Colors.RED
    
    def _get_cor_fundo(self, cor: str) -> str:
        """Retorna cor de fundo suave baseada na cor principal"""
        cores_fundo = {
            ft.Colors.GREEN: ft.Colors.GREEN_50,
            ft.Colors.ORANGE: ft.Colors.ORANGE_50, 
            ft.Colors.RED: ft.Colors.RED_50,
            ft.Colors.BLUE_400: ft.Colors.BLUE_50
        }
        return cores_fundo.get(cor, ft.Colors.GREY_50)
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page