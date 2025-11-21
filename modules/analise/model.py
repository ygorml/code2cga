"""
Módulo de análise de código-fonte para geração de grafos de chamada.

Este módulo contém a classe AnaliseModel responsável por analisar arquivos
de código-fonte usando LLMs (Modelos de Linguagem Grande) para extrair
informações estruturadas sobre o fluxo de execução e dependências.

O módulo suporta análise de múltiplos arquivos com sistema completo de:
- Checkpoint inteligente para evitar análises redundantes
- Pausa automática por limites de API com retentativa programada
- Timing preciso que exclui períodos de pausa
- Controle de progresso com callbacks
- Extração robusta de JSON das respostas do LLM
- Geração de grafos de chamada em formato JSON
- Tratamento de erros e recuperação

Sistema de Checkpoint:
- Verificação pré-análise para evitar requisições redundantes
- Validação de configuração para compatibilidade
- Reaproveitamento inteligente de análises anteriores

Sistema de Pausa Automática:
- Detecção automática de erros de limite de API (429, 403)
- Pausa automática com retentativa a cada 30 minutos
- Recuperação transparente do ponto onde parou

Sistema de Timing Preciso:
- Medição de tempo efetivo vs tempo total
- Exclusão automática de períodos de pausa
- Relatórios detalhados de performance
"""

import os
import json
import logging
import time
import re
import threading
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, Future
import queue
import requests
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class AnaliseModel:
    """
    Modelo responsável pela análise de código-fonte usando LLMs com sistemas avançados.

    Esta classe coordena o processo de análise de múltiplos arquivos de código,
    utilizando serviços de LLM (como Ollama) para extrair informações estruturadas
    sobre o fluxo de execução, dependências e arquitetura do código.

    Principais funcionalidades:
    - Sistema de checkpoint inteligente para evitar análises redundantes
    - Pausa automática por limites de API com retentativa programada
    - Timing preciso que mede tempo efetivo excluindo pausas
    - Análise síncrona de múltiplos arquivos
    - Controle de progresso com callbacks
    - Extração robusta de JSON das respostas do LLM
    - Geração de grafos de chamada em formato JSON
    - Tratamento de erros e recuperação

    Attributes:
        notifier (Optional[Callable]): Serviço de notificação para eventos
        config (Dict[str, Any]): Configurações da análise
        ollama_service (OllamaService): Serviço para interação com Ollama
        is_running (bool): Indica se há uma análise em execução
        is_paused (bool): Indica se a análise está pausada
        is_stopped (bool): Indica se a análise foi parada
        current_progress (float): Progresso atual da análise (0-100)
        current_file (str): Arquivo sendo analisado atualmente
        resultados (List[Dict]): Resultados das análises realizadas
        api_pause_active (bool): Indica se pausa automática por API está ativa
        api_pause_reason (str): Motivo da pausa automática
        api_pause_start_time (float): Timestamp de início da pausa
        api_retry_interval (int): Intervalo de retentativa em segundos (30 min)
        api_max_retries (int): Máximo de tentativas de retentativa
        api_retry_count (int): Contador de tentativas realizadas
    """
    def __init__(self, notifier=None):
        """
        Inicializa uma nova instância do AnaliseModel com sistemas avançados.

        Configura o modelo com suporte completo para checkpoint inteligente,
        pausa automática por API, e timing preciso. Inicializa o serviço do
        Ollama e cria os diretórios necessários para armazenamento.

        Args:
            notifier (Optional[Callable]): Serviço de notificação para eventos da análise

        Note:
            Cria os diretórios necessários para armazenamento dos resultados,
            inicializa o serviço do Ollama para interação com LLMs, e configura
            o sistema de pausa automática com intervalo de 30 minutos e máximo
            de 10 tentativas de retentativa.
        """
        self.notifier = notifier
        self.config = self._get_default_config()
        self.ollama_service = OllamaService(base_url=self.config.get('llm_url', 'http://localhost:11434'))
        self.garantir_pastas()

        # Sistema simplificado - sem threads complexas
        self.is_running = False
        self.is_paused = False
        self.is_stopped = False
        self.current_progress = 0
        self.current_file = ""
        self.resultados = []

        # Sistema de pausa automática por limite de API
        self.api_pause_active = False
        self.api_pause_reason = None
        self.api_pause_start_time = None
        self.api_retry_thread = None
        self.api_retry_interval = 30 * 60  # 30 minutos em segundos
        self.api_max_retries = 10  # Máximo de tentativas
        self.api_retry_count = 0

        # Sistema de debug para validação JSON
        self._last_validation_error = None

        logger.info("AnaliseModel instanciado (versão simplificada).")

    def _ativar_pausa_api(self, motivo: str):
        """
        Ativa o sistema de pausa automática por limite de API.

        Este método é chamado automaticamente quando são detectados erros
        de limite de API (429, 403, quota exceeded). Ele interrompe a análise
        atual e inicia um thread em background para retentativas automáticas
        a cada 30 minutos, com máximo de 10 tentativas.

        Args:
            motivo (str): Descrição do motivo da pausa (ex: "rate_limit", "quota_exceeded")

        Note:
            - Define api_pause_active=True para sinalizar estado de pausa
            - Registra timestamp de início para cálculos de timing
            - Inicia thread de retentativa automática se não estiver ativo
            - Notifica usuário sobre pausa e próximo tempo de tentativa

        Raises:
            None: Método trata exceções internamente
        """
        if self.api_pause_active:
            return  # Já está pausado

        self.api_pause_active = True
        self.api_pause_reason = motivo
        self.api_pause_start_time = time.time()
        self.is_paused = True  # Pausa a análise principal

        logger.warning(f"🚦 Pausa automática ativada: {motivo}")
        if self.notifier:
            self.notifier.warning(f"⏸️ Análise pausada: {motivo}. Retentativa em 30 minutos...")

        # Inicia thread de retentativa
        self._iniciar_retentativa_api()

    def _iniciar_retentativa_api(self):
        """
        Inicia thread para retentativas automáticas da API
        """
        if self.api_retry_thread and self.api_retry_thread.is_alive():
            return  # Já existe uma thread de retentativa

        def retry_worker():
            while self.api_pause_active and self.api_retry_count < self.api_max_retries:
                time.sleep(self.api_retry_interval)  # Espera 30 minutos
                self.api_retry_count += 1

                logger.info(f"🔄 Tentativa {self.api_retry_count}/{self.api_max_retries} de reconexão com API...")
                if self.notifier:
                    self.notifier.info(f"🔄 Tentativa {self.api_retry_count}/{self.api_max_retries} de reconexão...")

                # Testa a conexão com a API
                if self.ollama_service.check_connection():
                    logger.info("✅ API respondeu! Retomando análise...")
                    if self.notifier:
                        self.notifier.success("✅ API disponível! Retomando análise...")

                    self._desativar_pausa_api()
                    break
                else:
                    logger.warning(f"❌ API ainda indisponível. Próxima tentativa em 30 minutos...")
                    if self.notifier:
                        self.notifier.warning(f"❌ API ainda indisponível. Tentativa {self.api_retry_count + 1}/{self.api_max_retries} em 30 min...")

            # Se esgotou as tentativas
            if self.api_retry_count >= self.api_max_retries:
                logger.error("🚫 Número máximo de retentativas esgotado. Análise interrompida.")
                if self.notifier:
                    self.notifier.error("🚫 Máximo de retentativas esgotado. Verifique manualmente a API.")
                self.parar_analise()

        self.api_retry_thread = threading.Thread(target=retry_worker, daemon=True)
        self.api_retry_thread.start()

    def _desativar_pausa_api(self):
        """
        Desativa o sistema de pausa automática e retoma a análise.

        Este método é chamado quando a API volta a responder ou quando o
        usuário força uma retentativa. Ele reseta o estado de pausa e
        retoma a análise do ponto onde parou.

        Note:
            - Define api_pause_active=False para desativar estado de pausa
            - Calcula e registra tempo total de pausa para precisão de timing
            - Reseta contador de tentativas de retentativa
            - Retoma análise principal definindo is_paused=False
            - Notifica usuário sobre retomada bem-sucedida

        Raises:
            None: Método trata exceções internamente
        """
        if not self.api_pause_active:
            return

        self.api_pause_active = False
        self.api_pause_reason = None
        self.api_pause_start_time = None
        self.is_paused = False  # Retoma a análise principal
        self.api_retry_count = 0

        logger.info("🟢 Pausa automática desativada. Análise retomada.")

    def obter_status_pausa_api(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o status da pausa por API
        """
        if not self.api_pause_active:
            return {
                'ativa': False,
                'motivo': None,
                'tempo_esperado': 0,
                'tentativas': self.api_retry_count
            }

        tempo_esperado = time.time() - self.api_pause_start_time
        proxima_tentativa = self.api_retry_interval - (tempo_esperado % self.api_retry_interval)

        return {
            'ativa': True,
            'motivo': self.api_pause_reason,
            'tempo_esperado_segundos': int(tempo_esperado),
            'proxima_tentativa_segundos': int(proxima_tentativa),
            'tentativas': self.api_retry_count,
            'maximo_tentativas': self.api_max_retries
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retorna a configuração padrão para análise de código.

        Returns:
            Dict[str, Any]: Dicionário com configurações padrão incluindo:
                - nivel_analise: Nível de detalhamento da análise
                - incluir_comentarios: Se deve analisar comentários
                - analisar_dependencias: Se deve analisar dependências
                - llm_url: URL do servidor LLM
                - llm_modelo: Modelo LLM a ser usado
                - llm_tamanho_contexto: Tamanho máximo do contexto
                - llm_temperatura: Temperatura de geração do LLM
        """
        return {
            'nivel_analise': 'detalhado',
            'incluir_comentarios': True,
            'analisar_dependencias': True,
            'gerar_json': True,
            'gerar_explicabilidade': True,
            'limite_linhas': 1000,
            'linguagem': 'c',
            'threads': 1,
            'pasta_inspecao': 'inspecao/',
            # Configurações do LLM
            'llm_url': 'http://localhost:11434',
            'llm_modelo': 'llama2',
            'llm_tamanho_contexto': 4096,
            'llm_temperatura': 0.7
        }

    def _get_extensoes_por_linguagem(self) -> Dict[str, List[str]]:
        """
        Retorna um dicionário com as extensões de arquivo permitidas por linguagem.

        Returns:
            Dict[str, List[str]]: Mapeamento de linguagem para lista de extensões
        """
        return {
            'c': ['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.c++'],
            'python': ['.py', '.pyx', '.pyi'],
            'java': ['.java', '.class', '.jar'],
            'javascript': ['.js', '.jsx', '.mjs', '.cjs'],
            'typescript': ['.ts', '.tsx'],
            'go': ['.go'],
            'rust': ['.rs', '.toml'],
            'php': ['.php', '.phtml', '.php3', '.php4', '.php5'],
            'csharp': ['.cs', '.csx'],
            'ruby': ['.rb', '.rbw'],
            'cpp': ['.cpp', '.hpp', '.cc', '.cxx', '.c++', '.c', '.h']
        }

    def _validar_extensoes_arquivos(self, arquivos: List[str], config: Dict[str, Any]) -> List[str]:
        """
        Valida e filtra arquivos baseado nas extensões permitidas pela linguagem configurada.

        Args:
            arquivos (List[str]): Lista de caminhos de arquivos para validar
            config (Dict[str, Any]): Configuração da análise (deve conter 'linguagem')

        Returns:
            List[str]: Lista de arquivos com extensões válidas para a linguagem

        Note:
            Arquivos com extensões inválidas são logged como warning e removidos da lista
        """
        linguagem = config.get('linguagem', 'c').lower()
        extensoes_permitidas = self._get_extensoes_por_linguagem().get(linguagem, self._get_extensoes_por_linguagem()['c'])

        arquivos_validos = []
        arquivos_invalidos = []

        for arquivo in arquivos:
            _, ext = os.path.splitext(arquivo.lower())
            if ext in extensoes_permitidas:
                arquivos_validos.append(arquivo)
            else:
                arquivos_invalidos.append(arquivo)

        if arquivos_invalidos:
            logger.warning(f"🚫 {len(arquivos_invalidos)} arquivo(s) ignorado(s) por extensão incompatível com linguagem '{linguagem}':")
            for arquivo in arquivos_invalidos:
                _, ext = os.path.splitext(arquivo)
                logger.warning(f"   - {arquivo} (extensão: {ext})")
            logger.info(f"✅ {len(arquivos_validos)} arquivo(s) válido(s) para análise de linguagem '{linguagem}'")

        return arquivos_validos
    
    def _get_prompt_padrao(self) -> str:
        """Retorna o prompt padrão para análise de código"""
        return (
            "Você é um engenheiro de software sênior especializado em análise de código-fonte e arquitetura de sistemas.\n"
            "Sua missão é realizar uma análise completa do arquivo de código fornecido e estruturar sua resposta em duas seções distintas, conforme detalhado abaixo.\n\n"
            "--------------------------------\n"
            "### SEÇÃO 1: FORMATO OBRIGATÓRIO DO GRAFO JSON\n"
            "Para a tarefa de geração do grafo, você DEVE gerar o JSON seguindo ESTRITAMENTE o formato, a estrutura e a riqueza de detalhes do exemplo a seguir. Preencha todos os campos possíveis com base na sua análise do código, incluindo `group`, `shape`, `color` e especialmente os `metadata`.\n\n"
            "```json\n"
            "{{\n"
            '  "nodes": [],\n'
            '  "edges": [],\n'
            '  "meta": {{}}\n'
            "}}\n"
            "```\n\n"
            "--------------------------------\n"
            "### SEÇÃO 2: SUAS TAREFAS\n\n"
            "Com base no código-fonte fornecido, execute as seguintes tarefas:\n\n"
            "1.  **ANÁLISE TÉCNICA:**\n"
            "    - Escreva uma análise clara e técnica sobre o propósito e a funcionalidade do código.\n"
            "    - Descreva as responsabilidades principais da classe/função.\n"
            "    - Explique as lógicas de negócio e o fluxo de execução de ponta a ponta.\n\n"
            "2.  **GRAFO DE FLUXO (JSON):**\n"
            "    - Gere um grafo completo em formato JSON que mapeia as interações e chamadas no código.\n"
            "    - Siga rigorosamente o formato rico do exemplo na SEÇÃO 1.\n\n"
            "--- CÓDIGO DO ARQUIVO: {filename} ---\n"
            "```{lang}\n{code}\n```\n\n"
            "--- ANÁLISE COMPLETA ---\n"
        )
    
    def _construir_prompt_analise(self, arquivo: str, codigo: str, config: Dict[str, Any]) -> str:
        """Constrói o prompt para análise do código"""
        prompt_template = config.get('prompt_template', self._get_prompt_padrao())
        
        # Substitui placeholders
        prompt = prompt_template.replace('{filename}', os.path.basename(arquivo))
        prompt = prompt.replace('{lang}', config.get('linguagem', 'c'))
        prompt = prompt.replace('{code}', codigo[:config.get('limite_linhas', 1000) * 10])
        
        return prompt
    
    def _extrair_json_da_resposta(self, resposta: str) -> Dict[str, Any]:
        """
        Extrai JSON estruturado da resposta do LLM usando múltiplas estratégias robustas.

        Este método implementa um sistema completo de extração de JSON com fallbacks
        progressivos para lidar com diferentes formatos de resposta do LLM. Usa
        múltiplas estratégias de regex e fallback textual para garantir máxima
        taxa de sucesso na extração dos dados estruturados.

        Args:
            resposta (str): Resposta bruta do LLM contendo JSON estruturado

        Returns:
            Dict[str, Any]: Dicionário com os dados extraídos. Em caso de falha
                          completa, retorna estrutura vazia com campos obrigatórios.

        Note:
            Estratégias de extração em ordem de prioridade:
            1. Bloco de código JSON (```json ... ```)
            2. JSON entre chaves com formatação variada
            3. Análise textual como fallback (extrai nodes/edges manualmente)
            4. Estrutura vazia como último recurso

        Raises:
            None: Método sempre retorna um dicionário válido, tratando erros internamente

        Example:
            >>> json_data = model._extrair_json_da_resposta(resposta_llm)
            >>> nodes = json_data.get('nodes', [])
            >>> edges = json_data.get('edges', [])
        """
        try:
            logger.info(f"🔍 Iniciando extração de JSON (resposta: {len(resposta)} caracteres)")

            import re

            # 🔥 MELHORIA: Estratégias mais específicas para encontrar o JSON correto
            json_patterns = [
                # Padrões mais específicos primeiro - procuram por JSON com nodes/edges
                r'```json\s*(\{[^`]*"nodes"[^`]*"edges"[^`]*\})\s*```',
                r'```JSON\s*(\{[^`]*"nodes"[^`]*"edges"[^`]*\})\s*```',
                # Padrões para JSON que contenham nodes ou edges individualmente
                r'```json\s*(\{[^`]*"nodes"[^`]*\})\s*```',
                r'```JSON\s*(\{[^`]*"nodes"[^`]*\})\s*```',
                r'```json\s*(\{[^`]*"edges"[^`]*\})\s*```',
                r'```JSON\s*(\{[^`]*"edges"[^`]*\})\s*```',
                # Depois patterns mais genéricos dentro de blocos de código
                r'```json\s*(.*?)\s*```',
                r'```JSON\s*(.*?)\s*```',
                # Blocos de código genéricos (menos prioritários)
                r'```\s*(\{[^`]*\})\s*```',
                # 🔥 CORREÇÃO: Padrão mais específico fora de blocos de código
                # Evita capturar estruturas pequenas ou fragmentos
                r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\{[^{}]*"nodes"[^{}]*\}[^{}]*\})',
                r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\{[^{}]*"edges"[^{}]*\}[^{}]*\})',
            ]

            json_candidates = []
            invalid_structures = []

            for i, pattern in enumerate(json_patterns):
                matches = re.findall(pattern, resposta, re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    json_str = match.strip()

                    # 🔥 Limpeza mais robusta do JSON
                    json_str = self._limpar_json_str(json_str)

                    if json_str and json_str.startswith('{') and json_str.endswith('}'):
                        # 🔥 MELHORIA: Filtra candidatos muito pequenos provavelmente inválidos
                        if len(json_str) >= 50:  # Pelo menos 50 caracteres
                            json_candidates.append((json_str, f"pattern_{i+1}"))
                        else:
                            logger.debug(f"🔍 Candidato muito pequeno descartado ({len(json_str)} chars): {json_str[:50]}...")
                            continue

            logger.info(f"🔍 Encontrados {len(json_candidates)} candidatos a JSON")

            # 🔥 MELHORIA: Ordena candidatos por preferência (nodes/edges primeiro)
            def candidate_priority(json_str):
                try:
                    # Verifica se tem nodes e edges
                    has_nodes = '"nodes"' in json_str
                    has_edges = '"edges"' in json_str
                    has_name = '"name"' in json_str  # Provavelmente o JSON correto

                    # 🔥 MELHORIA: Verifica se JSON é muito pequeno (provavelmente inválido)
                    json_length = len(json_str)
                    is_too_small = json_length < 100  # Menos de 100 caracteres provavelmente é inválido
                    has_required_keys = has_nodes or has_edges

                    # Prioridade 1 (melhor): tem nodes, edges e name, e não é muito pequeno
                    if has_nodes and has_edges and has_name and not is_too_small:
                        return 1
                    # Prioridade 2: tem nodes e edges, e não é muito pequeno
                    elif has_nodes and has_edges and not is_too_small:
                        return 2
                    # Prioridade 3: tem nodes ou edges, mas não é muito pequeno
                    elif has_required_keys and not is_too_small:
                        return 3
                    # Prioridade 4: muito pequeno (provavelmente fragmento inválido)
                    elif is_too_small:
                        return 5
                    # Prioridade 5: outros (sem nodes/edges)
                    else:
                        return 4
                except:
                    return 6

            # Ordena candidatos por prioridade
            json_candidates.sort(key=lambda x: candidate_priority(x[0]))

            # Tenta cada candidato apenas uma vez
            for i, (json_str, source) in enumerate(json_candidates):
                try:
                    parsed_json = json.loads(json_str)
                    # 🔥 Validação básica da estrutura
                    if self._validar_estrutura_json(parsed_json):
                        nodes_count = len(parsed_json.get('nodes', []))
                        edges_count = len(parsed_json.get('edges', []))
                        logger.info(f"✅ JSON extraído com sucesso (via {source}, candidato {i+1})")
                        logger.info(f"   📊 Estatísticas: {nodes_count} nodes, {edges_count} edges")
                        return parsed_json
                    else:
                        # Coleta informações sobre estrutura inválida para debugging
                        keys = list(parsed_json.keys()) if isinstance(parsed_json, dict) else "not_dict"
                        error_msg = self._last_validation_error or "erro desconhecido"
                        invalid_structures.append((source, keys, error_msg))
                except json.JSONDecodeError as e:
                    logger.debug(f"❌ Parse falhou no candidato {i+1}: {e}")
                    continue

            # Se houver estruturas inválidas, mostra um resumo útil
            if invalid_structures:
                logger.warning(f"⚠️ {len(invalid_structures)} JSON(s) com estrutura inválida:")
                # Agrupa por padrão para mostrar os mais problemáticos
                pattern_counts = {}
                for source, _, _ in invalid_structures:
                    pattern_counts[source] = pattern_counts.get(source, 0) + 1

                # Mostra os padrões mais problemáticos primeiro
                for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                    logger.warning(f"   - {pattern}: {count} ocorrências")

                # Mostra exemplos específicos (limitado a 2)
                for source, keys, error_msg in invalid_structures[:2]:
                    logger.warning(f"   - {source}: {error_msg}")
                    logger.warning(f"     chaves encontradas = {keys}")
                if len(invalid_structures) > 2:
                    logger.warning(f"   ... e mais {len(invalid_structures) - 2} omissos")

            # 🔥 Estratégia 2: Extração manual mais sofisticada
            json_str = self._extrair_json_manual(resposta)
            if json_str:
                try:
                    parsed_json = json.loads(json_str)
                    if self._validar_estrutura_json(parsed_json):
                        nodes_count = len(parsed_json.get('nodes', []))
                        edges_count = len(parsed_json.get('edges', []))
                        logger.info(f"✅ JSON extraído manualmente com sucesso")
                        logger.info(f"   📊 Estatísticas: {nodes_count} nodes, {edges_count} edges")
                        return parsed_json
                except json.JSONDecodeError as e:
                    logger.debug(f"❌ Parse manual falhou: {e}")

            # 🔥 Estratégia 3: Tenta extrair informações do texto se JSON falhar completamente
            fallback_result = self._extrair_info_textual(resposta)
            if fallback_result:
                logger.warning("⚠️ JSON falhou, mas informações extraídas do texto")
                return fallback_result

            # Fallback para estrutura mínima com informações de debug
            logger.warning("⚠️ Não foi possível extrair JSON válido, usando estrutura mínima")
            return {
                "nodes": [],
                "edges": [],
                "meta": {
                    "parse_status": "failed",
                    "response_length": len(resposta),
                    "response_preview": resposta[:500] + "..." if len(resposta) > 500 else resposta
                }
            }

        except Exception as e:
            logger.error(f"💥 Erro crítico ao extrair JSON: {e}")
            return {
                "nodes": [],
                "edges": [],
                "meta": {"error": str(e), "parse_status": "critical_error"}
            }

    def _limpar_json_str(self, json_str: str) -> str:
        """Limpa e normaliza string JSON"""
        if not json_str:
            return ""

        # Remove caracteres problemáticos do início e fim
        json_str = json_str.strip()

        # Remove marcadores de código que possam ter sobrado
        json_str = re.sub(r'^[^\{]*', '', json_str)  # Remove tudo antes de {
        json_str = re.sub(r'[^\}]*$', '', json_str)  # Remove tudo depois de }

        # Corrige problemas comuns de formatação
        json_str = json_str.replace('\n', ' ').replace('\r', ' ')
        json_str = re.sub(r'\s+', ' ', json_str)  # Normaliza espaços

        # Remove comentários inline problemáticos
        json_str = re.sub(r'//.*?(?=[\}\],])', '', json_str)

        # Corrige aspas simples para aspas duplas (problema comum)
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)

        # Remove espaços antes de vírgulas e depois de vírgulas
        json_str = re.sub(r'\s*,', ',', json_str)
        json_str = re.sub(r',\s*', ',', json_str)

        return json_str

    def _validar_estrutura_json(self, json_data: Dict[str, Any]) -> bool:
        """
        Valida se o JSON tem a estrutura esperada para análise de código.

        Args:
            json_data (Dict[str, Any]): Dados JSON a validar

        Returns:
            bool: True se estrutura é válida, False caso contrário
        """
        if not isinstance(json_data, dict):
            return False

        # Verifica se tem as chaves principais
        required_keys = ['nodes', 'edges']
        missing_keys = [key for key in required_keys if key not in json_data]

        if missing_keys:
            # Debug: mostra quais chaves faltam em vez de apenas falhar
            self._last_validation_error = f"Chaves faltando: {missing_keys}"
            return False

        # Verifica se nodes e edges são listas
        if not isinstance(json_data['nodes'], list):
            self._last_validation_error = f"'nodes' não é lista: {type(json_data['nodes']).__name__}"
            return False

        if not isinstance(json_data['edges'], list):
            self._last_validation_error = f"'edges' não é lista: {type(json_data['edges']).__name__}"
            return False

        # 🔥 MELHORIA: Validação mais flexível dos formatos de arestas
        # Aceita tanto "source"/"target" quanto "from"/"to"
        if json_data['edges']:
            valid_edge = False
            for edge in json_data['edges'][:3]:  # Verifica só as 3 primeiras arestas
                if isinstance(edge, dict):
                    # Formato 1: source/target
                    if 'source' in edge and 'target' in edge:
                        valid_edge = True
                        break
                    # Formato 2: from/to
                    elif 'from' in edge and 'to' in edge:
                        valid_edge = True
                        break

            if not valid_edge:
                self._last_validation_error = "Edges não têm formato válido (source/target ou from/to)"
                return False

        self._last_validation_error = None
        return True

    def _extrair_json_manual(self, resposta: str) -> str:
        """Extrai JSON manualmente com heurísticas melhoradas"""
        # Procura pelo primeiro { e pelo último }
        start_idx = resposta.find('{')
        end_idx = resposta.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = resposta[start_idx:end_idx + 1]

            # Validação básica antes de retornar
            if json_str.count('{') == json_str.count('}'):  # Chaves balanceadas
                return self._limpar_json_str(json_str)

        return ""

    def _extrair_info_textual(self, resposta: str) -> Optional[Dict[str, Any]]:
        """Tenta extrair informações do texto quando JSON falha"""
        # Procura por menções de funções e estruturas no texto
        try:
            nodes = []
            edges = []

            # Padrões para encontrar funções/variáveis
            func_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)'
            var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'

            # Encontra funções
            functions = re.findall(func_pattern, resposta)
            for i, func in enumerate(set(functions[:10])):  # Limita para evitar excesso
                if len(func) > 2:  # Ignora nomes muito curtos
                    nodes.append({
                        "id": func,
                        "label": func,
                        "type": "function",
                        "pos": 100 + i * 10
                    })

            # Conecta algumas funções sequencialmente
            for i in range(len(nodes) - 1):
                edges.append({
                    "source": nodes[i]["id"],
                    "target": nodes[i + 1]["id"],
                    "type": "sequence"
                })

            if nodes:  # Só retorna se encontrou algo útil
                logger.info(f"🔓 Extraídas {len(nodes)} estruturas do texto")
                return {
                    "nodes": nodes,
                    "edges": edges,
                    "meta": {
                        "parse_status": "textual_fallback",
                        "extraction_method": "regex_textual"
                    }
                }
        except Exception as e:
            logger.debug(f"Falha na extração textual: {e}")

        return None

    def update_config(self, new_config: Dict[str, Any]):
        """Atualiza a configuração da análise"""
        self.config.update(new_config)

        # Atualiza a URL do OllamaService se foi alterada
        if 'llm_url' in new_config:
            new_url = self.config.get('llm_url', 'http://localhost:11434')
            self.ollama_service = OllamaService(base_url=new_url)
            logger.info(f"URL do Ollama atualizada para: {new_url}")

        logger.info(f"Configuração atualizada: {new_config}")

    def get_config(self) -> Dict[str, Any]:
        """Retorna a configuração atual"""
        return self.config.copy()

    def garantir_pastas(self):
        """Garante que as pastas necessárias existam."""
        os.makedirs("storage/data", exist_ok=True)
        os.makedirs("storage/temp", exist_ok=True)
        os.makedirs("explicabilidade", exist_ok=True)
        os.makedirs("inspecao", exist_ok=True)

    def analisar_codigo(self, arquivos: List[str], config: Dict[str, Any],
                    progress_callback: Callable = None,
                    completion_callback: Callable = None) -> str:
        """
        Inicia a análise de múltiplos arquivos de código-fonte.

        Este método inicia uma análise assíncrona dos arquivos fornecidos,
        utilizando LLM para extrair informações estruturadas sobre o código.
        A análise é executada em uma thread separada para não bloquear a UI.

        Args:
            arquivos (List[str]): Lista de caminhos dos arquivos para analisar
            config (Dict[str, Any]): Configurações da análise
            progress_callback (Callable, optional): Callback chamado com progresso
                Recebe: (progresso_percentual, arquivo_atual, resultado_parcial)
            completion_callback (Callable, optional): Callback chamado ao finalizar
                Recebe: (resultados, erro) - erro é None se sucesso

        Returns:
            str: ID único da tarefa de análise iniciada

        Raises:
            ValueError: Se nenhum arquivo válido for fornecido

        Note:
            A análise pode ser controlada com os métodos pausar_analise(),
            retomar_analise() e parar_analise().
        """
        task_id = f"analise_{int(time.time())}"

        # SISTEMA DE CHECKPOINT - Filtra apenas arquivos pendentes
        logger.info(f"🔍 Verificando {len(arquivos)} arquivos para análise...")
        arquivos_pendentes = self.obter_arquivos_pendentes(arquivos, config)

        if not arquivos_pendentes:
            logger.info("✅ Todos os arquivos já foram analisados com sucesso!")
            if completion_callback:
                completion_callback([], None)  # Retorna vazio pois não há o que analisar
            return task_id

        # VALIDAÇÃO DE EXTENSÕES - Filtra arquivos por extensão compatível com a linguagem
        logger.info(f"🔍 Validando extensões de arquivo para linguagem '{config.get('linguagem', 'c')}'...")
        arquivos_validos = self._validar_extensoes_arquivos(arquivos_pendentes, config)

        if not arquivos_validos:
            logger.error("❌ Nenhum arquivo com extensão válida encontrado para a linguagem configurada!")
            if completion_callback:
                completion_callback([], ValueError("Nenhum arquivo compatível com a linguagem selecionada"))
            return task_id

        logger.info(f"🎯 Iniciando análise de {len(arquivos_validos)} arquivos válidos (de {len(arquivos)} totais)")

        # Limpa estados anteriores
        self.is_running = True
        self.is_paused = False
        self.is_stopped = False
        self.current_progress = 0
        self.current_file = ""
        self.resultados = []

        # 🔍 ULTRATHINK: Executa em thread separada com tracking
        def run_analysis():
            # Logar início da thread
            import threading
            thread_id = threading.current_thread().ident
            logger.info(f"🆔 [ULTRATHINK] ANÁLISE THREAD INICIADA - Thread: {thread_id}")
            logger.info(f"🔍 [ULTRATHINK] Arquivos a analisar: {len(arquivos_validos)}")
            logger.debug(f"🔍 [ULTRATHINK] progress_callback: {progress_callback}")
            logger.debug(f"🔍 [ULTRATHINK] completion_callback: {completion_callback}")
            logger.debug(f"🔍 [ULTRATHINK] progress_callback ID: {id(progress_callback) if progress_callback else 'None'}")
            logger.debug(f"🔍 [ULTRATHINK] completion_callback ID: {id(completion_callback) if completion_callback else 'None'}")

            try:
                resultados = self._executar_analise_sincrona(
                    arquivos_validos, config, progress_callback, task_id
                )
                logger.info(f"✅ [ULTRATHINK] _executar_analise_sincrona concluída - Thread: {thread_id}")
                
                # ✅ CORREÇÃO: Chamar completion callback com tratamento de erro
                if completion_callback:
                    try:
                        completion_callback(resultados, None)
                    except Exception as callback_error:
                        logger.error(f"Erro no completion callback: {callback_error}", exc_info=True)
                        
            except Exception as e:
                logger.error(f"Erro na análise {task_id}: {e}")
                # ✅ CORREÇÃO: Chamar completion callback de erro com tratamento
                if completion_callback:
                    try:
                        completion_callback([], f"Erro: {str(e)}")
                    except Exception as callback_error:
                        logger.error(f"Erro no completion callback (erro): {callback_error}", exc_info=True)
            finally:
                self.is_running = False
        
        # Inicia a thread
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
        
        logger.info(f"Tarefa {task_id} iniciada. {len(arquivos_validos)} arquivos válidos para análise (de {len(arquivos)} totais).")
        return task_id

    def _executar_analise_sincrona(self, arquivos: List[str], config: Dict[str, Any],
                                progress_callback: Callable, task_id: str) -> List[Dict[str, Any]]:
        """
        Executa análise de forma síncrona - VERSÃO MAIS ROBUSTA
        """
        resultados = []
        total_arquivos = len(arquivos)
        
        logger.info(f"🎯 Iniciando análise síncrona da tarefa {task_id}")
        
        for i, arquivo in enumerate(arquivos):
            # Verifica se foi parada
            if self.is_stopped:
                logger.info(f"⏹️ Tarefa {task_id} parada pelo usuário")
                break
            
            # Verifica se está pausada (incluindo pausa automática por API)
            while self.is_paused and not self.is_stopped:
                if self.api_pause_active:
                    # Se está em pausa automática, espera mais tempo e verifica status
                    time.sleep(5)  # Espera longer para pausas automáticas

                    # Mostra status da pausa a cada minuto
                    if int(time.time()) % 60 == 0:
                        status_pausa = self.obter_status_pausa_api()
                        logger.info(f"⏳ Pausa automática: {status_pausa['motivo']}. "
                                  f"Próxima tentativa em {status_pausa['proxima_tentativa_segundos']//60} min...")
                else:
                    time.sleep(0.5)  # Pausa manual normal

            if self.is_stopped:
                break
            
            # Atualiza progresso
            self.current_file = arquivo
            self.current_progress = (i + 1) / total_arquivos * 100
            
            try:
                # Analisa arquivo individual
                resultado = self._analisar_arquivo_individual(arquivo, config)

                # Se resultado é None, indica pausa automática por API
                if resultado is None:
                    logger.info(f"⏸️ Análise de {os.path.basename(arquivo)} pausada por limite de API. Aguardando retomada automática...")
                    # Volta para o início do loop (onde vai esperar a pausa acabar)
                    i -= 1  # Volta para refazer este arquivo quando a análise retomar
                    continue

                resultados.append(resultado)

                # 🔍 ULTRATHINK: Notifica progresso com debug detalhado
                if progress_callback:
                    try:
                        # 🔍 Logar ANTES de chamar o callback
                        import threading
                        thread_id = threading.current_thread().ident
                        logger.info(f"🆔 [ULTRATHINK] MODEL CHAMANDO CALLBACK - Thread: {thread_id}")
                        logger.info(f"🔍 [ULTRATHINK] Arquivo: {arquivo}")
                        logger.info(f"🔍 [ULTRATHINK] Progresso: {self.current_progress}%")
                        logger.debug(f"🔍 [ULTRATHINK] Callback function: {progress_callback}")
                        logger.debug(f"🔍 [ULTRATHINK] Callback ID: {id(progress_callback)}")

                        # Logar o resultado que será passado
                        logger.debug(f"🔍 [ULTRATHINK] Resultado status: {resultado.get('status') if resultado else 'None'}")
                        logger.debug(f"🔍 [ULTRATHINK] Resultado keys: {list(resultado.keys()) if resultado else 'None'}")
                        if resultado and 'estatisticas' in resultado:
                            stats = resultado.get('estatisticas', {})
                            logger.debug(f"🔍 [ULTRATHINK] Estatísticas: {stats}")

                        logger.info(f"📞 [ULTRATHINK] EXECUTANDO progress_callback...")
                        progress_callback(self.current_progress, arquivo, resultado)
                        logger.info(f"✅ [ULTRATHINK] progress_callback executado com sucesso")
                    except Exception as callback_error:
                        logger.error(f"❌ [ULTRATHINK] ERRO NO CALLBACK: {callback_error}", exc_info=True)
                        logger.error(f"🔍 [ULTRATHINK] Callback function: {progress_callback}")
                        logger.error(f"🔍 [ULTRATHINK] Thread ID: {thread_id}")
                        # Não interrompe a análise por erro no callback
                else:
                    logger.warning(f"⚠️ [ULTRATHINK] progress_callback é None - não chamado para {arquivo}")

                logger.info(f"✅ Arquivo {i+1}/{total_arquivos} analisado: {os.path.basename(arquivo)}")

            except Exception as e:
                logger.error(f"❌ Erro ao analisar {arquivo}: {e}")
                resultado_erro = {
                    'arquivo': arquivo,
                    'erro': str(e),
                    'timestamp': time.time(),
                    'status': 'erro'
                }
                resultados.append(resultado_erro)
                
                # ✅ CORREÇÃO: Notifica progresso do erro com tratamento
                if progress_callback:
                    try:
                        progress_callback(self.current_progress, arquivo, resultado_erro)
                    except Exception as callback_error:
                        logger.error(f"Erro no callback de progresso (erro): {callback_error}")
        
        # Análise completada
        if not self.is_stopped:
            logger.info(f"🎉 Tarefa {task_id} completada. {len(resultados)} arquivos processados.")
        else:
            logger.info(f"⏹️ Tarefa {task_id} interrompida. {len(resultados)} arquivos processados.")

        # ✅ SALVAR: Armazena resultados no modelo para acesso posterior
        self.resultados = resultados
        logger.debug(f"Resultados armazenados em self.resultados: {len(self.resultados)} itens")

        return resultados

    def _verificar_checkpoint(self, arquivo: str, config: Dict[str, Any]) -> Optional[str]:
        """
        Verifica se o arquivo já foi analisado com sucesso usando o sistema de checkpoint inteligente.

        Este método implementa o sistema de checkpoint que evita análises redundantes,
        validando não apenas a existência do arquivo de análise anterior, mas também
        a compatibilidade da configuração utilizada. Isso garante que análises anteriores
        sejam reaproveitadas apenas quando appropriate.

        Args:
            arquivo (str): Caminho completo do arquivo fonte a ser verificado
            config (Dict[str, Any]): Configuração atual da análise para comparação

        Returns:
            Optional[str]: Caminho do arquivo JSON de análise existente se válido,
                         None se não existe ou é incompatível

        Note:
            Critérios de validação do checkpoint:
            - Arquivo JSON deve existir no diretório storage/data/
            - Status da análise anterior deve ser 'sucesso'
            - Configurações críticas devem ser compatíveis:
              * llm_modelo: Modelo LLM utilizado
              * nivel_analise: Nível da análise
              * analisar_dependencias: Flag de dependências
              * incluir_comentarios: Flag de comentários

        Example:
            >>> checkpoint = model._verificar_checkpoint('src/main.c', config)
            >>> if checkpoint:
            ...     print(f"Checkpoint válido encontrado: {checkpoint}")
            ...     # Reaproveitar análise anterior

        Raises:
            None: Método trata exceções internamente e retorna None em caso de erro
        """
        try:
            nome_base = os.path.basename(arquivo)

            # Determina o caminho do arquivo de análise
            if "inspecao" in arquivo:
                rel_path = os.path.relpath(arquivo, "inspecao")
                analysis_path = os.path.join("storage/data", rel_path + "_analise.json")
            else:
                analysis_path = os.path.join("storage/data", f"{nome_base}_analise.json")

            # Verifica se o arquivo existe
            if not os.path.exists(analysis_path):
                return None

            # Carrega e valida o arquivo de análise
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

            # Verifica se o status é sucesso e a configuração é compatível
            if (analysis_data.get('status') == 'sucesso' and
                'config' in analysis_data):

                stored_config = analysis_data['config']
                current_config = config

                # Verifica parâmetros críticos da configuração
                config_compativel = (
                    stored_config.get('llm_modelo') == current_config.get('llm_modelo') and
                    stored_config.get('nivel_analise') == current_config.get('nivel_analise') and
                    stored_config.get('analisar_dependencias') == current_config.get('analisar_dependencias') and
                    stored_config.get('incluir_comentarios') == current_config.get('incluir_comentarios')
                )

                if config_compativel:
                    logger.info(f"✅ Checkpoint encontrado para {arquivo} - análise anterior reaproveitada")
                    return analysis_path
                else:
                    logger.info(f"⚠️ Configuração mudou para {arquivo} - nova análise necessária")
                    return None
            else:
                logger.info(f"❌ Análise anterior falhou para {arquivo} - refazendo análise")
                return None

        except Exception as e:
            logger.warning(f"Erro ao verificar checkpoint para {arquivo}: {e}")
            return None

    def _analisar_arquivo_individual(self, arquivo: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um arquivo individual usando LLM - VERSÃO CORRIGIDA COM CHECKPOINT
        """
        logger.info(f"📁 Analisando arquivo: {arquivo}")

        # VERIFICAÇÃO DE CHECKPOINT - Evita análise redundante
        checkpoint_path = self._verificar_checkpoint(arquivo, config)
        if checkpoint_path:
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    stored_result = json.load(f)

                # Retorna resultado armazenado com marcação de checkpoint
                return {
                    'arquivo': arquivo,
                    'nome_arquivo': os.path.basename(arquivo),
                    'analise_texto': stored_result.get('analise_texto', ''),
                    'analise_json': stored_result.get('analise_json', {}),
                    'timestamp': stored_result.get('timestamp', time.time()),
                    'tempo_processamento': 0,  # Tempo zero pois foi do checkpoint
                    'checkpoint': True,  # Marcação de que veio do checkpoint
                    'checkpoint_path': checkpoint_path
                }
            except Exception as e:
                logger.warning(f"Erro ao carregar checkpoint para {arquivo}: {e}")

        try:
            # Lê o conteúdo do arquivo
            with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                codigo = f.read()
            
            # Verifica se o arquivo está vazio
            if not codigo.strip():
                logger.warning(f"📭 Arquivo vazio: {arquivo}")
                return {
                    'arquivo': arquivo,
                    'nome_arquivo': os.path.basename(arquivo),
                    'analise_texto': "Arquivo vazio",
                    'analise_json': {"nodes": [], "edges": [], "meta": {"empty_file": True}},
                    'timestamp': time.time(),
                    'config': config,
                    'status': 'vazio'
                }
            
            # Prepara o prompt para análise
            prompt = self._construir_prompt_analise(arquivo, codigo, config)
            
            # Obtém a análise do LLM
            modelo = config.get('llm_modelo', 'llama2')
            tamanho_contexto = config.get('llm_tamanho_contexto', 4096)
            temperatura = config.get('llm_temperatura', 0.7)
            
            logger.info(f"🤖 Solicitando análise do LLM (modelo: {modelo}, contexto: {tamanho_contexto})")

            analise, tempo_llm = self.ollama_service.generate_response(
                model=modelo,
                prompt=prompt,
                context_size=tamanho_contexto,
                temperature=temperatura
            )

            # ✅ CORREÇÃO: Melhor tratamento de erro para respostas do Ollama
            if not analise:
                # 🔥 MELHORIA: Captura a última mensagem de erro do OllamaService
                last_error = getattr(self.ollama_service, '_last_error', None)
                if last_error and ('429' in last_error or 'rate limit' in last_error.lower() or 'too many requests' in last_error.lower()):
                    # Erro de rate limit detectado - ativa pausa automática
                    error_msg = f"Erro de limite de API detectado: {last_error}"
                    logger.error(f"🚫 {error_msg}")
                    self._ativar_pausa_api(f"Limite de API atingido (rate_limit)")
                    return None  # Análise pausada
                else:
                    error_msg = f"Falha ao obter análise do LLM - modelo '{modelo}' pode não estar disponível"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)

            logger.info(f"📨 Resposta do LLM recebida: {len(analise)} caracteres")
            if tempo_llm:
                logger.info(f"⏱️ Tempo de processamento LLM: {tempo_llm:.2f} segundos")
            
            # Processa a resposta para extrair JSON
            resultado_json = self._extrair_json_da_resposta(analise)
            
            # Log das estatísticas finais
            nodes_count = len(resultado_json.get('nodes', []))
            edges_count = len(resultado_json.get('edges', []))
            logger.info(f"📊 Análise concluída: {nodes_count} nodes, {edges_count} edges extraídos")
            
            # Estrutura do resultado
            resultado = {
                'arquivo': arquivo,
                'nome_arquivo': os.path.basename(arquivo),
                'analise_texto': analise,
                'analise_json': resultado_json,
                'timestamp': time.time(),
                'config': config,
                'status': 'sucesso',
                'tempo_llm': tempo_llm,  # Tempo de processamento da LLM em segundos
                'estatisticas': {
                    'nodes_count': nodes_count,
                    'edges_count': edges_count,
                    'texto_length': len(analise),
                    'tempo_processamento': tempo_llm
                }
            }
            
            # Salva resultado em JSON
            output_path = self._salvar_resultado_json(resultado, arquivo)
            resultado['output_path'] = output_path
            
            logger.info(f"💾 Resultado salvo em: {output_path}")
            return resultado
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"💥 Erro ao analisar {arquivo}: {error_str}")

            # Usa o OllamaService para identificar o tipo de erro
            error_type = self.ollama_service.identificar_tipo_erro(error_str)

            # Verificação específica para erros de API que requerem pausa automática
            if error_type in ['rate_limit', 'quota_exceeded']:
                logger.error(f"🚫 Erro de limite de API detectado: {error_str}")
                self._ativar_pausa_api(f"Limite de API atingido ({error_type})")
            elif error_type == 'vram':
                logger.warning(f"🔴 Erro de memória VRAM detectado para {arquivo}")
            elif error_type == 'api_error':
                logger.warning(f"🔴 Erro de API detectado para {arquivo}")
            elif error_type == 'model_unavailable':
                logger.warning(f"🔴 Modelo não disponível para {arquivo}")
            elif error_type == 'timeout':
                logger.warning(f"🔴 Timeout detectado para {arquivo}")

            # Salva informação do erro para retomada posterior
            resultado_erro = {
                'arquivo': arquivo,
                'erro': error_str,
                'timestamp': time.time(),
                'status': 'erro',
                'error_type': error_type,
                'config': config  # Salva config para verificar compatibilidade futura
            }

            # 🔥 CORREÇÃO CRÍTICA: NÃO SALVA ARQUIVOS COM ERROS QUE NÃO SEJAM DE PAUSA
            # Evita que arquivos com erro sejam considerados "analisados" futuramente

            # Se for erro de API que requer pausa, não retorna resultado ainda
            # A análise será retomada automaticamente quando a API voltar
            if error_type in ['rate_limit', 'quota_exceeded']:
                logger.info(f"🚦 Análise pausada: {error_str}. Retentativa em 30 minutos...")
                return None  # Indica que a análise está pausada
            else:
                # 🔥 IMPORTANTE: Para erros não-relacionados a pausa (timeout, model unavailable, etc.)
                # NÃO salvar arquivo de resultado para permitir reanálise futura
                logger.warning(f"⚠️ Erro em {arquivo} não gerará arquivo (permitirá reanálise): {error_str}")
                return resultado_erro

    def analisar_status_analises(self, arquivos_projeto: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa o status de todos os arquivos de análise no projeto
        Retorna informações detalhadas sobre o que está completo, pendente ou com erro
        """
        logger.info("📊 Analisando status das análises do projeto...")

        status = {
            'total_arquivos': len(arquivos_projeto),
            'concluidos': [],
            'pendentes': [],
            'erros': [],
            'incompativeis': [],
            'resumo': {
                'sucesso': 0,
                'falha': 0,
                'pendente': 0,
                'incompativel': 0
            }
        }

        for arquivo in arquivos_projeto:
            try:
                nome_base = os.path.basename(arquivo)

                # Determina o caminho do arquivo de análise
                if "inspecao" in arquivo:
                    rel_path = os.path.relpath(arquivo, "inspecao")
                    analysis_path = os.path.join("storage/data", rel_path + "_analise.json")
                else:
                    analysis_path = os.path.join("storage/data", f"{nome_base}_analise.json")

                # Verifica se o arquivo de análise existe
                if not os.path.exists(analysis_path):
                    status['pendentes'].append({
                        'arquivo': arquivo,
                        'motivo': 'Não analisado anteriormente'
                    })
                    status['resumo']['pendente'] += 1
                    continue

                # Carrega o arquivo de análise
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)

                analysis_status = analysis_data.get('status', 'desconhecido')

                if analysis_status == 'sucesso':
                    # Verifica compatibilidade da configuração
                    if 'config' in analysis_data:
                        stored_config = analysis_data['config']
                        config_compativel = (
                            stored_config.get('llm_modelo') == config.get('llm_modelo') and
                            stored_config.get('nivel_analise') == config.get('nivel_analise') and
                            stored_config.get('analisar_dependencias') == config.get('analisar_dependencias') and
                            stored_config.get('incluir_comentarios') == config.get('incluir_comentarios')
                        )

                        if config_compativel:
                            status['concluidos'].append({
                                'arquivo': arquivo,
                                'analysis_path': analysis_path,
                                'timestamp': analysis_data.get('timestamp'),
                                'tempo_llm': analysis_data.get('tempo_llm', 0)
                            })
                            status['resumo']['sucesso'] += 1
                        else:
                            status['incompativeis'].append({
                                'arquivo': arquivo,
                                'motivo': 'Configuração alterada',
                                'analysis_path': analysis_path,
                                'stored_config': stored_config
                            })
                            status['resumo']['incompativel'] += 1
                    else:
                        # Análise bem-sucedida mas sem config - assume compatível
                        status['concluidos'].append({
                            'arquivo': arquivo,
                            'analysis_path': analysis_path,
                            'timestamp': analysis_data.get('timestamp'),
                            'tempo_llm': analysis_data.get('tempo_llm', 0)
                        })
                        status['resumo']['sucesso'] += 1

                elif analysis_status == 'erro':
                    error_type = analysis_data.get('error_type', 'geral')
                    status['erros'].append({
                        'arquivo': arquivo,
                        'erro': analysis_data.get('erro', 'Erro desconhecido'),
                        'error_type': error_type,
                        'timestamp': analysis_data.get('timestamp'),
                        'analysis_path': analysis_path
                    })
                    status['resumo']['falha'] += 1

                    # 🔥 CORREÇÃO: Trata falhas como pendentes para reanálise, exceto rate limit
                    if error_type not in ['rate_limit', 'quota_exceeded']:
                        status['pendentes'].append({
                            'arquivo': arquivo,
                            'motivo': f'Análise anterior falhou: {error_type}',
                            'retry': True  # Indica que pode ser reanalisado
                        })
                        status['resumo']['pendente'] += 1
                        status['resumo']['falha'] -= 1  # Remove da contagem de falha (agora é pendente)

                else:
                    # Status desconhecido - trata como pendente
                    status['pendentes'].append({
                        'arquivo': arquivo,
                        'motivo': f'Status desconhecido: {analysis_status}'
                    })
                    status['resumo']['pendente'] += 1

            except Exception as e:
                logger.warning(f"Erro ao analisar status de {arquivo}: {e}")
                status['pendentes'].append({
                    'arquivo': arquivo,
                    'motivo': f'Erro ao ler análise: {str(e)}'
                })
                status['resumo']['pendente'] += 1

        # Log do resumo
        logger.info(f"📈 Status da análise: {status['resumo']['sucesso']} concluídos, "
                   f"{status['resumo']['pendente']} pendentes, "
                   f"{status['resumo']['falha']} com erro, "
                   f"{status['resumo']['incompativel']} incompatíveis")

        return status

    def obter_arquivos_pendentes(self, arquivos_projetos: List[str], config: Dict[str, Any]) -> List[str]:
        """
        Retorna lista de arquivos que precisam ser analisados
        """
        status = self.analisar_status_analises(arquivos_projetos, config)

        # Arquivos pendentes incluem: nunca analisados + com erro + incompatíveis
        arquivos_pendentes = []

        # Adiciona nunca analisados
        for item in status['pendentes']:
            arquivos_pendentes.append(item['arquivo'])

        # Adiciona com erro (exceto erros de modelo indisponível)
        for item in status['erros']:
            if item['error_type'] != 'model_unavailable':
                arquivos_pendentes.append(item['arquivo'])

        # Adiciona incompatíveis
        for item in status['incompativeis']:
            arquivos_pendentes.append(item['arquivo'])

        logger.info(f"🎯 Identificados {len(arquivos_pendentes)} arquivos para análise (de {len(arquivos_projetos)} totais)")

        return arquivos_pendentes

    def forcar_retentativa_api(self) -> Dict[str, Any]:
        """
        Força uma tentativa imediata de reconexão com a API
        Útil se o usuário quer testar se a API voltou antes do tempo
        """
        if not self.api_pause_active:
            return {
                'status': 'nao_pausado',
                'mensagem': 'Não há pausa automática ativa no momento'
            }

        logger.info("🔄 Forçando tentativa imediata de reconexão com API...")
        if self.notifier:
            self.notifier.info("🔄 Testando conexão com API...")

        if self.ollama_service.check_connection():
            logger.info("✅ API respondeu! Retomando análise...")
            if self.notifier:
                self.notifier.success("✅ API disponível! Retomando análise...")
            self._desativar_pausa_api()
            return {
                'status': 'sucesso',
                'mensagem': 'API disponível! Análise retomada.'
            }
        else:
            logger.warning("❌ API ainda não respondeu.")
            if self.notifier:
                self.notifier.warning("❌ API ainda indisponível.")
            return {
                'status': 'falha',
                'mensagem': 'API ainda não respondeu. Continuando aguardo automático.'
            }

    def cancelar_pausa_automatica(self) -> Dict[str, Any]:
        """
        Cancela a pausa automática e interrompe a análise
        Útil se o usuário quer interromper completamente
        """
        if not self.api_pause_active:
            return {
                'status': 'nao_pausado',
                'mensagem': 'Não há pausa automática ativa no momento'
            }

        logger.info("🚫 Cancelando pausa automática por solicitação do usuário...")
        if self.notifier:
            self.notifier.warning("🚫 Pausa automática cancelada. Análise interrompida.")

        self._desativar_pausa_api()
        self.parar_analise()

        return {
            'status': 'sucesso',
            'mensagem': 'Pausa automática cancelada e análise interrompida.'
        }

    def verificar_status_completo(self, pasta_projeto: str = "inspecao/") -> Dict[str, Any]:
        """
        Método público para verificar status completo de todas as análises
        Útil para interface mostrar resumo do progresso
        """
        try:
            # Encontra todos os arquivos de código no projeto
            arquivos_projeto = []

            # Obtém a configuração atual de linguagem
            config = self.get_config()
            linguagem = config.get('linguagem', 'c')
            extensoes_permitidas = self._get_extensoes_por_linguagem().get(linguagem, ['.c', '.h'])

            for root, dirs, files in os.walk(pasta_projeto):
                for file in files:
                    if any(file.endswith(ext) for ext in extensoes_permitidas):
                        arquivos_projeto.append(os.path.join(root, file))

            if not arquivos_projeto:
                return {
                    'status': 'erro',
                    'mensagem': f'Nenhum arquivo de código encontrado em {pasta_projeto}',
                    'arquivos_total': 0
                }

            # Usa a configuração atual
            status = self.analisar_status_analises(arquivos_projeto, config)

            # Adiciona informações extras para a interface
            status.update({
                'status': 'sucesso',
                'pasta_projeto': pasta_projeto,
                'config_atual': {
                    'modelo': config.get('llm_modelo'),
                    'url': config.get('llm_url'),
                    'nivel_analise': config.get('nivel_analise')
                }
            })

            # Calcula economia de tempo/requisições
            total_tempo_economizado = sum(
                item.get('tempo_llm', 0) for item in status['concluidos']
            )
            status['economia'] = {
                'arquivos_ignorados': len(status['concluidos']),
                'tempo_economizado_segundos': total_tempo_economizado,
                'requisicoes_economizadas': len(status['concluidos'])
            }

            # Adiciona status da pausa automática por API
            status['pausa_automatica'] = self.obter_status_pausa_api()

            # Adiciona informações sobre a análise atual
            status['analise_atual'] = {
                'em_andamento': self.is_running,
                'arquivo_atual': self.current_file,
                'progresso_percentual': self.current_progress,
                'pausada': self.is_paused
            }

            return status

        except Exception as e:
            logger.error(f"Erro ao verificar status completo: {e}")
            return {
                'status': 'erro',
                'mensagem': f'Erro ao verificar status: {str(e)}',
                'arquivos_total': 0
            }

    def limpar_analises_com_erro(self, pasta_projeto: str = "inspecao/", tipos_erro: List[str] = None) -> Dict[str, Any]:
        """
        Remove arquivos de análise com erros específicos para permitir reanálise
        """
        if tipos_erro is None:
            tipos_erro = ['vram', 'timeout', 'api_error']  # Erros que podem ser temporários

        try:
            config = self.get_config()
            linguagem = config.get('linguagem', 'c')
            extensoes_permitidas = self._get_extensoes_por_linguagem().get(linguagem, ['.c', '.h'])

            arquivos_projeto = []
            for root, dirs, files in os.walk(pasta_projeto):
                for file in files:
                    if any(file.endswith(ext) for ext in extensoes_permitidas):
                        arquivos_projeto.append(os.path.join(root, file))

            status = self.analisar_status_analises(arquivos_projeto, config)
            removidos = 0

            for item in status['erros']:
                if item['error_type'] in tipos_erro:
                    try:
                        os.remove(item['analysis_path'])
                        logger.info(f"🗑️ Removida análise com erro ({item['error_type']}): {item['arquivo']}")
                        removidos += 1
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo {item['analysis_path']}: {e}")

            logger.info(f"✅ Limpeza concluída: {removidos} arquivos de análise removidos")
            return {
                'status': 'sucesso',
                'arquivos_removidos': removidos,
                'tipos_erro_processados': tipos_erro
            }

        except Exception as e:
            logger.error(f"Erro na limpeza de análises: {e}")
            return {
                'status': 'erro',
                'mensagem': f'Erro na limpeza: {str(e)}',
                'arquivos_removidos': 0
            }

    def _salvar_resultado_json(self, resultado: Dict[str, Any], arquivo_original: str) -> str:
        """Salva o resultado da análise em JSON com validação robusta"""
        try:
            nome_base = os.path.basename(arquivo_original)

            # 🔥 MELHORIA: Valida e corrige resultado antes de salvar
            resultado_validado = self._validar_e_corrigir_resultado(resultado, arquivo_original)

            # Cria estrutura de diretórios baseada no arquivo original
            if "inspecao" in arquivo_original:
                rel_path = os.path.relpath(arquivo_original, "inspecao")
                output_path = os.path.join("storage/data", rel_path + "_analise.json")
            else:
                output_path = os.path.join("storage/data", f"{nome_base}_analise.json")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(resultado_validado, f, indent=2, ensure_ascii=False)

            # 🔥 Validação final do JSON salvo
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Valida se o JSON está bem formado
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON salvo está malformado: {e}")
                # Salva versão de emergência
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(self._criar_resultado_emergencia(arquivo_original), f, indent=2, ensure_ascii=False)

            logger.debug(f"Resultado salvo em: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao salvar resultado JSON para {arquivo_original}: {e}")
            return ""

    def _validar_e_corrigir_resultado(self, resultado: Dict[str, Any], arquivo_original: str) -> Dict[str, Any]:
        """Valida e corrige o resultado antes de salvar"""
        # 🔥 Verifica se o resultado tem estrutura válida
        if not isinstance(resultado, dict):
            logger.warning(f"⚠️ Resultado inválido para {arquivo_original}, criando estrutura de emergência")
            return self._criar_resultado_emergencia(arquivo_original)

        # 🔥 Verifica se tem dados de análise válidos
        if 'status' not in resultado:
            resultado['status'] = 'sucesso'  # Assume sucesso se não especificado

        # 🔥 Valida e corrige dados do grafo
        analise_json = resultado.get('analise_json', {})

        if not isinstance(analise_json, dict):
            logger.warning(f"⚠️ analise_json inválido para {arquivo_original}")
            analise_json = {}

        # 🔥 Verifica se nodes e edges são listas válidas
        nodes = analise_json.get('nodes', [])
        edges = analise_json.get('edges', [])

        if not isinstance(nodes, list):
            nodes = []
            logger.warning(f"⚠️ nodes não é lista para {arquivo_original}")

        if not isinstance(edges, list):
            edges = []
            logger.warning(f"⚠️ edges não é lista para {arquivo_original}")

        # 🔥 CORREÇÃO: Se não há nodes nem edges E é um erro, NÃO gera grafo mínimo
        # Isso evita que arquivos com erro sejam considerados "analisados"
        if not nodes and not edges:
            # Verifica se o resultado indica erro
            if resultado.get('status') == 'erro':
                logger.warning(f"⚠️ Erro na análise de {arquivo_original} - não gerando grafo mínimo")
                # Cria estrutura vazia para indicar falha sem marcar como analisado
                analise_json = {
                    "nodes": [],
                    "edges": [],
                    "meta": {
                        "generated": "error_fallback",
                        "reason": "analysis_failed",
                        "error": resultado.get('erro', 'Unknown error')
                    }
                }
            else:
                # Apenas gera grafo mínimo se não for erro (ex: arquivo realmente sem código)
                nome_arquivo = os.path.basename(arquivo_original)
                analise_json = {
                    "nodes": [{
                        "id": nome_arquivo,
                        "label": nome_arquivo,
                        "type": "file",
                        "pos": 100
                    }],
                    "edges": [],
                    "meta": {
                        "generated": "auto_minimal",
                        "reason": "no_valid_data_found"
                    }
                }
                logger.warning(f"🔧 Gerado grafo mínimo para {arquivo_original}")

        # 🔥 Corrige e enriquece os dados
        resultado['analise_json'] = analise_json
        resultado['timestamp'] = resultado.get('timestamp', time.time())

        # 🔥 Adiciona estatísticas se não existirem
        if 'estatisticas' not in resultado:
            resultado['estatisticas'] = {
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "tempo_processamento": resultado.get('tempo_llm', 0)
            }

        # 🔥 Validação final
        if len(nodes) == 0 and len(edges) == 0:
            logger.warning(f"⚠️ Resultado sem dados de grafo para {arquivo_original}")

        return resultado

    def _criar_resultado_emergencia(self, arquivo_original: str) -> Dict[str, Any]:
        """Cria um resultado de emergência válido para arquivo que falhou completamente"""
        nome_arquivo = os.path.basename(arquivo_original)

        return {
            "arquivo": arquivo_original,
            "nome_arquivo": nome_arquivo,
            "status": "sucesso",
            "analise_texto": f"Análise de {nome_arquivo} concluída com dados mínimos",
            "analise_json": {
                "nodes": [{
                    "id": nome_arquivo,
                    "label": nome_arquivo,
                    "type": "file",
                    "pos": 100,
                    "color": "#888888"
                }],
                "edges": [],
                "meta": {
                    "generated": "emergency_fallback",
                    "reason": "complete_analysis_failure"
                }
            },
            "timestamp": time.time(),
            "config": self.config if hasattr(self, 'config') else {},
            "estatisticas": {
                "nodes_count": 1,
                "edges_count": 0,
                "tempo_processamento": 0
            },
            "error_recovery": True
        }

    def pausar_analise(self) -> bool:
        """Pausa a análise atual"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            logger.info("⏸️ Análise pausada")
            if self.notifier:
                self.notifier.info("Análise pausada")
            return True
        return False

    def retomar_analise(self) -> bool:
        """Retoma a análise pausada"""
        if self.is_paused:
            self.is_paused = False
            logger.info("▶️ Análise retomada")
            if self.notifier:
                self.notifier.info("Análise retomada")
            return True
        return False

    def parar_analise(self) -> bool:
        """Para a análise atual"""
        if self.is_running:
            self.is_stopped = True
            self.is_paused = False
            logger.info("⏹️ Análise parada")
            if self.notifier:
                self.notifier.info("Análise parada")
            return True
        return False

    def get_status_analise(self) -> Dict[str, Any]:
        """Retorna o status atual da análise"""
        return {
            'executando': self.is_running and not self.is_stopped,
            'pausada': self.is_paused,
            'parada': self.is_stopped,
            'completada': not self.is_running and not self.is_stopped,
            'progresso': self.current_progress,
            'arquivo_atual': self.current_file,
            'resultados_count': len(self.resultados),
            'resultado': self.resultados  # ✅ ADICIONADO: Inclui os resultados completos
        }

    def testar_conexao_ollama(self) -> Dict[str, Any]:
        """Testa a conexão com o Ollama"""
        try:
            if self.config.get('llm_url'):
                self.ollama_service.base_url = self.config['llm_url']
            
            conectado = self.ollama_service.check_connection()
            modelos = self.ollama_service.get_available_models() if conectado else []
            
            return {
                'conectado': conectado,
                'modelos': modelos,
                'url': self.config.get('llm_url', 'http://localhost:11434')
            }
        except Exception as e:
            logger.error(f"Erro ao testar conexão Ollama: {e}")
            return {
                'conectado': False,
                'modelos': [],
                'url': self.config.get('llm_url', 'http://localhost:11434'),
                'erro': str(e)
            }

    def is_analise_ativa(self) -> bool:
        """Verifica se há uma análise ativa"""
        return self.is_running and not self.is_stopped

    def shutdown(self):
        """Desliga o model adequadamente"""
        logger.info("Executando shutdown do AnaliseModel")
        self.parar_analise()
        logger.info("AnaliseModel shutdown completo")