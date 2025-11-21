# Medição de Tempos de Análise

## Overview

O sistema de medição de tempos captura duas métricas principais durante a análise de código:
1. **Tempo de processamento da LLM** (por arquivo)
2. **Tempo total de análise** (da sessão completa)

## Como os Tempos São Medidos

### 1. Tempo de Processamento LLM (`tempo_llm`)

O tempo da LLM é medido no serviço `OllamaService` através de um delta timestamp simples:

```python
# Em services/ollama_service.py
start_time = time.time()  # Timestamp ANTES de enviar requisição para LLM

response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=1200)

end_time = time.time()    # Timestamp DEPOIS de receber resposta da LLM
elapsed_time = end_time - start_time  # Delta em segundos
```

**O que é medido:**
- Início: `time.time()` imediatamente antes do `requests.post()`
- Fim: `time.time()` imediatamente após o `response.json()`
- Inclui: Tempo de rede + Tempo de processamento da LLM
- Exclui: Tempo de preparação do prompt, pós-processamento, salvamento em arquivo

### 2. Tempo Total de Análise (`total_analysis_time_ms`)

O tempo total é medido no `TimingLoggerService`:

```python
# Em services/timing_logger_service.py
self.start_time = time.time()  # No início da análise
# ... durante análise de cada arquivo ...
total_time = (time.time() - self.start_time) * 1000  # Delta convertido para ms
```

**O que é medido:**
- Início: `time.time()` quando `iniciar_analise()` é chamado
- Fim: `time.time()` quando `finish_analysis()` é chamado
- Inclui: Tempo completo desde o início até o final da análise
- Inclui: Todas as pausas, tempos de LLM, processamento, I/O

## Formato do Arquivo de Saída

O sistema gera um arquivo JSON em `storage/export/` com o seguinte formato:

```json
{
  "metadata": {
    "tool_name": "CallGraphAnalyzer",
    "tool_version": "1.0.0",
    "project_name": "dummy1",
    "project_root": "/inspecao/dummy1",
    "timestamp": "2025-11-18T03:24:26Z",
    "language": "C"
  },
  "timing": {
    "total_analysis_time_ms": 12000.18,
    "files": [
      {
        "file": "inspecao/dummy1/dummy1.c",
        "analysis_time_ms": 9191.71,
        "nodes": 4,
        "edges": 3
      }
    ]
  },
  "summary": {
    "total_files_processed": 1,
    "total_nodes": 4,
    "total_edges": 3
  }
}
```

### Campos Explicados

#### metadata
- `project_name`: Nome extraído do diretório pai dos arquivos
- `project_root`: Caminho absoluto do diretório do projeto
- `timestamp`: ISO 8601 UTC quando a análise foi finalizada
- `language`: Linguagem de programação (padrão: "C")

#### timing
- `total_analysis_time_ms`: Tempo total em milissegundos (decimal com 2 casas)
- `files`: Array com tempos individuais por arquivo
  - `analysis_time_ms`: Tempo LLM por arquivo em ms
  - `nodes`: Número de nós extraídos
  - `edges`: Número de arestas extraídas

#### summary
- `total_files_processed`: Número de arquivos analisados
- `total_nodes`: Soma de todos os nós
- `total_edges`: Soma de todas as arestas

## Arquivos Gerados

Dois arquivos são criados por análise:

1. **`timing_<projeto>_<timestamp>.json`** - Histórico permanente
   - Exemplo: `timing_dummy1_20251118_032426.json`
   - Nunca sobrescrito

2. **`timing_<projeto>.json`** - Última análise
   - Exemplo: `timing_dummy1.json`
   - Sempre sobrescrito com a análise mais recente

## Precisão e Limitações

### Precisão
- Resolução: `time.time()` tem precisão de microssegundos
- Formato: Decimal com 2 casas para milissegundos
- Conversão: Segundos → Milissegundos (multiply by 1000)

### Limitações
1. **Overhead de rede**: O tempo da LLM inclui latência de rede
2. **Precisão do clock**: Dependente do sistema operacional
3. **Thread-safe**: Medição em thread separada da UI
4. **Pausas**: Tempo total inclui pausas manuais do usuário

## Integração com o Sistema

### Fluxo de Dados

```
Análise Iniciada
    ↓
TimingLogger.start_analysis()
    ↓
Para cada arquivo:
    OllamaService.generate_response() [mede tempo LLM]
    ↓
    TimingLogger.add_file_timing()
    ↓
Análise Concluída
    ↓
TimingLogger.finish_analysis() [calcula total, salva JSON]
```

### Callbacks Utilizados

- `progress_callback`: Chamado após cada arquivo com timing
- `completion_callback`: Chamado ao final para salvar arquivo

## Debug e Monitoramento

Para habilitar logs de timing:

```python
# Em desenvolvimento, os logs de print() mostram:
print("ADICIONANDO TIMING: arquivo, tempo_ms, nodes, edges")
print("FINALIZANDO TIMING LOGGER...")
print(f"ARQUIVO SALVO: {filepath}")
```

Logs em nível INFO são registrados no logger principal:
- `services.timing_logger_service`
- `services.ollama_service`

## Exemplos de Uso

### Análise de Performance
```python
# Carregar arquivo de timing
with open('storage/export/timing_dummy1.json') as f:
    data = json.load(f)

# Tempo médio por arquivo
total_time = data['timing']['total_analysis_time_ms']
files = len(data['timing']['files'])
avg_time = total_time / files
```

### Comparação entre Projetos
- Comparar `total_analysis_time_ms` entre diferentes arquivos
- Analisar `analysis_time_ms` médio por tipo de arquivo
- Correlacionar número de nós/edges com tempo de processamento