# modules/dashboard/model.py

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
import networkx as nx
"""
Model do dashboard principal.

Gerencia os dados exibidos no dashboard da aplicação.
"""


logger = logging.getLogger(__name__)

class DashboardModel:
    def __init__(self, notifier):
        self.notifier = notifier
        self.historico_analises = []
        self.historico_analises_rag = []
        
    def calcular_metricas_avancadas(self, resultado_grafo: Dict[str, Any]) -> Any:
        """Calcula métricas avançadas do grafo"""
        try:
            # Cria um objeto simples para armazenar métricas
            class Metricas:
                def __init__(self):
                    self.acoplamento_medio = 0.0
                    self.coesao_media = 0.0
                    self.complexidade_ciclomatica_media = 0.0
                    self.centralidade_grau_maxima = 0.0
                    self.centralidade_intermediacao_maxima = 0.0
                    self.modularidade = 0.0
                    self.densidade = 0.0
                    self.diametro = 0
                    self.raio = 0
                    self.numero_componentes = 0
            
            metricas = Metricas()
            
            # Extrai estatísticas básicas
            estatisticas = resultado_grafo.get('estatisticas', {})
            
            # Calcula métricas baseadas nas estatísticas disponíveis
            num_nos = estatisticas.get('num_nos', 1)
            num_arestas = estatisticas.get('num_arestas', 0)
            grau_medio = estatisticas.get('grau_medio', 0)
            nos_isolados = estatisticas.get('nos_isolados', 0)
            densidade = estatisticas.get('densidade', 0)
            num_comunidades = estatisticas.get('num_comunidades', 1)
            grau_maximo = estatisticas.get('grau_maximo', 0)
            
            # Acoplamento médio (baseado no grau médio)
            metricas.acoplamento_medio = min(grau_medio / 10.0, 1.0)  # Normalizado
            
            # Coesão média (inversamente proporcional aos nós isolados)
            metricas.coesao_media = max(0, 1.0 - (nos_isolados / max(num_nos, 1)))
            
            # Densidade
            metricas.densidade = densidade
            
            # Número de componentes (comunidades)
            metricas.numero_componentes = max(num_comunidades, 1)
            
            # Modularidade (baseada na densidade e número de comunidades)
            if num_comunidades > 1:
                metricas.modularidade = min(densidade * num_comunidades / 10.0, 0.8)
            else:
                metricas.modularidade = min(densidade * 0.5, 0.6)
            
            # Centralidade máxima (baseada no grau máximo)
            metricas.centralidade_intermediacao_maxima = min(grau_maximo / max(num_nos * 0.5, 1), 1.0)
            metricas.centralidade_grau_maxima = metricas.centralidade_intermediacao_maxima
            
            # Complexidade ciclomática (estimativa baseada em arestas e nós)
            if num_nos > 0:
                metricas.complexidade_ciclomatica_media = max(1, (num_arestas - num_nos + 2) / max(num_nos, 1))
            else:
                metricas.complexidade_ciclomatica_media = 1.0
            
            # Diâmetro e raio (estimativas)
            metricas.diametro = min(max(3, int(num_nos / 10)), 10)
            metricas.raio = max(1, metricas.diametro - 2)
            
            logger.info(f"Métricas avançadas calculadas: "
                       f"acoplamento={metricas.acoplamento_medio:.2f}, "
                       f"coesao={metricas.coesao_media:.2f}, "
                       f"modularidade={metricas.modularidade:.3f}")
            
            return metricas
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas avançadas: {e}")
            # Retorna métricas padrão em caso de erro
            class Metricas:
                def __init__(self):
                    self.acoplamento_medio = 0.5
                    self.coesao_media = 0.6
                    self.complexidade_ciclomatica_media = 10.0
                    self.centralidade_grau_maxima = 0.3
                    self.centralidade_intermediacao_maxima = 0.2
                    self.modularidade = 0.4
                    self.densidade = 0.1
                    self.diametro = 5
                    self.raio = 2
                    self.numero_componentes = 3
            
            return Metricas()
    
    def gerar_storytelling(self, metricas, resultado_grafo: Dict[str, Any]) -> Dict[str, str]:
        """Gera narrativa contextual baseada nas métricas"""
        try:
            estatisticas = resultado_grafo.get('estatisticas', {})
            
            storytelling = {
                'resumo_geral': self._gerar_resumo_geral(metricas, estatisticas),
                'insights_tecnicos': self._gerar_insights_tecnicos(metricas, estatisticas),
                'pontos_atencao': self._gerar_pontos_atencao(metricas, estatisticas),
                'recomendacoes': self._gerar_recomendacoes(metricas, estatisticas)
            }
            
            logger.info("Storytelling gerado com sucesso")
            return storytelling
            
        except Exception as e:
            logger.error(f"Erro ao gerar storytelling: {e}")
            return {
                'resumo_geral': 'Análise contextual não disponível',
                'insights_tecnicos': 'Execute a análise completa para obter insights',
                'pontos_atencao': 'Nenhum ponto de atenção identificado',
                'recomendacoes': 'Execute a análise completa para obter recomendações'
            }
    
    def _gerar_resumo_geral(self, metricas, estatisticas: Dict[str, Any]) -> str:
        """Gera resumo geral da arquitetura"""
        num_nos = estatisticas.get('num_nos', 0)
        num_arestas = estatisticas.get('num_arestas', 0)
        num_comunidades = estatisticas.get('num_comunidades', 1)
        nos_isolados = estatisticas.get('nos_isolados', 0)
        
        # Avaliação geral baseada nas métricas
        if metricas.acoplamento_medio < 0.3 and metricas.coesao_media > 0.7:
            avaliacao = "boa qualidade arquitetural"
        elif metricas.acoplamento_medio > 0.7 or metricas.coesao_media < 0.3:
            avaliacao = "precisa de melhorias significativas"
        else:
            avaliacao = "qualidade moderada com oportunidades de melhoria"
        
        return (f"Sistema com {num_nos} componentes e {num_arestas} dependências, "
                f"organizado em {num_comunidades} comunidades principais. "
                f"Apresenta {avaliacao} com acoplamento médio de {metricas.acoplamento_medio:.2f} "
                f"e coesão de {metricas.coesao_media:.2f}. "
                f"{nos_isolados} componentes isolados identificados.")
    
    def _gerar_insights_tecnicos(self, metricas, estatisticas: Dict[str, Any]) -> str:
        """Gera insights técnicos"""
        insights = []
        
        # Análise de acoplamento
        if metricas.acoplamento_medio > 0.7:
            insights.append("Alto acoplamento detectado - sistema com muitas dependências entre componentes")
        elif metricas.acoplamento_medio > 0.4:
            insights.append("Acoplamento moderado - balanceamento razoável de dependências")
        else:
            insights.append("Baixo acoplamento - boa separação de concerns e independência entre componentes")
        
        # Análise de coesão
        if metricas.coesao_media > 0.8:
            insights.append("Alta coesão - componentes bem focados em responsabilidades específicas")
        elif metricas.coesao_media > 0.5:
            insights.append("Coesão moderada - alguns componentes podem beneficiar de refatoração")
        else:
            insights.append("Baixa coesão - componentes com responsabilidades muito diversificadas")
        
        # Análise de modularidade
        if metricas.modularidade > 0.6:
            insights.append("Boa modularidade - estrutura bem organizada em módulos coesos")
        elif metricas.modularidade > 0.3:
            insights.append("Modularidade moderada - oportunidades para melhor organização modular")
        else:
            insights.append("Baixa modularidade - estrutura pode ser melhor organizada em módulos")
        
        # Análise de complexidade
        if hasattr(metricas, 'complexidade_ciclomatica_media') and metricas.complexidade_ciclomatica_media > 15:
            insights.append("Alta complexidade ciclomática - considere simplificar a lógica dos componentes")
        elif hasattr(metricas, 'complexidade_ciclomatica_media') and metricas.complexidade_ciclomatica_media > 8:
            insights.append("Complexidade ciclomática moderada - monitorar evolução da complexidade")
        
        return " • " + "\n • ".join(insights) if insights else "Sistema com características balanceadas e organização adequada"
    
    def _gerar_pontos_atencao(self, metricas, estatisticas: Dict[str, Any]) -> str:
        """Gera pontos de atenção"""
        pontos = []
        
        num_nos = estatisticas.get('num_nos', 1)
        nos_isolados = estatisticas.get('nos_isolados', 0)
        
        # Componentes isolados
        if nos_isolados > num_nos * 0.2:
            pontos.append(f"Alto número de componentes isolados ({nos_isolados} de {num_nos}) - pode indicar dead code ou funcionalidades não integradas")
        elif nos_isolados > 0:
            pontos.append(f"Componentes isolados presentes ({nos_isolados}) - verificar se são necessários")
        
        # Centralidade excessiva
        if hasattr(metricas, 'centralidade_intermediacao_maxima') and metricas.centralidade_intermediacao_maxima > 0.8:
            pontos.append("Alta centralidade em poucos componentes - possíveis gargalos ou single points of failure")
        elif hasattr(metricas, 'centralidade_intermediacao_maxima') and metricas.centralidade_intermediacao_maxima > 0.6:
            pontos.append("Centralidade moderada-alta - monitorar componentes críticos")
        
        # Densidade
        if metricas.densidade > 0.7:
            pontos.append("Alta densidade de conexões - sistema fortemente acoplado, pode ser difícil de manter")
        elif metricas.densidade < 0.1:
            pontos.append("Baixa densidade - muitos componentes com poucas conexões, possivelmente subutilizados")
        
        # Acoplamento crítico
        if metricas.acoplamento_medio > 0.8:
            pontos.append("Acoplamento muito alto - impacto em mudanças pode ser significativo")
        
        # Coesão crítica
        if metricas.coesao_media < 0.3:
            pontos.append("Coesão muito baixa - componentes com responsabilidades muito dispersas")
        
        return " • " + "\n • ".join(pontos) if pontos else "Nenhum ponto crítico identificado - arquitetura apresenta características saudáveis"
    
    def _gerar_recomendacoes(self, metricas, estatisticas: Dict[str, Any]) -> str:
        """Gera recomendações de melhoria"""
        recomendacoes = []
        
        # Recomendações baseadas no acoplamento
        if metricas.acoplamento_medio > 0.7:
            recomendacoes.append("Refatorar para reduzir acoplamento: aplicar padrões como Dependency Injection, Interface Segregation")
        elif metricas.acoplamento_medio > 0.5:
            recomendacoes.append("Monitorar acoplamento: identificar componentes com muitas dependências para refatoração futura")
        
        # Recomendações baseadas na coesão
        if metricas.coesao_media < 0.4:
            recomendacoes.append("Aumentar coesão: dividir componentes grandes em responsabilidades mais específicas (Single Responsibility Principle)")
        elif metricas.coesao_media < 0.6:
            recomendacoes.append("Melhorar coesão: revisar componentes com múltiplas responsabilidades")
        
        # Recomendações baseadas na modularidade
        if metricas.modularidade < 0.4:
            recomendacoes.append("Melhorar modularidade: agrupar componentes relacionados em módulos coesos")
        
        # Recomendações baseadas em componentes isolados
        nos_isolados = estatisticas.get('nos_isolados', 0)
        if nos_isolados > 0:
            recomendacoes.append(f"Revisar {nos_isolados} componentes isolados: verificar se são necessários ou integrá-los ao sistema")
        
        # Recomendações gerais
        if not recomendacoes:
            recomendacoes.append("Manter boas práticas: continuar com a arquitetura atual, monitorando métricas regularmente")
            recomendacoes.append("Documentar decisões arquiteturais: manter documentação atualizada das escolhas de design")
        else:
            recomendacoes.append("Estabelecer métricas de acompanhamento: monitorar evolução das métricas após implementar melhorias")
            recomendacoes.append("Realizar code reviews focados: incluir verificação de aspectos arquiteturais nos reviews")
        
        return " • " + "\n • ".join(recomendacoes)
    
    def preparar_contexto_rag(self, metricas, resultado_grafo: Dict[str, Any], storytelling: Dict[str, str]) -> str:
        """Prepara contexto para análise RAG"""
        try:
            contexto = "CONTEXTO DA ANÁLISE DE ARQUITETURA:\n\n"
            
            # Estatísticas básicas
            estatisticas = resultado_grafo.get('estatisticas', {})
            contexto += "=== ESTATÍSTICAS GERAIS DO SISTEMA ===\n"
            contexto += f"• Total de componentes (nós): {estatisticas.get('num_nos', 'N/A')}\n"
            contexto += f"• Total de dependências (arestas): {estatisticas.get('num_arestas', 'N/A')}\n"
            contexto += f"• Comunidades detectadas: {estatisticas.get('num_comunidades', 'N/A')}\n"
            contexto += f"• Componentes isolados: {estatisticas.get('nos_isolados', 'N/A')}\n"
            contexto += f"• Densidade do grafo: {estatisticas.get('densidade', 'N/A')}\n"
            contexto += f"• Grau médio (conexões por componente): {estatisticas.get('grau_medio', 'N/A')}\n\n"
            
            # Métricas avançadas
            contexto += "=== MÉTRICAS DE QUALIDADE ARQUITETURAL ===\n"
            contexto += f"• Acoplamento médio: {metricas.acoplamento_medio:.3f} (0-1, menor é melhor)\n"
            contexto += f"• Coesão média: {getattr(metricas, 'coesao_media', 0):.3f} (0-1, maior é melhor)\n"
            contexto += f"• Modularidade: {getattr(metricas, 'modularidade', 0):.3f} (0-1, maior é melhor)\n"
            contexto += f"• Densidade: {getattr(metricas, 'densidade', 0):.3f} (0-1)\n"
            if hasattr(metricas, 'complexidade_ciclomatica_media'):
                contexto += f"• Complexidade ciclomática média: {metricas.complexidade_ciclomatica_media:.1f}\n"
            if hasattr(metricas, 'centralidade_intermediacao_maxima'):
                contexto += f"• Centralidade máxima (intermediação): {metricas.centralidade_intermediacao_maxima:.3f}\n"
            contexto += f"• Componentes conectados: {getattr(metricas, 'numero_componentes', 0)}\n\n"
            
            # Storytelling
            contexto += "=== ANÁLISE CONTEXTUAL E INTERPRETAÇÃO ===\n"
            contexto += f"RESUMO GERAL:\n{storytelling.get('resumo_geral', 'N/A')}\n\n"
            contexto += f"INSIGHTS TÉCNICOS:\n{storytelling.get('insights_tecnicos', 'N/A')}\n\n"
            contexto += f"PONTOS DE ATENÇÃO:\n{storytelling.get('pontos_atencao', 'N/A')}\n\n"
            contexto += f"RECOMENDAÇÕES:\n{storytelling.get('recomendacoes', 'N/A')}\n\n"
            
            contexto += "INSTRUÇÕES PARA ANÁLISE RAG:\n"
            contexto += "Com base nestas métricas e na análise contextual, forneça:\n"
            contexto += "1. Uma avaliação geral da qualidade arquitetural\n"
            contexto += "2. Identificação de padrões arquiteturais presentes\n"
            contexto += "3. Sugestões específicas de refatoração baseadas nos pontos de atenção\n"
            contexto += "4. Recomendações para melhorar métricas específicas (acoplamento, coesão, modularidade)\n"
            contexto += "5. Análise de trade-offs e impactos das mudanças sugeridas\n\n"
            
            contexto += "PERGUNTA DO USUÁRIO:\n"
            
            logger.info("Contexto RAG preparado com sucesso")
            return contexto
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto RAG: {e}")
            return "Contexto de análise não disponível. Execute a análise completa primeiro."
    
    def salvar_analise_historico(self, analise: Dict[str, Any]):
        """Salva análise no histórico"""
        try:
            analise_com_id = {
                'id': len(self.historico_analises) + 1,
                **analise
            }
            self.historico_analises.append(analise_com_id)
            
            # Mantém apenas as últimas 10 análises
            if len(self.historico_analises) > 10:
                self.historico_analises = self.historico_analises[-10:]
                
            logger.info(f"Análise {analise_com_id['id']} salva no histórico")
        except Exception as e:
            logger.error(f"Erro ao salvar análise no histórico: {e}")
    
    def salvar_analise_rag_historico(self, analise_rag: Dict[str, Any]):
        """Salva análise RAG no histórico"""
        try:
            analise_com_id = {
                'id': len(self.historico_analises_rag) + 1,
                **analise_rag
            }
            self.historico_analises_rag.append(analise_com_id)
            
            # Mantém apenas as últimas 20 análises RAG
            if len(self.historico_analises_rag) > 20:
                self.historico_analises_rag = self.historico_analises_rag[-20:]
                
            logger.info(f"Análise RAG {analise_com_id['id']} salva no histórico: {analise_rag['timestamp']}")
        except Exception as e:
            logger.error(f"Erro ao salvar análise RAG: {e}")
    
    def obter_historico_analises_rag(self) -> List[Dict[str, Any]]:
        """Obtém histórico de análises RAG"""
        try:
            # Retorna as análises mais recentes primeiro
            return sorted(self.historico_analises_rag, 
                         key=lambda x: x.get('timestamp', ''), 
                         reverse=True)
        except Exception as e:
            logger.error(f"Erro ao obter histórico RAG: {e}")
            return []
    
    def obter_historico_analises(self) -> List[Dict[str, Any]]:
        """Obtém histórico de análises completas"""
        try:
            return sorted(self.historico_analises,
                         key=lambda x: x.get('timestamp', ''),
                         reverse=True)
        except Exception as e:
            logger.error(f"Erro ao obter histórico de análises: {e}")
            return []
    
    def obter_analise_por_id(self, analise_id: int) -> Dict[str, Any]:
        """Obtém uma análise específica por ID"""
        try:
            for analise in self.historico_analises:
                if analise.get('id') == analise_id:
                    return analise
            return None
        except Exception as e:
            logger.error(f"Erro ao obter análise {analise_id}: {e}")
            return None
    
    def obter_analise_rag_por_id(self, analise_id: int) -> Dict[str, Any]:
        """Obtém uma análise RAG específica por ID"""
        try:
            for analise in self.historico_analises_rag:
                if analise.get('id') == analise_id:
                    return analise
            return None
        except Exception as e:
            logger.error(f"Erro ao obter análise RAG {analise_id}: {e}")
            return None
    
    def limpar_historico_analises(self):
        """Limpa o histórico de análises"""
        try:
            self.historico_analises.clear()
            logger.info("Histórico de análises limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
    
    def limpar_historico_analises_rag(self):
        """Limpa o histórico de análises RAG"""
        try:
            self.historico_analises_rag.clear()
            logger.info("Histórico de análises RAG limpo")
        except Exception as e:
            logger.error(f"Erro ao limpar histórico RAG: {e}")
    
    def obter_timestamp(self) -> str:
        """Retorna timestamp atual formatado"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def obter_metricas_resumidas(self, resultado_grafo: Dict[str, Any]) -> Dict[str, Any]:
        """Retorna métricas resumidas para exibição rápida"""
        try:
            metricas = self.calcular_metricas_avancadas(resultado_grafo)
            estatisticas = resultado_grafo.get('estatisticas', {})
            
            return {
                'num_nos': estatisticas.get('num_nos', 0),
                'num_arestas': estatisticas.get('num_arestas', 0),
                'acoplamento_medio': round(metricas.acoplamento_medio, 3),
                'coesao_media': round(metricas.coesao_media, 3),
                'modularidade': round(metricas.modularidade, 3),
                'densidade': round(metricas.densidade, 3),
                'complexidade_media': round(getattr(metricas, 'complexidade_ciclomatica_media', 0), 1),
                'componentes_conectados': metricas.numero_componentes
            }
        except Exception as e:
            logger.error(f"Erro ao obter métricas resumidas: {e}")
            return {
                'num_nos': 0,
                'num_arestas': 0,
                'acoplamento_medio': 0,
                'coesao_media': 0,
                'modularidade': 0,
                'densidade': 0,
                'complexidade_media': 0,
                'componentes_conectados': 0
            }
    
    def exportar_analise_json(self, analise: Dict[str, Any]) -> str:
        """Exporta análise completa para JSON"""
        try:
            return json.dumps(analise, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao exportar análise para JSON: {e}")
            return "{}"
    
    def importar_analise_json(self, json_str: str) -> Dict[str, Any]:
        """Importa análise de JSON string"""
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Erro ao importar análise de JSON: {e}")
            return {}