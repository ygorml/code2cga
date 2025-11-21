# grafo/model.py

import os
import json
import networkx as nx
import logging
from pyvis.network import Network
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

"""
Model do módulo de grafos.

Responsável por processar dados de grafos e suas estruturas.
"""

HAS_LOUVAIN = False
community_louvain = None

try:
    # Tenta importar python-louvain (nome atual do pacote)
    import community as community_louvain
    # Verifica se best_partition está disponível
    if hasattr(community_louvain, 'best_partition'):
        HAS_LOUVAIN = True
        logger.info("Biblioteca python-louvain carregada com sucesso")
    else:
        logger.warning("Biblioteca community encontrada mas best_partition não disponível")
        community_louvain = None
except ImportError:
    try:
        # Tenta com o novo nome do pacote
        import python_louvain as community_louvain
        if hasattr(community_louvain, 'best_partition'):
            HAS_LOUVAIN = True
            logger.info("Biblioteca python-louvain carregada com sucesso (novo nome)")
        else:
            logger.warning("Biblioteca python-louvain encontrada mas best_partition não disponível")
            community_louvain = None
    except ImportError:
        logger.warning("⚠️  Biblioteca python-louvain não encontrada. Usando apenas detecção básica de comunidades.")
        logger.info("   Para instalar: pip install python-louvain")
        community_louvain = None

class GrafoModel:
    def __init__(self, notifier=None):
        self.notifier = notifier
        self.graph = None
        self.communities = {}
        # Garante que a pasta de grafos existe
        self.grafo_dir = "grafo_gerado"
        os.makedirs(self.grafo_dir, exist_ok=True)
        
    def carregar_json_para_grafo(self, json_files: List[str]) -> nx.DiGraph:
        """Carrega múltiplos arquivos JSON e constrói um grafo consolidado - VERSÃO CORRIGIDA"""
        G = nx.DiGraph()
        arquivos_processados = 0
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Verifica se é um arquivo de análise válido
                if 'analise_json' not in data:
                    logger.debug(f"Arquivo {file_path} não contém análise JSON, pulando...")
                    continue

                analise_json = data['analise_json']
                arquivos_processados += 1

                # Adiciona nós - VERSÃO CORRIGIDA
                if 'nodes' in analise_json:
                    for node in analise_json['nodes']:
                        # Extrai ID do nó de forma robusta
                        node_id = self._extrair_node_id(node)
                        if not node_id:
                            continue

                        if not G.has_node(node_id):
                            attributes = self._extrair_node_attributes(node, node_id)
                            G.add_node(node_id, **attributes)
                            logger.debug(f"Adicionado nó: {node_id}")

                # Adiciona arestas - VERSÃO CORRIGIDA
                if 'edges' in analise_json:
                    for edge in analise_json['edges']:
                        source, target = self._extrair_edge_nodes(edge)
                        
                        if source and target and source != target:
                            if not G.has_node(source): 
                                G.add_node(source, label=source, type='External', group='External', color='#ff9999')
                            if not G.has_node(target): 
                                G.add_node(target, label=target, type='External', group='External', color='#ff9999')

                            if not G.has_edge(source, target):
                                edge_attrs = self._extrair_edge_attributes(edge)
                                G.add_edge(source, target, **edge_attrs)
                                logger.debug(f"Adicionada aresta: {source} -> {target}")
                                     
            except Exception as e:
                logger.error(f"Erro ao carregar {file_path}: {e}")
                if self.notifier:
                    self.notifier.error(f"Erro ao carregar {os.path.basename(file_path)}")

        self.graph = G
        logger.info(f"Grafo criado com {G.number_of_nodes()} nós e {G.number_of_edges()} arestas de {arquivos_processados} arquivos processados")
        
        if self.notifier:
            self.notifier.info(f"Grafo criado: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
            
        return G
    
    def _extrair_node_id(self, node: Dict) -> Optional[str]:
        """Extrai ID do nó de forma robusta"""
        # Tenta diferentes campos possíveis para ID
        for field in ['id', 'name', 'label', 'title']:
            if field in node and node[field]:
                return str(node[field]).strip()
        return None
    
    def _extrair_node_attributes(self, node: Dict, node_id: str) -> Dict[str, Any]:
        """Extrai atributos do nó de forma robusta"""
        # Atributos padrão
        attributes = {
            'label': node.get('label', node_id),
            'type': node.get('type', 'Unknown'),
            'group': node.get('group', 'Default'),
            'shape': node.get('shape', 'ellipse'),
            'color': self._parse_color(node.get('color', '#97c2fc')),
            'title': self._build_node_tooltip(node, node_id),
            'size': node.get('size', 25)
        }
        
        # Adiciona metadados se existirem
        if 'metadata' in node:
            attributes['metadata'] = node['metadata']
            
        return attributes
    
    def _parse_color(self, color_value) -> str:
        """Converte cor para formato válido"""
        if isinstance(color_value, dict):
            return color_value.get('background', '#97c2fc')
        elif isinstance(color_value, str):
            return color_value
        else:
            return '#97c2fc'
    
    def _build_node_tooltip(self, node: Dict, node_id: str) -> str:
        """Constrói tooltip informativo para o nó"""
        tooltip_parts = [f"ID: {node_id}"]
        
        if 'type' in node:
            tooltip_parts.append(f"Type: {node['type']}")
        if 'group' in node:
            tooltip_parts.append(f"Group: {node['group']}")
        if 'description' in node:
            tooltip_parts.append(f"Desc: {node['description']}")
            
        return "<br>".join(tooltip_parts)
    
    def _extrair_edge_nodes(self, edge: Dict) -> tuple:
        """Extrai nós de origem e destino da aresta"""
        source = edge.get('from') or edge.get('source') or edge.get('start')
        target = edge.get('to') or edge.get('target') or edge.get('end')
        
        return str(source).strip() if source else None, str(target).strip() if target else None
    
    def _extrair_edge_attributes(self, edge: Dict) -> Dict[str, Any]:
        """Extrai atributos da aresta"""
        attributes = {
            'label': edge.get('label', ''),
            'title': edge.get('title', edge.get('label', '')),
            'width': edge.get('width', 1),
            'color': edge.get('color', '#848484'),
            'arrows': edge.get('arrows', 'to')
        }
        
        # Adiciona metadados se existirem
        if 'metadata' in edge:
            attributes['metadata'] = edge['metadata']
            
        return attributes
    
    def detectar_comunidades(self) -> Dict[int, List[str]]:
        """Detecta comunidades usando o algoritmo de Louvain - VERSÃO CORRIGIDA"""
        if not self.graph or self.graph.number_of_nodes() == 0:
            logger.warning("Grafo vazio, não é possível detectar comunidades")
            return {}
            
        try:
            # Verifica se a biblioteca está disponível
            if not HAS_LOUVAIN:
                logger.warning("Biblioteca python-louvain não disponível. Usando detecção básica.")
                return self._detectar_comunidades_basico()
                
            # Converte para grafo não direcionado para detecção de comunidades
            G_undirected = self.graph.to_undirected()
            
            # Remove nós isolados para melhor detecção
            G_undirected.remove_nodes_from(list(nx.isolates(G_undirected)))
            
            if G_undirected.number_of_nodes() == 0:
                logger.warning("Nenhum nó conectado para detecção de comunidades")
                return {}
                
            # Detecta comunidades usando Louvain
            partition = community_louvain.best_partition(G_undirected)

            # Adiciona informação de comunidade ao grafo original
            for node, community_id in partition.items():
                if node in self.graph.nodes:
                    self.graph.nodes[node]['community'] = community_id
                    self.graph.nodes[node]['group'] = f"Community_{community_id}"

            # Organiza comunidades
            communities = {}
            for node, community_id in partition.items():
                if node in self.graph.nodes:
                    if community_id not in communities:
                        communities[community_id] = []
                    node_label = self.graph.nodes[node].get('label', node)
                    communities[community_id].append(node_label)

            self.communities = communities
            logger.info(f"Detectadas {len(communities)} comunidades usando Louvain")
            
            if self.notifier:
                self.notifier.info(f"Detectadas {len(communities)} comunidades")
                
            return communities
            
        except Exception as e:
            logger.error(f"Erro ao detectar comunidades com Louvain: {e}")
            logger.info("Tentando detecção básica...")
            return self._detectar_comunidades_basico()
    
    def gerar_html_visualizacao(self, output_filename: str = "grafo_visualizacao.html") -> str:
        """Gera arquivo HTML para visualização do grafo usando PyVis - VERSÃO CORRIGIDA"""
        if not self.graph or self.graph.number_of_nodes() == 0:
            raise ValueError("Grafo vazio ou não carregado")
            
        try:
            # Define o caminho completo na pasta grafo_gerado
            output_path = os.path.join(self.grafo_dir, output_filename)
            
            # Cria rede PyVis
            net = Network(
                height="750px", 
                width="100%", 
                bgcolor="#ffffff", 
                font_color="black", 
                directed=True,
                notebook=False
            )
            
            # Mapeamento de cores para comunidades
            community_colors = {
                0: '#97c2fc', 1: '#fb7e81', 2: '#7bf1a8', 3: '#ffb144',
                4: '#ca8bfe', 5: '#ffeb3b', 6: '#9c27b0', 7: '#00bcd4',
                8: '#8bc34a', 9: '#ff5722'
            }
            
            # Adiciona nós
            for node_id, node_data in self.graph.nodes(data=True):
                community_id = node_data.get('community', 0)
                color = community_colors.get(community_id % len(community_colors), '#97c2fc')
                
                net.add_node(
                    node_id,
                    label=node_data.get('label', node_id),
                    title=node_data.get('title', ''),
                    color=color,
                    shape=node_data.get('shape', 'ellipse'),
                    size=node_data.get('size', 25),
                    group=community_id
                )
            
            # Adiciona arestas
            for source, target, edge_data in self.graph.edges(data=True):
                net.add_edge(
                    source, 
                    target,
                    title=edge_data.get('title', ''),
                    width=edge_data.get('width', 1),
                    color=edge_data.get('color', '#848484'),
                    arrows=edge_data.get('arrows', 'to')
                )
            
            # Configurações avançadas da visualização
            net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "stabilization": {
                  "iterations": 100,
                  "updateInterval": 10
                },
                "barnesHut": {
                  "gravitationalConstant": -8000,
                  "centralGravity": 0.3,
                  "springLength": 95,
                  "springConstant": 0.04,
                  "damping": 0.09
                }
              },
              "interaction": {
                "hover": true,
                "tooltipDelay": 100,
                "keyboard": true,
                "navigationButtons": true
              },
              "layout": {
                "improvedLayout": true,
                "hierarchical": {
                  "enabled": false
                }
              },
              "nodes": {
                "font": {
                  "size": 14,
                  "face": "Tahoma"
                },
                "scaling": {
                  "min": 10,
                  "max": 30
                }
              },
              "edges": {
                "smooth": {
                  "enabled": true,
                  "type": "continuous"
                },
                "font": {
                  "size": 12,
                  "face": "Tahoma"
                }
              }
            }
            """)
            
            net.save_graph(output_path)
            logger.info(f"Visualização do grafo salva em: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar visualização HTML: {e}")
            if self.notifier:
                self.notifier.error(f"Erro ao gerar visualização: {str(e)}")
            raise
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do grafo - VERSÃO CORRIGIDA"""
        if not self.graph:
            return {}
            
        try:
            # Cálculos robustos
            num_nos = self.graph.number_of_nodes()
            num_arestas = self.graph.number_of_edges()
            
            # Grau médio (evita divisão por zero)
            grau_medio = 0
            if num_nos > 0:
                degrees = dict(self.graph.degree())
                grau_medio = sum(degrees.values()) / num_nos
            
            # Densidade (evita divisão por zero)
            densidade = 0
            if num_nos > 1:
                densidade = nx.density(self.graph)
            
            # Componentes conectados
            componentes = list(nx.weakly_connected_components(self.graph))
            maior_componente = max(len(comp) for comp in componentes) if componentes else 0
            
            return {
                "num_nos": num_nos,
                "num_arestas": num_arestas,
                "num_comunidades": len(self.communities),
                "densidade": round(densidade, 4),
                "grau_medio": round(grau_medio, 2),
                "componentes_conectados": len(componentes),
                "maior_componente": maior_componente,
                "nos_isolados": len(list(nx.isolates(self.graph)))
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def _detectar_comunidades_basico(self) -> Dict[int, List[str]]:
        """Detecção básica de comunidades usando componentes conectados"""
        try:
            if not self.graph:
                return {}
                
            # Usa componentes conectados fracos como comunidades básicas
            componentes = list(nx.weakly_connected_components(self.graph))
            communities = {}
            
            for i, componente in enumerate(componentes):
                community_id = i
                communities[community_id] = []
                
                for node in componente:
                    if node in self.graph.nodes:
                        self.graph.nodes[node]['community'] = community_id
                        self.graph.nodes[node]['group'] = f"Component_{community_id}"
                        node_label = self.graph.nodes[node].get('label', node)
                        communities[community_id].append(node_label)
            
            self.communities = communities
            logger.info(f"Detectadas {len(communities)} comunidades usando componentes conectados")
            
            if self.notifier:
                self.notifier.info(f"Detectadas {len(communities)} comunidades básicas")
                
            return communities
            
        except Exception as e:
            logger.error(f"Erro na detecção básica de comunidades: {e}")
            return {}
        
    def get_grafo_atual(self) -> Optional[nx.DiGraph]:
        """Retorna o grafo atual"""
        return self.graph
    
    def get_comunidades(self) -> Dict[int, List[str]]:
        """Retorna as comunidades detectadas"""
        return self.communities
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do grafo"""
        return self.obter_estatisticas()