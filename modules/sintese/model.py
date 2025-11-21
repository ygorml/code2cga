# ./modules/sintese/model.py
import os
import json
import logging
import re
import threading
from datetime import datetime
from services.notification_service import NotificationService
"""
Model do módulo de síntese.

Responsável por processar e sintetizar os resultados das análises.
"""


try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np # Import numpy para manipulação de arrays
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExtratorJsonDeTxt:
    def __init__(self, pasta_grafos_extraidos="grafos_extraidos"):
        self.pasta_destino = pasta_grafos_extraidos
        self.log_sucesso = "proveniencia_log.json"
        self.log_erro = "erros_log.json"
        self.id_processamento = 0
        self.sucessos = []

        if not os.path.exists(self.pasta_destino):
            os.makedirs(self.pasta_destino)
            logging.info(f"Pasta '{self.pasta_destino}' criada com sucesso.")
        
        if not SKLEARN_AVAILABLE:
            logging.warning("Biblioteca 'scikit-learn' não encontrada. A busca por similaridade está desativada.")

    def _atualizar_log_json(self, caminho_log, nova_entrada):
        entradas = []
        if os.path.exists(caminho_log):
            with open(caminho_log, 'r', encoding='utf-8') as f:
                try:
                    entradas = json.load(f)
                    if not isinstance(entradas, list): entradas = []
                except json.JSONDecodeError: entradas = []
        entradas.append(nova_entrada)
        with open(caminho_log, 'w', encoding='utf-8') as f:
            json.dump(entradas, f, indent=4, ensure_ascii=False)

    def _gerar_log_de_sucesso(self, id_proc, txt_path, json_path, metodo_busca):
        log_entry = {
            "id_processamento": id_proc,
            "origem_txt": os.path.abspath(txt_path),
            "destino_json": os.path.abspath(json_path),
            "metodo_busca_utilizado": metodo_busca,
        }
        self._atualizar_log_json(self.log_sucesso, log_entry)
        self.sucessos.append(json_path)
        logging.info(f"Log de proveniência (ID: {id_proc}) atualizado.")

    def _gerar_log_de_erro(self, id_proc, txt_path, tipo_erro, msg):
        log_entry = {
            "id_processamento": id_proc,
            "timestamp": datetime.now().isoformat(),
            "arquivo_com_erro": os.path.abspath(txt_path),
            "tipo_erro": tipo_erro,
            "detalhes": msg
        }
        self._atualizar_log_json(self.log_erro, log_entry)
        logging.error(f"Erro (ID: {id_proc}) registrado para o arquivo '{txt_path}'.")

    def _salvar_json(self, dados_json, caminho_completo_saida):
        os.makedirs(os.path.dirname(caminho_completo_saida), exist_ok=True)
        with open(caminho_completo_saida, 'w', encoding='utf-8') as f:
            json.dump(dados_json, f, indent=4, ensure_ascii=False)
        return caminho_completo_saida

    def _normalizar_texto(self, texto):
        texto = re.sub(r'[\W_]+', ' ', texto)
        return ' '.join(texto.lower().split())

    def _encontrar_secao_flexivel(self, conteudo_linhas, secao_alvo):
        secao_alvo_normalizada = self._normalizar_texto(secao_alvo)
        for i, linha in enumerate(conteudo_linhas):
            if secao_alvo_normalizada in self._normalizar_texto(linha):
                return i, linha
        return None, None
        
    def _encontrar_secao_por_similaridade(self, conteudo_linhas, secao_alvo, limiar):
        """
        Encontra a seção mais similar à seção alvo usando TF-IDF e similaridade de cosseno.

        Args:
            conteudo_linhas (list): Uma lista de strings, onde cada string é uma linha do arquivo.
            secao_alvo (str): O título da seção a ser procurada.
            limiar (float): O limiar de similaridade (entre 0 e 1) para considerar uma correspondência.

        Returns:
            tuple: Uma tupla (índice, conteúdo_da_linha) se uma correspondência acima do limiar for encontrada.
                   Caso contrário, retorna (None, None).
        """
        if not SKLEARN_AVAILABLE:
            logging.warning("Tentativa de busca por similaridade, mas 'scikit-learn' não está instalado.")
            return None, None
        
        if not conteudo_linhas:
            return None, None

        try:
            # Normaliza a seção alvo e todas as linhas do conteúdo
            secao_alvo_norm = self._normalizar_texto(secao_alvo)
            linhas_norm = [self._normalizar_texto(linha) for linha in conteudo_linhas]
            
            # Cria o corpus para vetorização (alvo + todas as linhas)
            corpus = [secao_alvo_norm] + linhas_norm

            # Vetoriza o texto usando TF-IDF
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # Calcula a similaridade de cosseno entre a seção alvo (primeiro item) e todas as outras linhas
            # tfidf_matrix[0:1] é o vetor da secao_alvo
            # tfidf_matrix[1:] são os vetores de todas as linhas do arquivo
            cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Encontra o índice da linha com a maior similaridade
            if cosine_similarities.size == 0:
                return None, None
            
            best_match_index = np.argmax(cosine_similarities)
            best_score = cosine_similarities[best_match_index]
            
            logging.debug(f"Busca por similaridade: Melhor correspondência na linha {best_match_index} com score de {best_score:.4f} (limiar: {limiar})")
            
            # Verifica se a melhor similaridade encontrada atende ao limiar
            if best_score >= limiar:
                return best_match_index, conteudo_linhas[best_match_index]
            else:
                return None, None
                
        except Exception as e:
            logging.error(f"Erro durante o cálculo de similaridade: {e}")
            return None, None

    def _extrair_json_de_bloco_codigo(self, texto_secao: str):
        try:
            inicio_bloco = texto_secao.find("```json")
            if inicio_bloco == -1: return None
            fim_bloco = texto_secao.find("```", inicio_bloco + 6)
            if fim_bloco == -1: return None
            json_string = texto_secao[inicio_bloco + 7 : fim_bloco].strip()
            return json_string
        except Exception:
            return None

    def _extrair_conteudo_json_delimitado(self, texto_secao):
        try:
            inicio = texto_secao.index("[ GRAFO JSON ]") + len("[ GRAFO JSON ]")
            fim = texto_secao.index("[ GRAFO JSON FIM]")
            return texto_secao[inicio:fim].strip()
        except ValueError: return None

    def _extrair_conteudo_json_por_chaves(self, texto_secao):
        try:
            inicio = texto_secao.find('{')
            if inicio == -1: return None
            contador = 0
            for i, char in enumerate(texto_secao[inicio:]):
                if char == '{': contador += 1
                elif char == '}': contador -= 1
                if contador == 0: return texto_secao[inicio : inicio + i + 1].strip()
            return None
        except Exception: return None

    def _extrair_de_arquivo(self, caminho_arquivo_txt, caminho_base, secao_alvo, metodo_busca, limiar_similaridade):
        self.id_processamento += 1
        id_atual = self.id_processamento
        logging.info(f"[ID: {id_atual}] Processando: {os.path.basename(caminho_arquivo_txt)}")

        try:
            with open(caminho_arquivo_txt, 'r', encoding='utf-8') as f:
                conteudo_linhas = f.read().splitlines()
            
            # --- CORREÇÃO PRINCIPAL CONTRA O ERRO "CANNOT UNPACK" ---
            # Primeiro, atribuímos o resultado a uma variável temporária
            resultado_busca = (self._encontrar_secao_por_similaridade(conteudo_linhas, secao_alvo, limiar_similaridade)
                                 if metodo_busca == 'similaridade'
                                 else self._encontrar_secao_flexivel(conteudo_linhas, secao_alvo))

            # Agora, verificamos se o resultado é válido ANTES de desempacotar
            if not resultado_busca or resultado_busca[0] is None:
                msg = f"A seção '{secao_alvo}' não foi encontrada."
                self._gerar_log_de_erro(id_atual, caminho_arquivo_txt, "Seção Não Encontrada", msg)
                return
            
            indice_secao, _ = resultado_busca
            # -----------------------------------------------------------

            texto_apos_secao = "\n".join(conteudo_linhas[indice_secao + 1:])
            
            json_string = (self._extrair_json_de_bloco_codigo(texto_apos_secao) or 
                           self._extrair_conteudo_json_delimitado(texto_apos_secao) or 
                           self._extrair_conteudo_json_por_chaves(texto_apos_secao))

            if not json_string:
                msg = "Não foi possível encontrar um bloco JSON válido na seção."
                self._gerar_log_de_erro(id_atual, caminho_arquivo_txt, "Conteúdo JSON Não Encontrado", msg)
                return
            
            try:
                dados_json = json.loads(json_string)
            except json.JSONDecodeError as e:
                self._gerar_log_de_erro(id_atual, caminho_arquivo_txt, "JSON Inválido", f"Erro: {e}.")
                return

            nome_base_relativo, _ = os.path.splitext(os.path.relpath(caminho_arquivo_txt, caminho_base))
            caminho_json_saida = os.path.join(self.pasta_destino, f"{nome_base_relativo}.json")
            
            self._salvar_json(dados_json, caminho_json_saida)
            self._gerar_log_de_sucesso(id_atual, caminho_arquivo_txt, caminho_json_saida, metodo_busca)

        except Exception as e:
            self._gerar_log_de_erro(id_atual, caminho_arquivo_txt, "Erro Inesperado", f"Ocorreu um erro: {e}")

    def processar_caminho(self, caminho_entrada, secao_alvo, metodo_busca, limiar_similaridade, stop_event: threading.Event):
        self.sucessos.clear()
        if not os.path.exists(caminho_entrada):
            logging.error(f"O caminho '{caminho_entrada}' não existe.")
            return self.sucessos

        if os.path.isfile(caminho_entrada):
            if stop_event.is_set(): return self.sucessos
            if caminho_entrada.lower().endswith('.txt'):
                self._extrair_de_arquivo(caminho_entrada, os.path.dirname(caminho_entrada), secao_alvo, metodo_busca, limiar_similaridade)
        elif os.path.isdir(caminho_entrada):
            logging.info(f"Iniciando varredura no diretório: {caminho_entrada}")
            for raiz, _, arquivos in os.walk(caminho_entrada):
                if stop_event.is_set(): break
                for arquivo in arquivos:
                    if stop_event.is_set(): break
                    if arquivo.lower().endswith('.txt'):
                        self._extrair_de_arquivo(os.path.join(raiz, arquivo), caminho_entrada, secao_alvo, metodo_busca, limiar_similaridade)
        return self.sucessos

class SinteseModel:
    def __init__(self, notifier: NotificationService):
        self.notifier = notifier
    
    def extrair_json_de_txt(self, caminho_entrada, secao_alvo, metodo_busca, limiar_similaridade, stop_event: threading.Event):
        try:
            self.notifier.notify('status_update', "Iniciando extração...")
            self.notifier.notify('log_message', "Parâmetros recebidos, iniciando processo.", level="INFO")

            extrator = ExtratorJsonDeTxt(pasta_grafos_extraidos="storage/data")
            
            lista_sucessos = extrator.processar_caminho(
                caminho_entrada, secao_alvo, metodo_busca, limiar_similaridade, stop_event
            )
            
            if stop_event.is_set():
                mensagem_final = "Processo de extração cancelado pelo usuário."
                self.notifier.notify('log_message', mensagem_final, level="WARNING")
            else:
                mensagem_final = "Processo de extração concluído."
                self.notifier.notify('log_message', f"Extração finalizada. {len(lista_sucessos)} arquivos gerados.", level="INFO")
            
            self.notifier.notify('status_update', mensagem_final)
            self.notifier.notify('execution_complete', results=lista_sucessos)

        except Exception as e:
            error_message = f"Ocorreu um erro inesperado durante a extração: {e}"
            logger.error(error_message, exc_info=True)
            self.notifier.notify('status_update', "Falha na extração.")
            self.notifier.notify('log_message', error_message, level="ERROR")
            self.notifier.notify('execution_complete', results=[])