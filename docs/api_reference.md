# Referência de API

## Visão Geral

Esta documentação descreve as APIs e interfaces principais do sistema de análise de grafos de chamada.

## Módulo de Análise (Analise)

### AnaliseModel

Classe principal para análise de código-fonte usando LLMs.

#### Métodos Principais

##### `__init__(notifier=None)`
Inicializa o modelo de análise.

**Parâmetros:**
- `notifier` (Optional[Callable]): Serviço de notificação para eventos

##### `analisar_codigo(arquivos, config, progress_callback=None, completion_callback=None)`
Inicia a análise de múltiplos arquivos de código.

**Parâmetros:**
- `arquivos` (List[str]): Lista de caminhos dos arquivos para analisar
- `config` (Dict[str, Any]): Configurações da análise
- `progress_callback` (Callable, optional): Callback para progresso
- `completion_callback` (Callable, optional): Callback para conclusão

**Retorna:**
- `str`: ID único da tarefa de análise

##### `pausar_analise() -> bool`
Pausa a análise atual.

**Retorna:**
- `bool`: True se pausado com sucesso

##### `retomar_analise() -> bool`
Retoma a análise pausada.

**Retorna:**
- `bool`: True se retomado com sucesso

##### `parar_analise() -> bool`
Para a análise atual.

**Retorna:**
- `bool`: True se parado com sucesso

##### `get_status_analise() -> Dict[str, Any]`
Retorna o status atual da análise.

**Retorna:**
- `Dict[str, Any]`: Dicionário com status da análise

### AnaliseController

Coordena as interações entre Model e View para análise.

#### Métodos Principais

##### `__init__(model, view, notification_service)`
Inicializa o controller.

**Parâmetros:**
- `model` (AnaliseModel): Instância do modelo
- `view` (ViewManager): Instância da view
- `notification_service`: Serviço de notificações

## Módulo de Síntese (Sintese)

### SinteseModel

Gerencia a síntese e resumo dos resultados da análise.

#### Métodos Principais

##### `gerar_sintese(resultados, config, callback=None)`
Gera uma síntese dos resultados da análise.

**Parâmetros:**
- `resultados` (List[Dict]): Resultados das análises
- `config` (Dict[str, Any]): Configurações da síntese
- `callback` (Callable, optional): Callback de progresso

**Retorna:**
- `str`: Texto da síntese gerada

## Módulo de Grafos (Grafo)

### GrafoModel

Processa dados de grafos de chamada.

#### Métodos Principais

##### `processar_dados_grafo(dados_json, config)`
Processa dados JSON para visualização em grafo.

**Parâmetros:**
- `dados_json` (Dict): Dados do grafo em formato JSON
- `config` (Dict): Configurações de visualização

**Retorna:**
- `Dict`: Dados processados para visualização

##### `exportar_grafo(formato, caminho)`
Exporta o grafo para diferentes formatos.

**Parâmetros:**
- `formato` (str): Formato de exportação (png, svg, json)
- `caminho` (str): Caminho para salvar o arquivo

## Módulo de Dashboard

### DashboardModel

Gerencia dados exibidos no dashboard.

#### Métodos Principais

##### `get_metricas_gerais() -> Dict[str, Any]`
Obtém métricas gerais do sistema.

**Retorna:**
- `Dict[str, Any]`: Métricas como total de análises, arquivos processados, etc.

##### `get_historico_analises() -> List[Dict]`
Obtém o histórico de análises realizadas.

**Retorna:**
- `List[Dict]`: Lista com histórico de análises

## Serviços

### OllamaService

Serviço para integração com Ollama.

#### Métodos

##### `generate_response(model, prompt, context_size=4096, temperature=0.7)`
Gera resposta usando modelo Ollama.

**Parâmetros:**
- `model` (str): Nome do modelo
- `prompt` (str): Prompt para geração
- `context_size` (int): Tamanho do contexto
- `temperature` (float): Temperatura de geração

**Retorna:**
- `str`: Resposta gerada

##### `check_connection() -> bool`
Verifica conexão com Ollama.

**Retorna:**
- `bool`: True se conectado

##### `get_available_models() -> List[str]`
Obtém lista de modelos disponíveis.

**Retorna:**
- `List[str]`: Nomes dos modelos disponíveis

### NotificationService

Gerencia notificações do sistema.

#### Métodos

##### `info(message, title=None)`
Envia notificação informativa.

**Parâmetros:**
- `message` (str): Mensagem da notificação
- `title` (str, optional): Título da notificação

##### `error(message, title=None)`
Envia notificação de erro.

**Parâmetros:**
- `message` (str): Mensagem de erro
- `title` (str, optional): Título da notificação

##### `success(message, title=None)`
Envia notificação de sucesso.

**Parâmetros:**
- `message` (str): Mensagem de sucesso
- `title` (str, optional): Título da notificação

## Middleware

### Auth Middleware

Decoradores para autenticação.

#### Funções

##### `@login_required
Decorator para proteger rotas que exigem autenticação.

**Uso:**
```python
@login_required
def minha_protegida():
    pass
```

## Componentes de UI

### Cards Principais

#### ConfigCard
Componente para configuração de análises.

**Métodos:**
- `get_config()`: Obtém configurações atuais
- `set_config(config)`: Define configurações

#### ExecutionCard
Componente para controle de execução.

**Métodos:**
- `start()`: Inicia execução
- `pause()`: Pausa execução
- `stop()`: Para execução

#### FilesCard
Componente para seleção de arquivos.

**Métodos:**
- `get_selected_files()`: Obtém arquivos selecionados
- `clear_selection()`: Limpa seleção

## Estrutura de Dados

### Formato do Grafo JSON

```json
{
  "nodes": [
    {
      "id": "unique_id",
      "label": "Nome da função/classe",
      "type": "function|class|module",
      "group": "group_name",
      "shape": "circle|box|diamond",
      "color": "#color",
      "metadata": {
        "file": "caminho/arquivo.py",
        "line": 123,
        "complexity": 5
      }
    }
  ],
  "edges": [
    {
      "source": "node_id_1",
      "target": "node_id_2",
      "type": "calls|imports|inherits",
      "weight": 1,
      "label": "relationship_label"
    }
  ],
  "meta": {
    "total_nodes": 100,
    "total_edges": 150,
    "generated_at": "2024-01-01T00:00:00Z",
    "analyzer_version": "1.0.0"
  }
}
```

### Estrutura de Resultado da Análise

```json
{
  "arquivo": "caminho/do/arquivo.py",
  "nome_arquivo": "arquivo.py",
  "analise_texto": "Texto completo da análise...",
  "analise_json": { /* Grafo JSON */ },
  "timestamp": 1640995200.0,
  "config": { /* Configurações usadas */ },
  "status": "sucesso|erro|vazio",
  "estatisticas": {
    "nodes_count": 50,
    "edges_count": 75,
    "texto_length": 5000
  }
}
```

## Configuração

### Configurações Padrão de Análise

```python
{
  'nivel_analise': 'detalhado|simples|resumido',
  'incluir_comentarios': True,
  'analisar_dependencias': True,
  'gerar_json': True,
  'gerar_explicabilidade': True,
  'limite_linhas': 1000,
  'linguagem': 'python|java|c|javascript',
  'threads': 1,
  'pasta_inspecao': 'inspecao/',
  # Configurações LLM
  'llm_url': 'http://localhost:11434',
  'llm_modelo': 'llama2|codellama|mistral',
  'llm_tamanho_contexto': 4096,
  'llm_temperatura': 0.7
}
```

## Eventos e Callbacks

### Callback de Progresso

```python
def progress_callback(progress_percent, current_file, partial_result):
    """
    Chamado durante o progresso da análise.

    Args:
        progress_percent (float): Percentual de progresso (0-100)
        current_file (str): Arquivo sendo analisado
        partial_result (Dict): Resultado parcial do arquivo
    """
    pass
```

### Callback de Conclusão

```python
def completion_callback(results, error):
    """
    Chamado ao finalizar a análise.

    Args:
        results (List[Dict]): Resultados completos da análise
        error (str, None): Mensagem de erro, se houver
    """
    pass
```