# modules/auth/view/login_component.py
import flet as ft
import logging

logger = logging.getLogger(__name__)

class LoginComponent:
    def __init__(self, auth_service, on_login_success):
        self.auth_service = auth_service
        self.on_login_success = on_login_success
        self.page = None
        
        # Campos do formulário
        self.username_field = ft.TextField(
            label="Usuário",
            prefix_icon=ft.Icons.PERSON,
            width=300,
            autofocus=True
        )
        
        self.password_field = ft.TextField(
            label="Senha",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        self.login_button = ft.ElevatedButton(
            "Entrar",
            icon=ft.Icons.LOGIN,
            on_click=self._login,
            width=300
        )
        
        self.status_text = ft.Text(
            "",
            color=ft.Colors.RED_600,
            size=12
        )
        
        self.progress_ring = ft.ProgressRing(
            visible=False,
            width=20,
            height=20
        )
    
    def build(self) -> ft.Container:
        """Constrói o componente de login"""
        return ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SECURITY, size=48, color=ft.Colors.BLUE_700),
                        ft.Text("Sistema de Análise de Código", 
                               size=24, 
                               weight=ft.FontWeight.BOLD,
                               color=ft.Colors.BLUE_700),
                        ft.Text("Faça login para continuar",
                               size=14,
                               color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20
                ),
                
                ft.Divider(),
                
                # Formulário de login
                ft.Container(
                    content=ft.Column([
                        self.username_field,
                        self.password_field,
                        
                        ft.Container(height=10),
                        
                        ft.Row([
                            self.login_button,
                            self.progress_ring
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        
                        ft.Container(height=10),
                        
                        self.status_text,
                        
                        # Link para criar conta (opcional)
                        ft.TextButton(
                            "Primeiro acesso? Criar conta",
                            icon=ft.Icons.PERSON_ADD,
                            on_click=self._show_create_account
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            
            # Centraliza na tela
            alignment=ft.alignment.center,
            expand=True
        )
    
    def _login(self, e):
        """Processa o login"""
        username = self.username_field.value.strip()
        password = self.password_field.value
        
        if not username or not password:
            self.status_text.value = "Preencha todos os campos"
            self.status_text.color = ft.Colors.RED_600
            if self.page:
                self.page.update()
            return
        
        # Mostra loading
        self.login_button.disabled = True
        self.progress_ring.visible = True
        self.status_text.value = "Autenticando..."
        self.status_text.color = ft.Colors.BLUE_600
        if self.page:
            self.page.update()
        
        # Realiza login
        success, message, session_data = self.auth_service.login(username, password)
        
        if success:
            self.status_text.value = "Login bem-sucedido!"
            self.status_text.color = ft.Colors.GREEN_600
            
            # Chama callback de sucesso
            if self.on_login_success:
                self.on_login_success(session_data)
        else:
            self.status_text.value = message
            self.status_text.color = ft.Colors.RED_600
        
        # Restaura UI
        self.login_button.disabled = False
        self.progress_ring.visible = False
        
        if self.page:
            self.page.update()
    
    def _show_create_account(self, e):
        """Mostra diálogo para criar conta"""
        if not self.page:
            return
            
        def create_account(e):
            username = create_username_field.value.strip()
            password = create_password_field.value
            confirm_password = confirm_password_field.value
            
            if not username or not password:
                show_error("Preencha todos os campos")
                return
                
            if password != confirm_password:
                show_error("Senhas não coincidem")
                return
            
            success, message = self.auth_service.create_user(username, password)
            
            if success:
                self.page.dialog.open = False
                self.username_field.value = username
                self.password_field.value = ""
                self.status_text.value = "Conta criada com sucesso! Faça login."
                self.status_text.color = ft.Colors.GREEN_600
            else:
                show_error(message)
            
            self.page.update()
        
        def show_error(message: str):
            error_text.value = message
            self.page.update()
        
        # Campos do diálogo
        create_username_field = ft.TextField(
            label="Novo usuário",
            prefix_icon=ft.Icons.PERSON,
            width=300
        )
        
        create_password_field = ft.TextField(
            label="Senha",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        confirm_password_field = ft.TextField(
            label="Confirmar senha",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        error_text = ft.Text(
            "",
            color=ft.Colors.RED_600,
            size=12
        )
        
        # Diálogo
        create_account_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Criar Nova Conta"),
            content=ft.Column([
                create_username_field,
                create_password_field,
                confirm_password_field,
                error_text
            ], width=400, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(self.page.dialog, "open", False)),
                ft.ElevatedButton("Criar Conta", on_click=create_account)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = create_account_dialog
        self.page.dialog.open = True
        self.page.update()
    
    def set_page(self, page: ft.Page):
        """Define a página para atualizações"""
        self.page = page