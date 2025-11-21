# Sistema de Checkpoint, Pausa Automática e Timing Preciso para Análise de Código

Este documento descreve o sistema completo implementado para otimizar o uso da API do Ollama, incluindo checkpoint inteligente, pausa automática por limites de API, e sistema de timing preciso que exclui períodos de pausa.

## Visão Geral

O sistema combina três componentes principais que trabalham de forma integrada:

1. **Sistema de Checkpoint Inteligente** - Evita análises redundantes
2. **Sistema de Pausa Automática** - Gerencia limites de API automaticamente
3. **Sistema de Timing Preciso** - Mede tempo efetivo excluindo pausas

## Funcionalidades Implementadas

### 1. Sistema de Checkpoint Automático
- **Verificação pré-análise**: Antes de analisar um arquivo, o sistema verifica se já existe uma análise bem-sucedida
- **Validação de configuração**: Compara se a configuração atual é compatível com a análise armazenada
- **Reaproveitamento inteligente**: Se a análise anterior for válida, o resultado é carregado diretamente

### 2. Análise Seletiva
- **Filtragem automática**: A análise processa apenas arquivos pendentes (nunca analisados + com erro + configuração incompatível)
- **Economia de requisições**: Arquivos já analisados com sucesso são ignorados
- **Relatório de progresso**: Sistema mostra quantos arquivos serão analisados vs total do projeto

### 3. Tratamento Inteligente de Erros
- **Identificação de tipo de erro**: VRAM, timeout, API, modelo indisponível, etc.
- **Salvamento de informações de erro**: Permite análise posterior e retomada seletiva
- **Diferenciação de erros temporários**: Erros de VRAM/API podem ser limpos para retentativa

### 4. Métodos de Gerenciamento

#### `verificar_status_completo(pasta_projeto="inspecao/")`
Retorna status completo de todas as análises:
```python
status = analise_controller.verificar_status_completo()
print(f"Concluídos: {status['resumo']['sucesso']}")
print(f"Pendentes: {status['resumo']['pendente']}")
print(f"Economia: {status['economia']['requisicoes_economizadas']} requisições")
```

#### `limpar_analises_com_erro(tipos_erro=['vram', 'timeout'])`
Remove análises com erros específicos:
```python
resultado = analise_controller.limpar_analises_com_erro(['vram'])
print(f"Removidas {resultado['arquivos_removidos']} análises com erro de VRAM")
```

## Exemplo de Fluxo de Uso

### 1. Análise Inicial
```
🔍 Verificando 150 arquivos para análise...
🎯 Identificados 150 arquivos para análise (de 150 totais)
📁 Analisando arquivo: inspecao/nginx/src/core/nginx.c
✅ Checkpoint encontrado para inspecao/nginx/src/core/nginx.h - análise anterior reaproveitada
```

### 2. Após Interrupção (ex: erro de VRAM)
```
🔍 Verificando 150 arquivos para análise...
📈 Status da análise: 120 concluídos, 25 pendentes, 5 com erro, 0 incompatíveis
🎯 Iniciando análise de 30 arquivos pendentes (de 150 totais)
```

### 3. Status Completo
```json
{
  "total_arquivos": 150,
  "resumo": {
    "sucesso": 120,
    "pendente": 25,
    "falha": 5,
    "incompativel": 0
  },
  "economia": {
    "arquivos_ignorados": 120,
    "tempo_economizado_segundos": 1847.32,
    "requisicoes_economizadas": 120
  }
}
```

## Tipos de Erro Identificados

- **`vram`**: Erro de memória de vídeo (requires more system memory)
- **`api_error`**: Erro de API (HTTP 500, Internal Server Error)
- **`model_unavailable`**: Modelo não disponível
- **`timeout`**: Timeout na requisição
- **`geral`**: Outros tipos de erro

## Arquivos de Análise

### Estrutura de um arquivo bem-sucedido:
```json
{
  "arquivo": "inspecao/nginx/src/core/nginx.c",
  "status": "sucesso",
  "tempo_llm": 15.67,
  "config": { ... },
  "analise_json": { ... },
  "estatisticas": { ... }
}
```

### Estrutura de um arquivo com erro:
```json
{
  "arquivo": "inspecao/nginx/src/core/nginx.c",
  "status": "erro",
  "error_type": "vram",
  "erro": "model requires more system memory (9.4 GiB) than is available (8.7 GiB)",
  "config": { ... },
  "timestamp": 1234567890
}
```

### 5. Sistema de Pausa Automática por API

- **Detecção inteligente**: Identifica automaticamente erros de limite de API (429, 403, quota exceeded)
- **Pausa automática**: Suspende a análise quando atinge limites da API
- **Retentativa programada**: Tenta reconectar a cada 30 minutos automaticamente
- **Recuperação automática**: Retoma a análise do ponto onde parou quando a API voltar
- **Interface informativa**: Mostra status da pausa e tempo para próxima tentativa

### 6. Sistema de Timing Preciso

#### **6.1 Medição de Tempo Efetivo**
- **Tempo total vs tempo efetivo**: Diferencia tempo com pausas de tempo de análise real
- **Tracking de pausas**: Registra automaticamente períodos de inatividade por API
- **Validação de timestamps**: Garante consistência nos dados temporais
- **Logging detalhado**: Registra tempos efetivos vs tempos totais

#### **6.2 Estrutura de JSON de Timing**
```json
{
  "timing": {
    "total_analysis_time_ms": 3124567.89,      // Tempo total com pausas
    "effective_analysis_time_ms": 2456789.12,   // Tempo efetivo sem pausas
    "files_processing_time_ms": 2890123.45,    // Tempo dos arquivos
    "llm_total_time_ms": 2564321.10,            // Tempo total de chamadas LLM
    "total_pause_time_ms": 667856.77,           // Tempo total em pausa
    "files": [                                   // Todos os arquivos processados
      {
        "file_path": "src/main.c",
        "analysis_time_ms": 45234.56,
        "nodes": 15,
        "edges": 8
      },
      {
        "file_path": "src/utils.c",
        "analysis_time_ms": 0.0,               // Checkpoint reaproveitado
        "nodes": 22,
        "edges": 14
      }
    ]
  },
  "summary": {
    "total_files_processed": 658,
    "total_nodes": 12450,
    "total_edges": 8932
  }
}
```

#### **6.3 Métodos de Gerenciamento de Timing**
- `pause_analysis()`: Inicia tracking de tempo de pausa
- `resume_analysis()`: Finaliza tracking e acumula tempo de pausa
- `get_effective_elapsed_time()`: Retorna tempo efetivo atual
- `get_current_elapsed_time()`: Retorna tempo total desde início

#### **6.4 Logging de Timing**
```
⏱️ Tempo efetivo (sem pausas): 2456789.12ms | Tempo total com pausas: 3124567.89ms
Análise finalizada: 658 arquivos
```

#### **6.5 Integração com Sistema de Pausa**
- **Timing automático**: Pausas são automaticamente registradas
- **Precisão matemática**: Cálculo exato de tempo efetivo
- **Recuperação transparente**: Dados mantidos mesmo com múltiplas pausas

### 7. Controle Manual da Pausa

- **Retentativa forçada**: Usuário pode testar conexão antes do tempo automaticamente
- **Cancelamento**: Usuário pode cancelar pausa automática e interromper análise
- **Status em tempo real**: Informações detalhadas sobre pausa ativa
- **Botão de debug**: Ícone 🐛 permite testar forçadamente a exibição do botão retry

## Fluxo de Pausa Automática

### 1. Detecção de Erro de API
```
💥 Erro ao analisar arquivo.c: 429 - {"error":"rate limit exceeded"}
🚫 Erro de limite de API detectado: 429 - {"error":"rate limit exceeded"}
🚦 Pausa automática ativada: Limite de API atingido (rate_limit)
⏸️ Análise pausada: Limite de API atingido (rate_limit). Retentativa em 30 minutos...
```

### 2. Espera Automática
```
⏳ Pausa automática: Limite de API atingido (rate_limit). Próxima tentativa em 29 min...
⏳ Pausa automática: Limite de API atingido (rate_limit). Próxima tentativa em 28 min...
```

### 3. Retentativa e Recuperação
```
🔄 Tentativa 1/10 de reconexão com API...
✅ API respondeu! Retomando análise...
🟢 Pausa automática desativada. Análise retomada.
✅ Arquivo 45/150 analisado: arquivo.c
```

## Métodos de Gerenciamento da Pausa Automática

#### `obter_status_pausa_api()`
Retorna informações detalhadas sobre a pausa automática:
```python
status = analise_controller.obter_status_pausa_api()
print(f"Ativa: {status['ativa']}")
print(f"Motivo: {status['motivo']}")
print(f"Próxima tentativa: {status['proxima_tentativa_segundos']} segundos")
```

#### `forcar_retentativa_api()`
Força uma tentativa imediata de reconexão:
```python
resultado = analise_controller.forcar_retentativa_api()
if resultado['status'] == 'sucesso':
    print("API disponível! Análise retomada.")
```

#### `cancelar_pausa_automatica()`
Cancela a pausa automática e interrompe a análise:
```python
resultado = analise_controller.cancelar_pausa_automatica()
print(resultado['mensagem'])
```

## Integração com Interface

### Status Completo Incluindo Pausa Automática
```json
{
  "status": "sucesso",
  "total_arquivos": 150,
  "resumo": {
    "sucesso": 120,
    "pendente": 30,
    "falha": 0,
    "incompativel": 0
  },
  "economia": {
    "arquivos_ignorados": 120,
    "requisicoes_economizadas": 120
  },
  "pausa_automatica": {
    "ativa": true,
    "motivo": "Limite de API atingido (rate_limit)",
    "tempo_esperado_segundos": 1200,
    "proxima_tentativa_segundos": 600,
    "tentativas": 1,
    "maximo_tentativas": 10
  },
  "analise_atual": {
    "em_andamento": true,
    "arquivo_atual": "inspecao/nginx/src/core/ngx_connection.c",
    "progresso_percentual": 80.0,
    "pausada": true
  }
}
```

## Configurações do Sistema

### Parâmetros de Pausa Automática
- **Intervalo de retentativa**: 30 minutos (1800 segundos)
- **Máximo de tentativas**: 10 tentativas automáticas
- **Tipos de erro que ativam pausa**: `rate_limit`, `quota_exceeded`
- **Verificação de conexão**: Testa API antes de retomar análise

### Tipos de Erro Detectados
- **`rate_limit`**: Erro 429 - Too Many Requests
- **`quota_exceeded`**: Erro 403 - Cota esgotada
- **`vram`**: Erro de memória de vídeo
- **`model_unavailable`**: Modelo não disponível
- **`timeout`**: Timeout de requisição
- **`api_error`**: Erros de servidor HTTP 5xx

## Benefícios

1. **Economia de API**: Evita requisições redundantes para arquivos já analisados
2. **Resiliência**: Permite retomada após interrupções sem perder progresso
3. **Gerenciamento automático de limites**: Lida com restrições de API transparentemente
4. **Otimização de custos**: Ideal para planos gratuitos com limites horários/semanais
5. **Flexibilidade**: Permite limpar erros temporários e refazer análises seletivamente
6. **Operação contínua**: Sistema pode rodar por horas/dias com intervenção mínima
7. **Transparência**: Relatórios detalhados do status, economia e pausas ativas

## Configurações Verificadas

O sistema valida as seguintes configurações para determinar compatibilidade:
- `llm_modelo`: Modelo LLM utilizado
- `nivel_analise`: Nível da análise (básico, detalhado, etc.)
- `analisar_dependencias`: Flag de análise de dependências
- `incluir_comentarios`: Flag de inclusão de comentários