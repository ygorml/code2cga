import logging
import flet as ft
from typing import Callable, Any
import threading
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Um serviço simples de publicação/inscrição para desacoplar componentes.
    Implementa o padrão Observer (Pub/Sub).
    """
    def __init__(self):
        self._subscribers = {}
        self._page = None
        self._snack_bar = None
        self.database = DatabaseService()
        self._background_tasks = {}  # Para controlar tarefas em background
        logger.info("NotificationService instanciado.")

    def set_page(self, page: ft.Page):
        """Define a página para exibir notificações"""
        self._page = page
        self._snack_bar = ft.SnackBar(
            content=ft.Text(""),
            action="OK",
            duration=4000
        )

    def subscribe(self, event_type: str, callback):
        """Inscreve um callback para um tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Novo inscrito para o evento '{event_type}': {callback.__name__}")

    def notify(self, event_type: str, *args, **kwargs):
        """Notifica todos os inscritos sobre um evento."""
        if event_type in self._subscribers:
            logger.debug(f"Notificando evento '{event_type}' com args: {args}, kwargs: {kwargs}")
            for callback in self._subscribers[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Erro ao executar callback para o evento '{event_type}': {e}", exc_info=True)

    # Métodos auxiliares para notificações comuns
    def info(self, message: str):
        """Exibe uma notificação informativa"""
        self._show_snackbar(message, ft.Colors.BLUE)

    def success(self, message: str):
        """Exibe uma notificação de sucesso"""
        self._show_snackbar(message, ft.Colors.GREEN)

    def error(self, message: str):
        """Exibe uma notificação de erro"""
        self._show_snackbar(message, ft.Colors.RED)

    def warning(self, message: str):
        """Exibe uma notificação de aviso"""
        self._show_snackbar(message, ft.Colors.ORANGE)

    def _show_snackbar(self, message: str, color: str):
        """Exibe uma SnackBar com a mensagem e cor especificadas"""
        if self._page and hasattr(self._page, 'add'):
            logger.info(f"Notificação: {message}")
            
            # Também envia para o sistema de logs da UI se disponível
            if hasattr(self, '_subscribers') and 'log_info' in self._subscribers:
                self.notify('log_info', message)
                
            # Cria uma nova SnackBar para cada mensagem
            snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color,
                action="OK",
                duration=4000
            )
            
            # Adiciona à página e atualiza
            self._page.add(snack_bar)
            self._page.update()
        else:
            logger.info(f"Notificação (sem página): {message}")

    # Métodos para gerenciar tarefas em background
    def register_background_task(self, task_id: str, task: threading.Thread):
        """Registra uma tarefa em background"""
        self._background_tasks[task_id] = {
            'thread': task,
            'paused': False,
            'stopped': False
        }
        logger.info(f"Tarefa em background registrada: {task_id}")

    def pause_background_task(self, task_id: str):
        """Pausa uma tarefa em background"""
        if task_id in self._background_tasks:
            self._background_tasks[task_id]['paused'] = True
            logger.info(f"Tarefa pausada: {task_id}")

    def resume_background_task(self, task_id: str):
        """Retoma uma tarefa em background"""
        if task_id in self._background_tasks:
            self._background_tasks[task_id]['paused'] = False
            logger.info(f"Tarefa retomada: {task_id}")

    def stop_background_task(self, task_id: str):
        """Para uma tarefa em background"""
        if task_id in self._background_tasks:
            self._background_tasks[task_id]['stopped'] = True
            logger.info(f"Tarefa parada: {task_id}")

    def is_task_paused(self, task_id: str) -> bool:
        """Verifica se uma tarefa está pausada"""
        return self._background_tasks.get(task_id, {}).get('paused', False)

    def is_task_stopped(self, task_id: str) -> bool:
        """Verifica se uma tarefa foi parada"""
        return self._background_tasks.get(task_id, {}).get('stopped', False)

    def get_active_tasks(self) -> list:
        """Retorna lista de tarefas ativas"""
        return [task_id for task_id, task_info in self._background_tasks.items() 
                if task_info['thread'].is_alive() and not task_info['stopped']]