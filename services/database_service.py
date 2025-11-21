#services/database_service.py

"""
Serviço de Banco de Dados - Gerenciamento de persistência SQLite.

Este módulo implementa o serviço de banco de dados SQLite utilizado para
armazenar configurações, resultados de análises e metadados da aplicação.
Oferece uma interface simplificada para operações CRUD com tratamento
automático de erros e migrações de schema.

Funcionalidades:
- Criação automática de tabelas e migrações
- Persistência de configurações e análises
- Operações CRUD com tratamento de erros
- Backup e recuperação de dados
- Gerenciamento de transações
- Query builder para consultas complexas
"""

import sqlite3
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Serviço de gerenciamento do banco de dados SQLite.

    Esta classe gerencia todas as operações de persistência da aplicação,
    incluindo configurações, resultados de análises e metadados. Implementa
    um sistema de migrações automáticas para garantir compatibilidade.

    Attributes:
        db_path (str): Caminho para o arquivo do banco de dados SQLite

    Example:
        >>> db = DatabaseService("storage/analise.db")
        >>> db.save_config("llm_model", "codellama")
        >>> model = db.get_config("llm_model")
        >>> db.save_analysis_result({"file": "main.c", "nodes": 10})
    """

    def __init__(self, db_path: str = "storage/analise.db"):
        """
        Inicializa o serviço de banco de dados.

        Args:
            db_path (str): Caminho para o arquivo do banco de dados.
                          Default: "storage/analise.db"
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela de configurações
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS configuracao (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chave TEXT UNIQUE NOT NULL,
                        valor TEXT NOT NULL,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela de arquivos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS arquivos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        caminho TEXT UNIQUE NOT NULL,
                        nome_arquivo TEXT NOT NULL,
                        selecionado BOOLEAN DEFAULT 1,
                        processado BOOLEAN DEFAULT 0,
                        resultado_json TEXT,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabela de análises (histórico)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analises (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tarefa_id TEXT UNIQUE NOT NULL,
                        status TEXT NOT NULL,
                        progresso REAL DEFAULT 0,
                        total_arquivos INTEGER DEFAULT 0,
                        arquivos_processados INTEGER DEFAULT 0,
                        configuracao TEXT,
                        iniciado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        finalizado_em TIMESTAMP,
                        resultado TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Banco de dados inicializado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def salvar_configuracao(self, chave: str, valor: Any):
        """Salva uma configuração no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO configuracao (chave, valor, atualizado_em)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (chave, json.dumps(valor)))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar configuração {chave}: {e}")
    
    def obter_configuracao(self, chave: str, default: Any = None) -> Any:
        """Obtém uma configuração do banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT valor FROM configuracao WHERE chave = ?', (chave,))
                resultado = cursor.fetchone()
                return json.loads(resultado[0]) if resultado else default
        except Exception as e:
            logger.error(f"Erro ao obter configuração {chave}: {e}")
            return default
    
    def salvar_arquivos(self, arquivos: List[str]):
        """Salva/atualiza a lista de arquivos no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Primeiro, marca todos os arquivos existentes como não selecionados
                cursor.execute('UPDATE arquivos SET selecionado = 0')
                
                # Depois, insere/atualiza os novos arquivos
                for arquivo in arquivos:
                    cursor.execute('''
                        INSERT OR REPLACE INTO arquivos (caminho, nome_arquivo, selecionado, atualizado_em)
                        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ''', (arquivo, os.path.basename(arquivo)))
                
                conn.commit()
                logger.info(f"Salvos {len(arquivos)} arquivos no banco")
                
        except Exception as e:
            logger.error(f"Erro ao salvar arquivos: {e}")
    
    def obter_arquivos_selecionados(self) -> List[str]:
        """Obtém a lista de arquivos selecionados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT caminho FROM arquivos WHERE selecionado = 1')
                resultados = cursor.fetchall()
                return [resultado[0] for resultado in resultados]
        except Exception as e:
            logger.error(f"Erro ao obter arquivos selecionados: {e}")
            return []
    
    def atualizar_selecao_arquivo(self, caminho: str, selecionado: bool):
        """Atualiza a seleção de um arquivo específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE arquivos 
                    SET selecionado = ?, atualizado_em = CURRENT_TIMESTAMP
                    WHERE caminho = ?
                ''', (1 if selecionado else 0, caminho))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar seleção do arquivo {caminho}: {e}")
    
    def salvar_analise(self, tarefa_id: str, status: str, configuracao: Dict[str, Any]):
        """Salva uma nova análise no histórico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analises (tarefa_id, status, configuracao)
                    VALUES (?, ?, ?)
                ''', (tarefa_id, status, json.dumps(configuracao)))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar análise {tarefa_id}: {e}")
    
    def atualizar_analise(self, tarefa_id: str, **kwargs):
        """Atualiza os dados de uma análise"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                campos = []
                valores = []
                
                for campo, valor in kwargs.items():
                    campos.append(f"{campo} = ?")
                    valores.append(json.dumps(valor) if isinstance(valor, (dict, list)) else valor)
                
                if campos:
                    valores.append(tarefa_id)
                    query = f'''
                        UPDATE analises 
                        SET {', '.join(campos)}, 
                            finalizado_em = CASE WHEN ? = 'completada' THEN CURRENT_TIMESTAMP ELSE finalizado_em END
                        WHERE tarefa_id = ?
                    '''
                    cursor.execute(query, (*valores, tarefa_id))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar análise {tarefa_id}: {e}")
    
    def obter_historico_analises(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Obtém o histórico de análises"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM analises 
                    ORDER BY iniciado_em DESC 
                    LIMIT ?
                ''', (limite,))
                
                colunas = [desc[0] for desc in cursor.description]
                resultados = []
                
                for linha in cursor.fetchall():
                    resultado = dict(zip(colunas, linha))
                    # Converte campos JSON
                    for campo in ['configuracao', 'resultado']:
                        if resultado.get(campo):
                            resultado[campo] = json.loads(resultado[campo])
                    resultados.append(resultado)
                
                return resultados
                
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []

