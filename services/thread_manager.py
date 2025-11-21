import threading
import time
import logging
from typing import Callable, Any, Dict, List
from queue import Queue, Empty

logger = logging.getLogger(__name__)

class ThreadManager:
    """
    Gerenciador de threads para executar tarefas em background
    com controle de pausa, retomada e parada.
    """
    
    def __init__(self, notifier):
        self.notifier = notifier
        self.tasks: Dict[str, Dict] = {}
        self.task_queue = Queue()
        self.worker_thread = None
        self.running = False
        
    def start(self):
        """Inicia o gerenciador de threads"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("ThreadManager iniciado")
        
    def stop(self):
        """Para o gerenciador de threads"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        logger.info("ThreadManager parado")
        
    def submit_task(self, task_id: str, task_func: Callable, 
                   callback: Callable = None, *args, **kwargs) -> bool:
        """Submete uma tarefa para execução em background"""
        if task_id in self.tasks:
            logger.warning(f"Tarefa {task_id} já existe")
            return False
            
        self.tasks[task_id] = {
            'func': task_func,
            'callback': callback,
            'args': args,
            'kwargs': kwargs,
            'status': 'pending',  # pending, running, paused, completed, stopped
            'result': None,
            'error': None,
            'thread': None
        }
        
        self.task_queue.put(('start', task_id))
        logger.info(f"Tarefa {task_id} submetida para execução")
        return True
        
    def pause_task(self, task_id: str) -> bool:
        """Pausa uma tarefa"""
        if task_id in self.tasks and self.tasks[task_id]['status'] == 'running':
            self.tasks[task_id]['status'] = 'paused'
            self.task_queue.put(('pause', task_id))
            logger.info(f"Tarefa {task_id} pausada")
            return True
        return False
        
    def resume_task(self, task_id: str) -> bool:
        """Retoma uma tarefa pausada"""
        if task_id in self.tasks and self.tasks[task_id]['status'] == 'paused':
            self.tasks[task_id]['status'] = 'running'
            self.task_queue.put(('resume', task_id))
            logger.info(f"Tarefa {task_id} retomada")
            return True
        return False
        
    def stop_task(self, task_id: str) -> bool:
        """Para uma tarefa"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'stopped'
            self.task_queue.put(('stop', task_id))
            logger.info(f"Tarefa {task_id} parada")
            return True
        return False
        
    def get_task_status(self, task_id: str) -> str:
        """Retorna o status de uma tarefa"""
        return self.tasks.get(task_id, {}).get('status', 'unknown')
        
    def get_active_tasks(self) -> List[str]:
        """Retorna lista de tarefas ativas"""
        return [task_id for task_id, task_info in self.tasks.items() 
                if task_info['status'] in ['pending', 'running', 'paused']]
                
    def _worker_loop(self):
        """Loop principal do worker que processa tarefas"""
        while self.running:
            try:
                # Processa comandos da fila
                try:
                    command, task_id = self.task_queue.get(timeout=1)
                except Empty:
                    continue
                    
                if command == 'start':
                    self._start_task(task_id)
                elif command == 'pause':
                    self._pause_task(task_id)
                elif command == 'resume':
                    self._resume_task(task_id)
                elif command == 'stop':
                    self._stop_task(task_id)
                    
            except Exception as e:
                logger.error(f"Erro no worker loop: {e}")
                
    def _start_task(self, task_id: str):
        """Inicia uma tarefa em thread separada"""
        if task_id not in self.tasks:
            return
            
        task_info = self.tasks[task_id]
        
        def task_wrapper():
            try:
                task_info['status'] = 'running'
                logger.info(f"Executando tarefa {task_id}")
                
                # Executa a função principal
                result = task_info['func'](*task_info['args'], **task_info['kwargs'])
                task_info['result'] = result
                task_info['status'] = 'completed'
                logger.info(f"Tarefa {task_id} completada")
                
                # Chama o callback se existir
                if task_info['callback']:
                    task_info['callback'](result, None)
                    
            except Exception as e:
                task_info['error'] = str(e)
                task_info['status'] = 'error'
                logger.error(f"Erro na tarefa {task_id}: {e}")
                
                # Chama o callback com erro
                if task_info['callback']:
                    task_info['callback'](None, str(e))
        
        # Cria e inicia a thread
        thread = threading.Thread(target=task_wrapper, daemon=True)
        task_info['thread'] = thread
        thread.start()
        
    def _pause_task(self, task_id: str):
        """Pausa uma tarefa (implementação básica)"""
        # Em uma implementação real, isso seria mais complexo
        # dependendo do tipo de tarefa
        logger.info(f"Tarefa {task_id} marcada como pausada")
        
    def _resume_task(self, task_id: str):
        """Retoma uma tarefa pausada"""
        logger.info(f"Tarefa {task_id} marcada como retomada")
        
    def _stop_task(self, task_id: str):
        """Para uma tarefa"""
        logger.info(f"Tarefa {task_id} marcada como parada")