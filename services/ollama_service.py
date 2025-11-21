#services/ollama.py

"""
Serviço Ollama - Interface para comunicação com Large Language Models.

Este módulo implementa a comunicação com o servidor Ollama para geração
de respostas usando modelos de linguagem grandes. Suporta tanto chamadas
via API REST quanto interface de linha de comando como fallback.

Funcionalidades:
- Conexão com servidor Ollama via REST API
- Listagem e verificação de modelos disponíveis
- Geração de respostas com configurações personalizáveis
- Sistema de fallback para CLI quando API não está disponível
- Tratamento robusto de erros e timeouts
- Medição de tempo de resposta para analytics
"""

import requests
import logging
import subprocess
import json
import time
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class OllamaService:
    """
    Serviço para comunicação com o servidor Ollama.

    Esta classe fornece uma interface abstrata para interagir com modelos
    de linguagem grandes através do Ollama. Suporta múltiplos métodos de
    comunicação e tratamento robusto de erros.

    Attributes:
        base_url (str): URL base do servidor Ollama
        available_models (List[str]): Cache de modelos disponíveis

    Example:
        >>> service = OllamaService("http://localhost:11434")
        >>> if service.check_connection():
        ...     models = service.get_available_models()
        ...     response, time_taken = service.generate_response(
        ...         model="codellama",
        ...         prompt="Explique este código",
        ...         temperature=0.7
        ...     )
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Inicializa o serviço Ollama.

        Args:
            base_url (str): URL base do servidor Ollama.
                          Default: "http://localhost:11434"
        """
        self.base_url = base_url
        self.available_models = []
        self._last_error = None  # 🔥 Armazena última mensagem de erro para debugging
        
    def check_connection(self) -> bool:
        """
        Verifica se o servidor Ollama está acessível.

        Tenta conectar ao servidor Ollama via API REST para verificar
        se o serviço está rodando e respondendo corretamente.

        Returns:
            bool: True se o servidor está acessível, False caso contrário

        Note:
            Usa timeout de 1200 segundos para acomodar análises complexas.
            Log automaticamente erros de conexão para debugging.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=1200)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao conectar com Ollama: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponíveis"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=60)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            else:
                logger.error(f"Erro ao obter modelos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erro ao obter modelos disponíveis: {e}")
            return []
    
    def _get_models_via_cli(self) -> List[str]:
        """Tenta obter modelos via linha de comando"""
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Pula o cabeçalho
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                self.available_models = models
                return models
            return []
        except Exception as e:
            logger.error(f"Erro ao obter modelos via CLI: {e}")
            return []
    
    def generate_response(self, model: str, prompt: str,
                        context_size: int = 4096,
                        temperature: float = 0.7) -> Tuple[Optional[str], Optional[float]]:
        """
        Gera uma resposta usando o modelo especificado

        Returns:
            Tuple[Optional[str], Optional[float]]: (resposta, tempo_em_segundos)
        """
        try:
            # ✅ CORREÇÃO: Verificar se o modelo está disponível primeiro
            available_models = self.get_available_models()
            if model not in available_models:
                logger.error(f"Modelo '{model}' não encontrado. Modelos disponíveis: {available_models}")
                return None, None

            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_ctx": context_size,
                    "temperature": temperature
                }
            }

            # Marca o início da requisição
            start_time = time.time()

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=1200
            )

            # Marca o fim da requisição
            end_time = time.time()
            elapsed_time = end_time - start_time

            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')

                # Log do tempo de processamento
                logger.info(f"⏱️ Tempo de resposta do LLM '{model}': {elapsed_time:.2f} segundos")

                return response_text, elapsed_time
            else:
                error_msg = f"Erro na geração: {response.status_code} - {response.text}"
                logger.error(error_msg)

                # 🔥 ARMAZENA ERRO PARA DETECÇÃO
                self._last_error = error_msg

                # Lança exceção específica para ser capturada pelo modelo
                raise Exception(error_msg)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erro ao gerar resposta: {e}")

            # 🔥 ARMAZENA ERRO PARA DETECÇÃO
            self._last_error = error_msg

            return None, None
    
    def identificar_tipo_erro(self, error_str: str) -> str:
        """
        Identifica o tipo de erro baseado na mensagem de erro
        Retorna: 'rate_limit', 'quota_exceeded', 'vram', 'model_unavailable', 'timeout', 'api_error', 'geral'
        """
        error_lower = error_str.lower()

        # Erros de limite de API
        if any(indicator in error_lower for indicator in [
            '429', 'too many requests', 'rate limit', 'rate limited',
            'quota exceeded', 'quota limit', 'usage limit', 'limit exceeded',
            'you\'ve reached', 'hourly usage limit', 'daily usage limit'
        ]):
            return 'rate_limit'

        # Erros de cota esgotada
        if any(indicator in error_lower for indicator in [
            '403', 'forbidden', 'access denied', 'billing', 'payment required',
            'subscription required', 'plan limit', 'usage cap'
        ]):
            return 'quota_exceeded'

        # Erros de VRAM
        if 'requires more system memory' in error_lower or 'vram' in error_lower:
            return 'vram'

        # Modelo não disponível
        if any(indicator in error_lower for indicator in [
            'model not found', 'model unavailable', 'model does not exist',
            'invalid model', 'unknown model'
        ]):
            return 'model_unavailable'

        # Timeout
        if any(indicator in error_lower for indicator in [
            'timeout', 'timed out', 'deadline exceeded'
        ]):
            return 'timeout'

        # Erros de API (HTTP 5xx)
        if any(code in error_str for code in ['500', '502', '503', '504']):
            return 'api_error'

        return 'geral'

    def test_model(self, model: str) -> bool:
        """Testa se um modelo específico está funcionando"""
        try:
            test_prompt = "Responda apenas com 'OK' se você está funcionando."
            response, _ = self.generate_response(model, test_prompt)
            return response is not None and 'OK' in response.upper()
        except Exception as e:
            logger.error(f"Erro ao testar modelo {model}: {e}")
            return False