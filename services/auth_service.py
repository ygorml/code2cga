# services/auth_service.py
import hashlib
import secrets
import logging
from typing import Dict, Optional, Tuple
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, users_file: str = "storage/users.json"):
        self.users_file = users_file
        self.sessions = {}  # session_id -> user_data
        self._load_users()
    
    def _load_users(self):
        """Carrega usuários do arquivo JSON"""
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                # Usuário admin padrão
                self.users = {
                    "mestre": {
                        "password_hash": self._hash_password("mestrado2025!$%"),
                        "role": "mestre",
                        "created_at": datetime.now().isoformat(),
                        "last_login": None
                    }
                }
                self._save_users()
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            self.users = {}
    
    def _save_users(self):
        """Salva usuários no arquivo JSON"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Gera hash SHA-256 da senha CORRETAMENTE"""
        # ✅ CORREÇÃO: encode para bytes antes de fazer hash
        password_bytes = password.encode('utf-8')
        return hashlib.sha256(password_bytes).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica se a senha corresponde ao hash"""
        try:
            # ✅ CORREÇÃO: Usar o mesmo método de hash para comparação
            return self._hash_password(password) == password_hash
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Realiza login do usuário"""
        try:
            if username not in self.users:
                logger.warning(f"Tentativa de login com usuário inexistente: {username}")
                return False, "Usuário não encontrado", None
            
            user_data = self.users[username]
            
            if not self.verify_password(password, user_data["password_hash"]):
                logger.warning(f"Senha incorreta para usuário: {username}")
                return False, "Senha incorreta", None
            
            # Atualiza último login
            user_data["last_login"] = datetime.now().isoformat()
            self._save_users()
            
            # Cria sessão
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {
                "username": username,
                "role": user_data["role"],
                "login_time": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            logger.info(f"Login bem-sucedido para usuário: {username}")
            return True, "Login bem-sucedido", {
                "session_id": session_id,
                "user": {
                    "username": username,
                    "role": user_data["role"]
                }
            }
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False, f"Erro interno: {str(e)}", None
    
    def verify_session(self, session_id: str) -> Tuple[bool, Optional[Dict]]:
        """Verifica se uma sessão é válida"""
        try:
            if session_id not in self.sessions:
                return False, None
            
            session = self.sessions[session_id]
            expires_at = datetime.fromisoformat(session["expires_at"])
            
            if datetime.now() > expires_at:
                # Sessão expirada
                del self.sessions[session_id]
                return False, None
            
            return True, session
            
        except Exception as e:
            logger.error(f"Erro ao verificar sessão: {e}")
            return False, None
    
    def logout(self, session_id: str) -> bool:
        """Realiza logout do usuário"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info("Logout realizado com sucesso")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro no logout: {e}")
            return False
    
    def create_user(self, username: str, password: str, role: str = "user") -> Tuple[bool, str]:
        """Cria um novo usuário"""
        try:
            if username in self.users:
                return False, "Usuário já existe"
            
            if len(password) < 6:
                return False, "Senha deve ter pelo menos 6 caracteres"
            
            self.users[username] = {
                "password_hash": self._hash_password(password),
                "role": role,
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            
            self._save_users()
            logger.info(f"Novo usuário criado: {username}")
            return True, "Usuário criado com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return False, f"Erro interno: {str(e)}"
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Altera a senha do usuário"""
        try:
            if username not in self.users:
                return False, "Usuário não encontrado"
            
            if not self.verify_password(old_password, self.users[username]["password_hash"]):
                return False, "Senha atual incorreta"
            
            if len(new_password) < 6:
                return False, "Nova senha deve ter pelo menos 6 caracteres"
            
            self.users[username]["password_hash"] = self._hash_password(new_password)
            self._save_users()
            
            logger.info(f"Senha alterada para usuário: {username}")
            return True, "Senha alterada com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            return False, f"Erro interno: {str(e)}"
    
    def get_user_stats(self) -> Dict:
        """Retorna estatísticas dos usuários"""
        return {
            "total_users": len(self.users),
            "active_sessions": len(self.sessions),
            "users": list(self.users.keys())
        }