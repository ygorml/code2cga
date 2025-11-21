# modules/dashboard/controller.py

import logging
import time
from typing import Dict, Any, List, Optional
from services.ollama_service import OllamaService
"""
Controller do dashboard principal.

Coordena a exibição de métricas e informações gerais do sistema.
"""


logger = logging.getLogger(__name__)

class DashboardController:
    def __init__(self, model, notifier, grafo_controller, analise_controller=None):
        self.model = model
        self.notifier = notifier
        self.grafo_controller = grafo_controller
        self.analise_controller = analise_controller

        # Inicializa OllamaService com URL da configuração se analise_controller estiver disponível
        if analise_controller:
            config = analise_controller.get_config()
            ollama_url = config.get('llm_url', 'http://localhost:11434')
            self.ollama_service = OllamaService(base_url=ollama_url)
        else:
            self.ollama_service = OllamaService()

        self.analise_atual = None
        self.analise_em_andamento = False
        
    def processar_analise_completa(self) -> Dict[str, Any]:
        """Processa análise completa e prepara contexto RAG"""
        try:
            if self.analise_em_andamento:
                self.notifier.warning("Já existe uma análise em andamento!")
                return None
                
            self.analise_em_andamento = True
            logger.info("Iniciando processamento de análise completa...")
            self.notifier.info("Iniciando análise completa...")
            
            # 1. Obtém dados do grafo atual - USANDO MÉTODO CORRETO
            resultado_grafo = self.grafo_controller.obter_resultado_grafo()
            if not resultado_grafo:
                self.notifier.error("Nenhum grafo disponível. Execute a análise de grafos primeiro.")
                self.analise_em_andamento = False
                return None
            
            # Verifica se temos um grafo válido
            grafo = resultado_grafo.get('grafo')
            if not grafo or grafo.number_of_nodes() == 0:
                self.notifier.error("Grafo vazio ou inválido. Execute a análise de grafos primeiro.")
                self.analise_em_andamento = False
                return None
            
            self.notifier.info("📊 Calculando métricas avançadas...")
            
            # 2. Calcula métricas avançadas
            metricas_avancadas = self.model.calcular_metricas_avancadas(resultado_grafo)
            
            self.notifier.info("📖 Gerando análise contextual...")
            
            # 3. Gera storytelling
            storytelling = self.model.gerar_storytelling(metricas_avancadas, resultado_grafo)
            
            self.notifier.info("🔧 Preparando contexto RAG...")
            
            # 4. Prepara contexto RAG
            contexto_rag = self.model.preparar_contexto_rag(metricas_avancadas, resultado_grafo, storytelling)
            
            # 5. Salva análise atual
            self.analise_atual = {
                'resultado_grafo': resultado_grafo,
                'metricas_avancadas': metricas_avancadas,
                'storytelling': storytelling,
                'contexto_rag': contexto_rag,
                'timestamp': self.model.obter_timestamp(),
                'metricas_resumidas': self.model.obter_metricas_resumidas(resultado_grafo)
            }
            
            # 6. Salva no histórico
            self.model.salvar_analise_historico(self.analise_atual)
            
            logger.info("Análise completa processada com sucesso")
            self.notifier.success("✅ Análise completa concluída! Contexto RAG preparado.")
            self.analise_em_andamento = False
            
            return self.analise_atual
            
        except Exception as e:
            logger.error(f"Erro no processamento da análise completa: {e}")
            self.notifier.error(f"❌ Erro na análise: {str(e)}")
            self.analise_em_andamento = False
            return None
        
    def get_analise_atual(self) -> Dict[str, Any]:
        """Retorna a análise atual"""
        return self.analise_atual
    
    def gerar_analise_personalizada(self, prompt: str) -> Dict[str, Any]:
        """Gera análise personalizada usando LLM"""
        try:
            logger.info("Iniciando análise personalizada com LLM...")
            
            if not self.analise_atual:
                return {
                    "sucesso": False,
                    "erro": "Execute a análise completa primeiro para carregar o contexto"
                }
            
            # Verifica conexão com Ollama
            if not self.ollama_service.check_connection():
                return {
                    "sucesso": False,
                    "erro": f"Servidor Ollama não está disponível em {self.ollama_service.base_url}. Verifique se o servidor está rodando e a URL está correta."
                }
            
            # Obtém modelos disponíveis
            modelos = self.ollama_service.get_available_models()
            if not modelos:
                return {
                    "sucesso": False,
                    "erro": "Nenhum modelo disponível no Ollama. Instale um modelo primeiro (ex: ollama pull codellama:7b)"
                }
            
            # Usa o primeiro modelo disponível
            modelo = modelos[0]
            logger.info(f"Usando modelo: {modelo}")
            
            # Gera resposta usando LLM
            resposta = self.ollama_service.generate_response(
                model=modelo,
                prompt=prompt,
                context_size=4096,
                temperature=0.7
            )
            
            if resposta:
                # Salva no histórico de análises RAG
                analise_rag = {
                    'prompt': prompt,
                    'analise_gerada': resposta,
                    'modelo_utilizado': modelo,
                    'timestamp': self.model.obter_timestamp(),
                    'metricas_utilizadas': self._extrair_metricas_do_contexto(prompt)
                }
                self.model.salvar_analise_rag_historico(analise_rag)
                
                logger.info("Análise RAG gerada com sucesso")
                
                return {
                    "sucesso": True,
                    "analise": resposta,
                    "modelo": modelo,
                    "timestamp": analise_rag['timestamp']
                }
            else:
                logger.error("Falha ao gerar resposta do LLM")
                return {
                    "sucesso": False,
                    "erro": "Falha ao gerar resposta do modelo LLM"
                }
                
        except Exception as e:
            logger.error(f"Erro na análise personalizada: {e}")
            return {
                "sucesso": False,
                "erro": f"Erro interno: {str(e)}"
            }
    
    def _extrair_metricas_do_contexto(self, prompt: str) -> Dict[str, Any]:
        """Extrai métricas relevantes do contexto do prompt"""
        try:
            if not self.analise_atual:
                return {}
                
            metricas = self.analise_atual.get('metricas_resumidas', {})
            return {
                'num_nos': metricas.get('num_nos', 0),
                'num_arestas': metricas.get('num_arestas', 0),
                'acoplamento_medio': metricas.get('acoplamento_medio', 0),
                'coesao_media': metricas.get('coesao_media', 0),
                'modularidade': metricas.get('modularidade', 0)
            }
        except Exception as e:
            logger.error(f"Erro ao extrair métricas do contexto: {e}")
            return {}
    
    def obter_historico_analises(self) -> List[Dict[str, Any]]:
        """Obtém histórico de análises RAG"""
        return self.model.obter_historico_analises_rag()
    
    def obter_historico_analises_completas(self) -> List[Dict[str, Any]]:
        """Obtém histórico de análises completas"""
        return self.model.obter_historico_analises()
    
    def verificar_analise_disponivel(self) -> bool:
        """Verifica se há análise disponível"""
        return self.analise_atual is not None and not self.analise_em_andamento
    
    def limpar_analise_atual(self):
        """Limpa a análise atual"""
        self.analise_atual = None
        logger.info("Análise atual limpa")
    
    def obter_metricas_resumidas(self) -> Dict[str, Any]:
        """Retorna métricas resumidas da análise atual"""
        if not self.analise_atual:
            return {}
        return self.analise_atual.get('metricas_resumidas', {})
    
    def obter_storytelling(self) -> Dict[str, str]:
        """Retorna storytelling da análise atual"""
        if not self.analise_atual:
            return {}
        return self.analise_atual.get('storytelling', {})
    
    def obter_estatisticas_grafo(self) -> Dict[str, Any]:
        """Retorna estatísticas do grafo atual"""
        if not self.analise_atual:
            return {}
        return self.analise_atual.get('resultado_grafo', {}).get('estatisticas', {})
    
    def obter_nos_criticos(self, limite: int = 5) -> List[Dict[str, Any]]:
        """Retorna lista de nós críticos baseados na centralidade"""
        try:
            if not self.analise_atual:
                return []
            
            resultado_grafo = self.analise_atual.get('resultado_grafo', {})
            nos_criticos = resultado_grafo.get('nos_criticos', [])
            
            # Ordena por centralidade e retorna os top N
            nos_ordenados = sorted(nos_criticos, 
                                 key=lambda x: x.get('centralidade_intermediacao', 0), 
                                 reverse=True)
            
            return nos_ordenados[:limite]
            
        except Exception as e:
            logger.error(f"Erro ao obter nós críticos: {e}")
            return []
    
    def obter_recomendacoes(self) -> str:
        """Retorna recomendações da análise atual"""
        storytelling = self.obter_storytelling()
        return storytelling.get('recomendacoes', 'Nenhuma recomendação disponível')
    
    def testar_conexao_ollama(self) -> Dict[str, Any]:
        """Testa a conexão com o Ollama e retorna status"""
        try:
            logger.info("Testando conexão com Ollama...")
            
            conectado = self.ollama_service.check_connection()
            modelos = []
            
            if conectado:
                modelos = self.ollama_service.get_available_models()
                logger.info(f"Conexão bem-sucedida. Modelos disponíveis: {len(modelos)}")
            else:
                logger.warning("Falha na conexão com Ollama")
            
            return {
                'conectado': conectado,
                'modelos': modelos,
                'quantidade_modelos': len(modelos),
                'url': self.ollama_service.base_url
            }
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão Ollama: {e}")
            return {
                'conectado': False,
                'modelos': [],
                'quantidade_modelos': 0,
                'erro': str(e),
                'url': self.ollama_service.base_url
            }
    
    def exportar_analise_atual(self) -> str:
        """Exporta análise atual para JSON"""
        try:
            if not self.analise_atual:
                return "{}"
            
            return self.model.exportar_analise_json(self.analise_atual)
            
        except Exception as e:
            logger.error(f"Erro ao exportar análise: {e}")
            return "{}"
    
    def importar_analise(self, json_str: str) -> bool:
        """Importa análise de JSON string"""
        try:
            analise_importada = self.model.importar_analise_json(json_str)
            
            if analise_importada:
                self.analise_atual = analise_importada
                logger.info("Análise importada com sucesso")
                self.notifier.success("Análise importada com sucesso!")
                return True
            else:
                logger.error("Falha ao importar análise")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao importar análise: {e}")
            self.notifier.error(f"Erro ao importar análise: {str(e)}")
            return False
    
    def obter_status_analise(self) -> Dict[str, Any]:
        """Retorna status atual da análise"""
        return {
            'analise_disponivel': self.analise_atual is not None,
            'analise_em_andamento': self.analise_em_andamento,
            'timestamp_ultima_analise': self.analise_atual.get('timestamp') if self.analise_atual else None,
            'quantidade_arquivos': self.analise_atual.get('resultado_grafo', {}).get('estatisticas', {}).get('num_nos', 0) if self.analise_atual else 0,
            'conexao_ollama': self.ollama_service.check_connection()
        }
    
    def obter_dados_dashboard(self) -> Dict[str, Any]:
        """Retorna dados consolidados para o dashboard"""
        status = self.obter_status_analise()
        metricas = self.obter_metricas_resumidas()
        storytelling = self.obter_storytelling()
        nos_criticos = self.obter_nos_criticos()
        estatisticas = self.obter_estatisticas_grafo()
        
        return {
            'status': status,
            'metricas': metricas,
            'storytelling': storytelling,
            'nos_criticos': nos_criticos,
            'estatisticas': estatisticas,
            'recomendacoes': self.obter_recomendacoes(),
            'historico_rag_count': len(self.obter_historico_analises()),
            'historico_completo_count': len(self.obter_historico_analises_completas())
        }
    
    def processar_analise_rapida(self) -> Dict[str, Any]:
        """Processa uma análise rápida com métricas básicas"""
        try:
            logger.info("Iniciando análise rápida...")
            self.notifier.info("🔄 Processando análise rápida...")
            
            resultado_grafo = self.grafo_controller.obter_resultado_grafo()
            if not resultado_grafo:
                self.notifier.error("Nenhum grafo disponível para análise rápida")
                return None
            
            # Calcula apenas métricas básicas
            metricas_basicas = self.model.obter_metricas_resumidas(resultado_grafo)
            
            analise_rapida = {
                'resultado_grafo': resultado_grafo,
                'metricas_basicas': metricas_basicas,
                'timestamp': self.model.obter_timestamp(),
                'tipo': 'rapida'
            }
            
            logger.info("Análise rápida processada com sucesso")
            self.notifier.success("✅ Análise rápida concluída!")
            
            return analise_rapida
            
        except Exception as e:
            logger.error(f"Erro na análise rápida: {e}")
            self.notifier.error(f"Erro na análise rápida: {str(e)}")
            return None
    
    def limpar_historico_analises(self):
        """Limpa o histórico de análises"""
        try:
            self.model.limpar_historico_analises()
            logger.info("Histórico de análises limpo")
            self.notifier.info("Histórico de análises limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            self.notifier.error(f"Erro ao limpar histórico: {str(e)}")
    
    def limpar_historico_analises_rag(self):
        """Limpa o histórico de análises RAG"""
        try:
            self.model.limpar_historico_analises_rag()
            logger.info("Histórico de análises RAG limpo")
            self.notifier.info("Histórico de análises RAG limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar histórico RAG: {e}")
            self.notifier.error(f"Erro ao limpar histórico RAG: {str(e)}")
    
    def obter_analise_por_id(self, analise_id: int) -> Dict[str, Any]:
        """Obtém uma análise específica por ID"""
        return self.model.obter_analise_por_id(analise_id)
    
    def obter_analise_rag_por_id(self, analise_id: int) -> Dict[str, Any]:
        """Obtém uma análise RAG específica por ID"""
        return self.model.obter_analise_rag_por_id(analise_id)
    
    def get_ollama_service(self) -> OllamaService:
        """Retorna o serviço Ollama para uso externo"""
        return self.ollama_service
    
    def atualizar_configuracao_ollama(self, base_url: str) -> bool:
        """Atualiza a URL base do serviço Ollama"""
        try:
            self.ollama_service = OllamaService(base_url)
            logger.info(f"URL do Ollama atualizada para: {base_url}")

            # Sincroniza com o analise_controller se disponível
            if self.analise_controller:
                self.analise_controller.update_config({'llm_url': base_url})
                logger.info("URL sincronizada com o AnaliseController")

            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar URL do Ollama: {e}")
            return False
    
    def validar_prompt_rag(self, prompt: str) -> Dict[str, Any]:
        """Valida se o prompt é adequado para análise RAG"""
        try:
            if not prompt or len(prompt.strip()) == 0:
                return {
                    'valido': False,
                    'erro': 'O prompt não pode estar vazio'
                }
            
            if len(prompt.strip()) < 10:
                return {
                    'valido': False,
                    'erro': 'O prompt é muito curto. Forneça mais detalhes para uma análise significativa.'
                }
            
            if len(prompt) > 10000:
                return {
                    'valido': False,
                    'erro': 'O prompt é muito longo. Limite a 10000 caracteres.'
                }
            
            # Verifica se há contexto de análise disponível
            if not self.analise_atual:
                return {
                    'valido': False,
                    'erro': 'Execute a análise completa primeiro para ter contexto das métricas.'
                }
            
            return {
                'valido': True,
                'tamanho': len(prompt),
                'linhas': prompt.count('\n') + 1
            }
            
        except Exception as e:
            logger.error(f"Erro ao validar prompt: {e}")
            return {
                'valido': False,
                'erro': f'Erro na validação: {str(e)}'
            }
    def verificar_e_preparar_grafo(self) -> bool:
        """
        Verifica se há um grafo disponível e prepara para análise.
        Retorna True se o grafo está pronto para uso.
        """
        try:
            # Tenta obter o resultado atual do grafo
            resultado_grafo = self.grafo_controller.obter_resultado_grafo()
            
            if not resultado_grafo:
                logger.info("📊 Nenhum grafo disponível, tentando processar automaticamente...")

                # Tenta encontrar e processar arquivos automaticamente
                arquivos_json = self.grafo_controller.encontrar_arquivos_json()

                if not arquivos_json:
                    logger.info("📂 Nenhum arquivo de análise encontrado para processar.")
                    self.notifier.warning("Nenhum arquivo de análise encontrado para processar.")
                    return False

                logger.info(f"🔧 Encontrados {len(arquivos_json)} arquivos, processando grafo automaticamente...")
                self.notifier.info("Processando grafo automaticamente...")

                # Processa o grafo automaticamente
                resultado = self.grafo_controller.processar_grafo(arquivos_json)

                if resultado and resultado.get('grafo'):
                    logger.info("✅ Grafo processado automaticamente com sucesso!")
                    self.notifier.success("Grafo processado automaticamente!")
                    return True
                else:
                    logger.error("❌ Falha ao processar grafo automaticamente")
                    self.notifier.error("Falha ao processar grafo automaticamente.")
                    return False
            else:
                # Grafo já está disponível
                grafo = resultado_grafo.get('grafo')
                if grafo and grafo.number_of_nodes() > 0:
                    logger.info(f"Grafo disponível: {grafo.number_of_nodes()} nós")
                    return True
                else:
                    self.notifier.warning("Grafo disponível mas vazio.")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao verificar e preparar grafo: {e}")
            self.notifier.error(f"Erro ao preparar grafo: {str(e)}")
            return False
    
    def processar_analise_completa_com_verificacao(self) -> Dict[str, Any]:
        """
        Versão segura que verifica e prepara o grafo antes da análise
        """
        # Verifica e prepara o grafo primeiro
        if not self.verificar_e_preparar_grafo():
            return None
        
        # Agora processa a análise completa
        return self.processar_analise_completa()
