# modules/dashboard/view/components/__init__.py

from .metricas_card import MetricasCard
from .storytelling_card import StorytellingCard
from .recomendacoes_card import RecomendacoesCard
from .nos_criticos_card import NosCriticosCard
from .historico_card import HistoricoCard
from .rag_analyser import RagAnalyserCard

__all__ = [
    'MetricasCard',
    'StorytellingCard',
    'RecomendacoesCard',
    'NosCriticosCard',
    'HistoricoCard',
    'RagAnalyserCard'
]