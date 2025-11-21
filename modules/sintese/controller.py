# ./modules/sintese/controller.py
import logging
import threading
from .model import SinteseModel
from services.notification_service import NotificationService
"""
Controller do módulo de síntese.

Gerencia a geração de sínteses e resumos dos resultados da análise.
"""


logger = logging.getLogger(__name__)

class SinteseController:
    def __init__(self, model: SinteseModel, notifier: NotificationService):
        self.model = model
        self.notifier = notifier
        self.stop_event = threading.Event() # NOVO: Evento para sinalizar parada

    def handle_sintese_execution(self, caminho_entrada, secao_alvo, metodo_busca, limiar_similaridade):
        if not caminho_entrada:
            self.notifier.notify('log_message', "O caminho de entrada não foi definido.", "ERROR")
            return

        self.stop_event.clear() # Garante que o sinal de parada está resetado
        logger.info(f"Agendando execução da extração para o caminho: {caminho_entrada}")
        
        thread = threading.Thread(
            target=self.model.extrair_json_de_txt,
            args=(caminho_entrada, secao_alvo, metodo_busca, limiar_similaridade, self.stop_event)
        )
        thread.start()
        
    def handle_sintese_cancellation(self):
        """Sinaliza para a thread de extração que ela deve parar."""
        logger.warning("Sinal de parada enviado para a tarefa de extração.")
        self.stop_event.set()