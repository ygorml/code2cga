# modules/grafo/controller.py

import os
import json
import time
from typing import List, Dict, Any, Tuple, Set
import logging
import networkx as nx  
from collections import Counter
from .model import GrafoModel, HAS_LOUVAIN
"""
Controller do módulo de grafos.

Gerencia a visualização e manipulação de grafos de chamada.
"""


logger = logging.getLogger(__name__)

class GrafoController:
    def __init__(self, model: GrafoModel, notifier=None):
        self.model = model
        self.notifier = notifier
        self.resultado_atual = {}
        self.limite_arquivos = None
        self.arquivos_rejeitados = []  # Arquivos que não passaram na validação
        self.arquivos_schema_diferente = []  # Arquivos com schema incompatível
        
    def set_limite_arquivos(self, limite: int):
        """Define quantos arquivos processar"""
        self.limite_arquivos = limite
        logger.info(f"🔧 Limite de arquivos definido para: {limite}")
    
    def analisar_schema_arquivo(self, arquivo_path: str) -> Dict[str, Any]:
        """
        Analisa o schema de um arquivo JSON e retorna sua estrutura
        """
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            schema = {
                'campos_raiz': set(data.keys()),
                'tem_analise_json': 'analise_json' in data,
                'tem_nodes': False,
                'tem_edges': False,
                'tipos_nodes': set(),
                'tipos_edges': set(),
                'total_nodes': 0,
                'total_edges': 0,
                'estrutura_valida': False
            }
            
            if 'analise_json' in data and isinstance(data['analise_json'], dict):
                analise_json = data['analise_json']
                schema['tem_nodes'] = 'nodes' in analise_json
                schema['tem_edges'] = 'edges' in analise_json
                
                if schema['tem_nodes'] and isinstance(analise_json['nodes'], list):
                    schema['total_nodes'] = len(analise_json['nodes'])
                    # Analisa tipos de nodes
                    for node in analise_json['nodes'][:10]:  # Amostra dos primeiros 10
                        if isinstance(node, dict):
                            node_type = node.get('type', 'unknown')
                            schema['tipos_nodes'].add(node_type)
                
                if schema['tem_edges'] and isinstance(analise_json['edges'], list):
                    schema['total_edges'] = len(analise_json['edges'])
                    # Analisa tipos de edges
                    for edge in analise_json['edges'][:10]:  # Amostra dos primeiros 10
                        if isinstance(edge, dict):
                            edge_type = edge.get('type', 'unknown')
                            schema['tipos_edges'].add(edge_type)
                
                schema['estrutura_valida'] = schema['tem_nodes'] or schema['tem_edges']
            
            return schema
            
        except Exception as e:
            return {
                'erro': str(e),
                'estrutura_valida': False
            }
    
    def validar_consistencia_arquivo(self, arquivo_path: str) -> Tuple[bool, str]:
        """
        Valida a consistência de um arquivo JSON
        Retorna (é_válido, mensagem_erro)
        """
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificação básica de estrutura
            if not isinstance(data, dict):
                return False, "Estrutura raiz não é um dicionário"
            
            if 'analise_json' not in data:
                return False, "Campo 'analise_json' não encontrado"
            
            analise_json = data.get('analise_json', {})
            if not isinstance(analise_json, dict):
                return False, "analise_json não é um dicionário"
            
            # Valida nodes
            if 'nodes' in analise_json:
                nodes = analise_json['nodes']
                if not isinstance(nodes, list):
                    return False, "nodes não é uma lista"
                
                for i, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        return False, f"Node {i} não é um dicionário"
                    
                    node_id = self.model._extrair_node_id(node)
                    if not node_id:
                        return False, f"Node {i} sem ID válido"
            
            # Valida edges
            if 'edges' in analise_json:
                edges = analise_json['edges']
                if not isinstance(edges, list):
                    return False, "edges não é uma lista"
                
                for i, edge in enumerate(edges):
                    if not isinstance(edge, dict):
                        return False, f"Edge {i} não é um dicionário"
                    
                    source = edge.get('source') or edge.get('from')
                    target = edge.get('target') or edge.get('to')
                    
                    if not source or not target:
                        return False, f"Edge {i} sem source ou target válidos"
            
            return True, "OK"
            
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {str(e)}"
        except Exception as e:
            return False, f"Erro na leitura: {str(e)}"
    
    def encontrar_schema_mais_comum(self, schemas: List[Dict]) -> Dict:
        """
        Encontra o schema mais comum entre os arquivos válidos
        """
        if not schemas:
            return {}
        
        # Conta frequência de campos
        campos_frequentes = Counter()
        tipos_nodes_frequentes = Counter()
        tipos_edges_frequentes = Counter()
        
        for schema in schemas:
            if schema.get('estrutura_valida'):
                campos_frequentes.update(schema.get('campos_raiz', set()))
                tipos_nodes_frequentes.update(schema.get('tipos_nodes', set()))
                tipos_edges_frequentes.update(schema.get('tipos_edges', set()))
        
        schema_comum = {
            'campos_raiz_mais_comuns': campos_frequentes.most_common(5),
            'tipos_nodes_mais_comuns': tipos_nodes_frequentes.most_common(5),
            'tipos_edges_mais_comuns': tipos_edges_frequentes.most_common(5),
            'total_arquivos_analisados': len(schemas),
            'arquivos_validos': len([s for s in schemas if s.get('estrutura_valida')])
        }
        
        return schema_comum
    
    def encontrar_arquivos_json(self, diretorio: str = "storage/data") -> List[str]:
        """Encontra e SELECIONA arquivos JSON com schemas consistentes"""
        try:
            logger.info(f"🔍 Procurando e validando arquivos em: {diretorio}")
            
            if not os.path.exists(diretorio):
                logger.error(f"❌ Diretório não encontrado: {diretorio}")
                if self.notifier:
                    self.notifier.error(f"Diretório não encontrado: {diretorio}")
                return []
            
            # Lista todos os arquivos JSON
            arquivos_encontrados = []
            for root, dirs, files in os.walk(diretorio):
                for file in files:
                    if file.endswith('.json'):
                        full_path = os.path.join(root, file)
                        arquivos_encontrados.append(full_path)
            
            logger.info(f"📁 Encontrados {len(arquivos_encontrados)} arquivos JSON totais")
            
            # Reset listas de rejeição
            self.arquivos_rejeitados = []
            self.arquivos_schema_diferente = []
            
            # Fase 1: Validação básica e análise de schema
            arquivos_validos = []
            schemas_analisados = []
            
            logger.info("🔄 Fase 1: Validando consistência dos arquivos...")
            
            for arquivo in arquivos_encontrados:
                nome_arquivo = os.path.basename(arquivo)
                
                # Valida consistência
                valido, mensagem_erro = self.validar_consistencia_arquivo(arquivo)
                
                if not valido:
                    self.arquivos_rejeitados.append({
                        'arquivo': nome_arquivo,
                        'motivo': 'INCONSISTENTE',
                        'erro': mensagem_erro,
                        'caminho': arquivo
                    })
                    logger.warning(f"❌ Arquivo inconsistente: {nome_arquivo} - {mensagem_erro}")
                    continue
                
                # Analisa schema
                schema = self.analisar_schema_arquivo(arquivo)
                schema['arquivo'] = nome_arquivo
                schemas_analisados.append(schema)
                
                if schema.get('estrutura_valida'):
                    arquivos_validos.append(arquivo)
                    logger.debug(f"✅ Arquivo válido: {nome_arquivo}")
                else:
                    self.arquivos_rejeitados.append({
                        'arquivo': nome_arquivo,
                        'motivo': 'SCHEMA_INVALIDO',
                        'erro': schema.get('erro', 'Estrutura inválida'),
                        'caminho': arquivo
                    })
                    logger.warning(f"❌ Schema inválido: {nome_arquivo}")
            
            logger.info(f"📊 Validação básica: {len(arquivos_validos)} válidos de {len(arquivos_encontrados)}")
            
            # Fase 2: Agrupamento por schema similar
            if arquivos_validos:
                logger.info("🔄 Fase 2: Analisando similaridade de schemas...")
                
                # Encontra schema mais comum
                schema_comum = self.encontrar_schema_mais_comum(schemas_analisados)
                
                # Seleciona arquivos com schema similar
                arquivos_selecionados = self._selecionar_arquivos_schema_similar(
                    arquivos_validos, schemas_analisados, schema_comum
                )
                
                logger.info(f"🎯 Schemas similares: {len(arquivos_selecionados)} de {len(arquivos_validos)} arquivos válidos")
            else:
                arquivos_selecionados = []
            
            # Aplica limite se definido
            if self.limite_arquivos and self.limite_arquivos > 0 and len(arquivos_selecionados) > self.limite_arquivos:
                arquivos_originais = len(arquivos_selecionados)
                arquivos_selecionados = arquivos_selecionados[:self.limite_arquivos]
                logger.info(f"⏹️  LIMITE: Processando {len(arquivos_selecionados)} de {arquivos_originais} arquivos")
            
            # Gera relatório de seleção
            self._gerar_relatorio_selecao(arquivos_selecionados)
            
            return arquivos_selecionados
            
        except Exception as e:
            logger.error(f"💥 Erro ao encontrar arquivos JSON: {e}")
            if self.notifier:
                self.notifier.error(f"Erro ao buscar arquivos: {str(e)}")
            return []
    
    def _selecionar_arquivos_schema_similar(self, arquivos_validos: List[str], 
                                          schemas_analisados: List[Dict], 
                                          schema_comum: Dict) -> List[str]:
        """
        Seleciona arquivos com schema similar ao mais comum
        """
        if not schemas_analisados:
            return arquivos_validos
        
        arquivos_selecionados = []
        
        # Pega os campos mais comuns do schema
        campos_comuns = [campo for campo, _ in schema_comum.get('campos_raiz_mais_comuns', [])[:3]]
        tipos_nodes_comuns = [tipo for tipo, _ in schema_comum.get('tipos_nodes_mais_comuns', [])[:3]]
        
        logger.info(f"📋 Schema de referência: campos={campos_comuns}, node_types={tipos_nodes_comuns}")
        
        for i, schema in enumerate(schemas_analisados):
            if not schema.get('estrutura_valida'):
                continue
            
            arquivo_path = arquivos_validos[i]
            nome_arquivo = schema['arquivo']
            
            # Calcula similaridade com schema comum
            similaridade = self._calcular_similaridade_schema(schema, campos_comuns, tipos_nodes_comuns)
            
            # Define threshold de similaridade (70%)
            if similaridade >= 0.7:
                arquivos_selecionados.append(arquivo_path)
                logger.debug(f"✅ Schema similar: {nome_arquivo} (similaridade: {similaridade:.2f})")
            else:
                self.arquivos_schema_diferente.append({
                    'arquivo': nome_arquivo,
                    'similaridade': similaridade,
                    'schema': schema,
                    'caminho': arquivo_path
                })
                logger.warning(f"🔶 Schema diferente: {nome_arquivo} (similaridade: {similaridade:.2f})")
        
        return arquivos_selecionados
    
    def _calcular_similaridade_schema(self, schema: Dict, campos_comuns: List[str], 
                                    tipos_nodes_comuns: List[str]) -> float:
        """
        Calcula similaridade entre um schema e o schema de referência
        """
        similaridade = 0.0
        fatores = 0
        
        # Similaridade de campos raiz
        if schema.get('campos_raiz'):
            campos_arquivo = schema['campos_raiz']
            campos_comuns_count = sum(1 for campo in campos_comuns if campo in campos_arquivo)
            similaridade += campos_comuns_count / max(len(campos_comuns), 1)
            fatores += 1
        
        # Similaridade de tipos de nodes
        if schema.get('tipos_nodes'):
            tipos_arquivo = schema['tipos_nodes']
            tipos_comuns_count = sum(1 for tipo in tipos_nodes_comuns if tipo in tipos_arquivo)
            similaridade += tipos_comuns_count / max(len(tipos_nodes_comuns), 1)
            fatores += 1
        
        # Presença de estrutura básica
        if schema.get('tem_nodes') and schema.get('tem_edges'):
            similaridade += 1.0
            fatores += 1
        
        return similaridade / fatores if fatores > 0 else 0.0
    
    def _gerar_relatorio_selecao(self, arquivos_selecionados: List[str]):
        """Gera relatório detalhado da seleção de arquivos"""
        total_encontrados = len(arquivos_selecionados) + len(self.arquivos_rejeitados) + len(self.arquivos_schema_diferente)
        
        logger.info("📊 RELATÓRIO DE SELEÇÃO DE ARQUIVOS:")
        logger.info(f"   📁 Total encontrados: {total_encontrados}")
        logger.info(f"   ✅ Selecionados: {len(arquivos_selecionados)}")
        logger.info(f"   ❌ Rejeitados (inconsistentes): {len(self.arquivos_rejeitados)}")
        logger.info(f"   🔶 Ignorados (schema diferente): {len(self.arquivos_schema_diferente)}")
        
        # Lista arquivos selecionados
        if arquivos_selecionados:
            logger.info("   📋 ARQUIVOS SELECIONADOS:")
            for i, arquivo in enumerate(arquivos_selecionados[:10]):
                logger.info(f"      {i+1}. {os.path.basename(arquivo)}")
            if len(arquivos_selecionados) > 10:
                logger.info(f"      ... e mais {len(arquivos_selecionados) - 10} arquivos")
        
        # Lista arquivos rejeitados (apenas os primeiros)
        if self.arquivos_rejeitados:
            logger.info("   🗑️  ARQUIVOS REJEITADOS (inconsistentes):")
            for problema in self.arquivos_rejeitados[:5]:
                logger.info(f"      ❌ {problema['arquivo']}: {problema['erro']}")
            if len(self.arquivos_rejeitados) > 5:
                logger.info(f"      ... e mais {len(self.arquivos_rejeitados) - 5} arquivos")
        
        # Lista arquivos com schema diferente (apenas os primeiros)
        if self.arquivos_schema_diferente:
            logger.info("   🔶 ARQUIVOS IGNORADOS (schema diferente):")
            for problema in self.arquivos_schema_diferente[:5]:
                logger.info(f"      🔶 {problema['arquivo']}: similaridade {problema['similaridade']:.2f}")
            if len(self.arquivos_schema_diferente) > 5:
                logger.info(f"      ... e mais {len(self.arquivos_schema_diferente) - 5} arquivos")

    def detectar_comunidades(self) -> Dict[int, List[str]]:
        """Detecta comunidades usando o model (evita duplicação de código)"""
        # Usa o model para detectar comunidades (evita duplicação)
        if hasattr(self, 'model') and self.model:
            return self.model.detectar_comunidades()

        # Fallback se model não estiver disponível
        return {}
    
    def processar_grafo(self, arquivos_json: List[str] = None) -> Dict[str, Any]:
        """Processa os arquivos JSON selecionados por consistência"""
        try:
            start_time = time.time()
            
            logger.info("🚀 INICIANDO PROCESSAMENTO DO GRAFO COM VALIDAÇÃO")
            
            if not arquivos_json:
                arquivos_json = self.encontrar_arquivos_json()
                
            if not arquivos_json:
                logger.error("❌ Nenhum arquivo consistente encontrado após validação")
                if self.notifier:
                    mensagem_erro = "Nenhum arquivo com schema consistente encontrado"
                    if self.arquivos_rejeitados or self.arquivos_schema_diferente:
                        mensagem_erro += f". {len(self.arquivos_rejeitados)} inconsistentes, {len(self.arquivos_schema_diferente)} com schema diferente"
                    self.notifier.error(mensagem_erro)
                return {}
            
            # Notifica sobre a seleção
            if self.notifier:
                mensagem_selecao = f"Selecionados {len(arquivos_json)} arquivos consistentes"
                if self.arquivos_rejeitados:
                    mensagem_selecao += f", {len(self.arquivos_rejeitados)} rejeitados"
                if self.arquivos_schema_diferente:
                    mensagem_selecao += f", {len(self.arquivos_schema_diferente)} com schema diferente"
                self.notifier.info(mensagem_selecao)
            
            logger.info(f"🎯 Processando {len(arquivos_json)} arquivos consistentes...")
            
            # Carrega grafo
            logger.info("🔄 Carregando grafo a partir dos arquivos selecionados...")
            grafo = self.model.carregar_json_para_grafo(arquivos_json)
            
            if grafo.number_of_nodes() == 0:
                logger.error("❌ Grafo vazio - nenhum nó válido nos arquivos selecionados")
                if self.notifier:
                    self.notifier.error("Nenhum dado válido nos arquivos selecionados")
                return {}
            
            logger.info(f"✅ Grafo carregado: {grafo.number_of_nodes()} nós, {grafo.number_of_edges()} arestas")
            
            # Detecta comunidades
            logger.info("🔄 Detectando comunidades...")
            comunidades = self.model.detectar_comunidades()
            
            # Gera visualização
            logger.info("🔄 Gerando visualização HTML...")
            html_path = self.model.gerar_html_visualizacao()
            
            # Estatísticas
            estatisticas = self.model.obter_estatisticas()
            
            processing_time = time.time() - start_time
            
            self.resultado_atual = {
                "grafo": grafo,
                "comunidades": comunidades,
                "html_path": html_path,
                "estatisticas": estatisticas,
                "arquivos_processados": len(arquivos_json),
                "arquivos_rejeitados": self.arquivos_rejeitados,
                "arquivos_schema_diferente": self.arquivos_schema_diferente,
                "limite_aplicado": self.limite_arquivos,
                "tempo_processamento": round(processing_time, 2)
            }
            
            # Mensagem final
            msg_final = (
                f"Processamento concluído! "
                f"{len(arquivos_json)} arquivos consistentes, "
                f"{grafo.number_of_nodes()} nós, {grafo.number_of_edges()} arestas"
            )
            
            logger.info(f"🎉 {msg_final}")
            
            if self.notifier:
                self.notifier.success(msg_final)
                
            return self.resultado_atual
            
        except Exception as e:
            logger.error(f"💥 Erro ao processar grafo: {e}")
            if self.notifier:
                self.notifier.error(f"Erro ao processar grafo: {str(e)}")
            return {}
    
    def obter_resultado_grafo(self) -> Dict[str, Any]:
        """Retorna resultado para dashboard incluindo informações de rejeição"""
        try:
            resultado = self.get_resultado_atual()
            
            if not resultado:
                return {}
            
            grafo = resultado.get('grafo')
            estatisticas = resultado.get('estatisticas', {})
            comunidades = resultado.get('comunidades', {})
            arquivos_rejeitados = resultado.get('arquivos_rejeitados', [])
            arquivos_schema_diferente = resultado.get('arquivos_schema_diferente', [])
            
            # Prepara nós críticos
            nos_criticos = []
            if grafo and grafo.number_of_nodes() > 0:
                try:
                    degrees = dict(grafo.degree())
                    top_nos = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
                    
                    for node_id, grau in top_nos:
                        centralidade = grau / (grafo.number_of_nodes() - 1) if grafo.number_of_nodes() > 1 else 0
                        nos_criticos.append({
                            'node_id': node_id,
                            'centralidade_grau': round(centralidade, 4),
                            'tipo': 'Hub' if grau > 5 else 'Normal'
                        })
                except Exception as e:
                    logger.warning(f"Erro ao calcular nós críticos: {e}")
            
            return {
                'grafo': grafo,
                'estatisticas': estatisticas,
                'comunidades': comunidades,
                'nos_criticos': nos_criticos,
                'arquivos_processados': resultado.get('arquivos_processados', 0),
                'arquivos_rejeitados': arquivos_rejeitados,
                'arquivos_schema_diferente': arquivos_schema_diferente,
                'limite_aplicado': resultado.get('limite_aplicado'),
                'tempo_processamento': resultado.get('tempo_processamento', 0),
                'html_path': resultado.get('html_path', '')
            }
            
        except Exception as e:
            logger.error(f"Erro em obter_resultado_grafo: {e}")
            return {}
    
    def get_arquivos_rejeitados(self) -> List[Dict]:
        """Retorna lista de arquivos rejeitados"""
        return self.arquivos_rejeitados
    
    def get_arquivos_schema_diferente(self) -> List[Dict]:
        """Retorna lista de arquivos com schema diferente"""
        return self.arquivos_schema_diferente
    
    def get_relatorio_selecao(self) -> str:
        """Gera relatório completo da seleção"""
        total_selecionados = len(self.resultado_atual.get('arquivos_processados', []))
        total_rejeitados = len(self.arquivos_rejeitados)
        total_schema_diferente = len(self.arquivos_schema_diferente)
        
        relatorio = f"📊 RELATÓRIO COMPLETO DE SELEÇÃO:\n\n"
        relatorio += f"✅ Selecionados: {total_selecionados} arquivos\n"
        relatorio += f"❌ Rejeitados: {total_rejeitados} arquivos\n"
        relatorio += f"🔶 Schema diferente: {total_schema_diferente} arquivos\n\n"
        
        if self.arquivos_rejeitados:
            relatorio += "🗑️  ARQUIVOS REJEITADOS:\n"
            for problema in self.arquivos_rejeitados[:10]:
                relatorio += f"   ❌ {problema['arquivo']}: {problema['erro']}\n"
        
        if self.arquivos_schema_diferente:
            relatorio += "\n🔶 ARQUIVOS COM SCHEMA DIFERENTE:\n"
            for problema in self.arquivos_schema_diferente[:10]:
                relatorio += f"   🔶 {problema['arquivo']}: similaridade {problema['similaridade']:.2f}\n"
        
        return relatorio

    # Métodos auxiliares mantidos para compatibilidade
    def _is_analise_valida(self, data: Dict) -> bool:
        """Método legado para compatibilidade"""
        valido, _ = self.validar_consistencia_arquivo_from_data(data)
        return valido

    def validar_consistencia_arquivo_from_data(self, data: Dict) -> Tuple[bool, str]:
        """Valida consistência a partir de dados já carregados"""
        try:
            if not isinstance(data, dict):
                return False, "Estrutura raiz não é um dicionário"
            
            if 'analise_json' not in data:
                return False, "Campo 'analise_json' não encontrado"
            
            analise_json = data.get('analise_json', {})
            if not isinstance(analise_json, dict):
                return False, "analise_json não é um dicionário"
            
            return True, "OK"
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"

    def _is_arquivo_analise_valido(self, arquivo_path: str) -> bool:
        """Método legado para compatibilidade"""
        valido, _ = self.validar_consistencia_arquivo(arquivo_path)
        return valido

    def get_resultado_atual(self) -> Dict[str, Any]:
        return self.resultado_atual
    
    def get_estatisticas(self) -> Dict[str, Any]:
        return self.resultado_atual.get('estatisticas', {})
    
    def get_comunidades(self) -> Dict[int, List[str]]:
        return self.resultado_atual.get('comunidades', {})
    
    def get_caminho_visualizacao(self) -> str:
        return self.resultado_atual.get('html_path', '')
    
    def get_limite_aplicado(self) -> int:
        return self.limite_arquivos or 0
    
    def limpar_resultados(self):
        self.resultado_atual = {}
        self.arquivos_rejeitados = []
        self.arquivos_schema_diferente = []
        logger.info("🧹 Resultados do grafo limpos")