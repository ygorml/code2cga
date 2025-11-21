# modules/auth/controller.py
import logging
from services.auth_service import AuthService
from modules.auth.view.login_component import LoginComponent
"""
Controller de autenticação.

Gerencia o login, logout e controle de sessão de usuários.
"""


logger = logging.getLogger(__name__)

class AuthController:
    def __init__(self, notifier):
        self.auth_service = AuthService()
        self.notifier = notifier
        self.current_user = None
        self.session_id = None
        self.is_authenticated = False
        
    def get_login_component(self, on_login_success) -> LoginComponent:
        """Retorna o componente de login"""
        return LoginComponent(self.auth_service, on_login_success)
    
    def login(self, username: str, password: str) -> bool:
        """Realiza login"""
        success, message, session_data = self.auth_service.login(username, password)
        
        if success:
            self.current_user = session_data["user"]
            self.session_id = session_data["session_id"]
            self.is_authenticated = True
            self.notifier.success(message)
            logger.info(f"Usuário autenticado: {username}")
        else:
            self.notifier.error(message)
            logger.warning(f"Falha no login: {username} - {message}")
        
        return success
    
    def logout(self):
        """Realiza logout"""
        if self.session_id:
            self.auth_service.logout(self.session_id)
        
        self.current_user = None
        self.session_id = None
        self.is_authenticated = False
        self.notifier.info("Logout realizado com sucesso")
        logger.info("Usuário deslogado")
    
    def verify_session(self) -> bool:
        """Verifica se a sessão atual é válida"""
        if not self.session_id:
            return False
        
        valid, session = self.auth_service.verify_session(self.session_id)
        
        if valid:
            self.current_user = {
                "username": session["username"],
                "role": session["role"]
            }
            self.is_authenticated = True
            return True
        else:
            self.is_authenticated = False
            return False
    
    def get_current_user(self):
        """Retorna dados do usuário atual"""
        return self.current_user
    
    def has_permission(self, required_role: str) -> bool:
        """Verifica se usuário tem permissão"""
        if not self.is_authenticated or not self.current_user:
            return False
        
        user_role = self.current_user.get("role", "user")
        
        # Hierarquia de roles
        role_hierarchy = {
            "admin": 3,
            "moderator": 2, 
            "user": 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Cria novo usuário (apenas admin)"""
        if not self.has_permission("admin"):
            self.notifier.error("Permissão negada")
            return False
        
        success, message = self.auth_service.create_user(username, password, role)
        
        if success:
            self.notifier.success(message)
        else:
            self.notifier.error(message)
        
        return success
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Altera senha do usuário atual"""
        if not self.is_authenticated:
            self.notifier.error("Usuário não autenticado")
            return False
        
        username = self.current_user["username"]
        success, message = self.auth_service.change_password(username, old_password, new_password)
        
        if success:
            self.notifier.success(message)
        else:
            self.notifier.error(message)
        
        return success