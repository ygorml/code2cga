# middleware/auth_middleware.py
import logging
from functools import wraps
from modules.auth.controller import AuthController

logger = logging.getLogger(__name__)

def login_required(required_role: str = "user"):
    """Decorator para exigir autenticação"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # O primeiro argumento é geralmente 'self' (controller)
            self = args[0]
            
            # Verifica se o controller tem auth_controller
            if hasattr(self, 'auth_controller'):
                auth_controller = self.auth_controller
                
                if not auth_controller.is_authenticated:
                    logger.warning("Acesso negado: usuário não autenticado")
                    if hasattr(self, 'notifier'):
                        self.notifier.error("Faça login para acessar esta funcionalidade")
                    return None
                
                if not auth_controller.has_permission(required_role):
                    logger.warning(f"Acesso negado: permissão insuficiente para {required_role}")
                    if hasattr(self, 'notifier'):
                        self.notifier.error("Permissão insuficiente")
                    return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def public_endpoint(func):
    """Decorator para endpoints públicos (sem autenticação)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper