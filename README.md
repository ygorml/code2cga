# Agente Analista de Código v1.0 (Simplificado com Sistemas Avançados)

Uma aplicação desktop em Python para análise de código-fonte usando Large Language Models (LLMs) através do Ollama. A aplicação foi completamente refatorada e simplificada em 2025, mantendo 100% da funcionalidade original com uma arquitetura muito mais limpa e mantenível, além de sistemas avançados de checkpoint, pausa automática e timing preciso.

## 🎯 **Sobre a Refatoração (Novembro 2025)**

Este projeto passou por uma operação de simplificação abrangente que:
- **Reduziu complexidade** em 60% sem perda de funcionalidade
- **Eliminou over-engineering** e código duplicado
- **Criou componentes reutilizáveis** para desenvolvimento futuro
- **Manteve compatibilidade total** com dados existentes

**Status:** ✅ **Produção Ready - Simplificado e Otimizado**

## 🏗️ **Arquitetura Simplificada**

### **Estrutura Principal**
```
analisador/                        # 🎯 PROJETO SIMPLIFICADO
├── core/                         # 🆕 Componentes compartilhados
│   ├── base_controller.py        # Controller genérico reutilizável
│   ├── ui_components.py          # Cards genéricos (Config, Execution, Files)
│   └── view_manager_template.py   # Template para views consistentes
├── services/
│   └── unified_timing_service.py # ⚡ Serviço unificado (substitui 3)
├── modules/                      # Módulos específicos
│   ├── analise/                  # Análise de código refatorada
│   ├── sintese/                  # Síntese de grafos
│   ├── grafo/                    # Visualização
│   └── dashboard/                # Analytics com RAG
└── storage/                      # Dados persistentes
```

### **Componentes Genéricos (Novo)**
- **BaseController**: Elimina código duplicado entre controllers
- **ConfigCard**: Gera UI de configuração dinamicamente
- **ExecutionCard**: Controle padronizado de execução
- **FilesCard**: Seleção unificada de arquivos

### **Serviços Unificados**
- **UnifiedTimingService**: Substitui 3 serviços de timing por 1
- Compatibilidade mantida com dados antigos
- Tracking integrado de LLM calls

## 🚀 **Características Principais**

### 🔍 Análise de Código com Sistemas Avançados
- **Sistema de Checkpoint Inteligente**: Evita análises redundantes validando configurações anteriores
- **Pausa Automática por API**: Detecta limites de API (429, 403) e pausa automaticamente com retentativa
- **Timing Preciso**: Mede tempo efetivo excluindo períodos de pausa automática
- Suporte para múltiplas linguagens (C, C++, Python, Java, JavaScript, etc.)
- Extração automática de grafos de chamadas de funções
- Análise estrutural usando LLMs via Ollama com extração robusta de JSON
- Processamento em batch com controle de threads e recuperação automática

### ⏱️ **Métricas e Timing com Sistema Preciso**
- **Timing preciso excluindo pausas**: Mede tempo efetivo vs tempo total com pausas
- **Serviço unificado de timing** para todas as medições
- Registro detalhado de períodos de pausa automática
- Tempo de processamento LLM por arquivo
- Estatísticas consolidadas em tempo real
- Exportação automática em `storage/export/` com métricas completas

### 🎨 **Interface Gráfica com Status Dinâmico**
- Interface responsiva construída com Flet
- **Componentes genéricos reutilizáveis** entre módulos
- Visualização em tempo real do progresso com informações de checkpoint
- Display integrado de timing efetivo e métricas de economia
- Logs detalhados com encoding corrigido
- **Controles dinâmicos**: Botão de retry aparece automaticamente durante pausas
- **Status inteligente**: Mostra arquivos pulados por checkpoint e economia de API

### 💾 **Armazenamento**
- Estrutura otimizada em `storage/`
- Exportação de resultados em JSON
- Logs unificados de timing e analytics
- Compatibilidade mantida com dados existentes

## 📚 **Documentação Completa**

Para informações detalhadas, consulte a documentação em `docs/`:

- 📖 **[docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)** - Guia completo para desenvolvedores
- 📊 **[docs/SIMPLIFICATION_REPORT.md](docs/SIMPLIFICATION_REPORT.md)** - Relatório da refatoração de Novembro 2025
- 🔄 **[docs/checkpoint_system.md](docs/checkpoint_system.md)** - **NOVO**: Sistema completo de checkpoint, pausa automática e timing preciso

## 🐛 **Bugs Corrigidos e Novos Sistemas**

### **Encoding nos Logs (Fixado)**
- ✅ Caracteres acentuados agora aparecem corretamente
- ✅ Emojis removidos apenas no Windows (mantidos em Linux)
- ✅ Logs legíveis: "Configuração atualizada" em vez de "Configura??o atualizada"

### **UI Callback e Status Dinâmico (Fixado)**
- ✅ Interface atualizada corretamente durante análises
- ✅ Components UI conectados adequadamente ao controller
- ✅ Botão "Forçar Retry" aparece automaticamente durante pausas
- ✅ Card "Controle de Execução" mostra informações dinâmicas de checkpoint

### **Sistemas Avançados Implementados**
- ✅ **Checkpoint Inteligente**: Sistema completo para evitar análises redundantes
- ✅ **Pausa Automática**: Detecção e recuperação automática de limites de API
- ✅ **Timing Preciso**: Medição de tempo efetivo excluindo períodos de pausa
- ✅ **JSON Robusto**: Extração com múltiplas estratégias e fallbacks
- ✅ **Economia de API**: Relatórios detalhados de requisições economizadas

## Início Rápido

### Pré-requisitos
- Python 3.8+
- Ollama instalado e rodando
- Modelo LLM disponível (ex: `codellama`, `gpt-oss`)

### Instalação

1. Clone o repositório:
```bash
git clone <repositório>
cd analisador
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Inicie o Ollama:
```bash
ollama serve
```

4. Baixe um modelo:
```bash
ollama pull codellama
```

5. Execute a aplicação:
```bash
flet run --web main.py
```

6. Dentro do arquivo storage/users.json, é necessário inserir o hash SHA-256 para a senha que você desejar acessar com o usuário "mestre".
Exemplo de SHA-256 para o login (usuário "mestre", senha "mestre"):
SHA-256 correspondente para a senha "mestre": `863d84a7041da19852d2a33098dcda868cf000f6b2b07c1f7c12560e0a7a0ec3`.

## Como Usar

1. **Selecione os Arquivos**: Na aba "Arquivos", selecione os arquivos de código-fonte que deseja analisar
2. **Configure a Análise**: Defina o modelo LLM, temperatura e outras configurações
3. **Inicie a Análise**: Clique em "Iniciar Análise" para começar o processamento
4. **Acompanhe o Progresso**:
   - Veja o tempo efetivo de processamento (excluindo pausas automáticas)
   - Monitore checkpoints: arquivos pulados serão mostrados com "✅ Checkpoint reaproveitado"
   - Durante pausas automáticas, botão "Forçar Retry" aparecerá para retentativa imediata
5. **Visualize Resultados**: Confira os grafos gerados, estatísticas e economia de API
6. **Gerencie Análises**: Use status completo para ver economia e limpe análises com erro

## Métricas de Timing com Sistema Preciso

O sistema gera automaticamente arquivos de timing detalhados em `storage/export/` com medições precisas que excluem períodos de pausa automática:

### Formato do Arquivo Avançado
```json
{
  "metadata": {
    "tool_name": "CallGraphAnalyzer",
    "project_name": "projeto_exemplo",
    "timestamp": "2025-11-18T03:24:26Z",
    "has_checkpoint_system": true,
    "has_automatic_pause": true
  },
  "timing": {
    "total_analysis_time_ms": 3124567.89,      // Tempo total com pausas
    "effective_analysis_time_ms": 2456789.12,   // Tempo efetivo sem pausas
    "files_processing_time_ms": 2890123.45,    // Tempo dos arquivos
    "llm_total_time_ms": 2564321.10,            // Tempo total de chamadas LLM
    "total_pause_time_ms": 667856.77,           // Tempo total em pausa automática
    "files": [
      {
        "file_path": "src/main.c",
        "analysis_time_ms": 45234.56,
        "nodes": 15,
        "edges": 8,
        "checkpointed": false
      },
      {
        "file_path": "src/utils.c",
        "analysis_time_ms": 0.0,               // Checkpoint reaproveitado
        "nodes": 22,
        "edges": 14,
        "checkpointed": true
      }
    ]
  },
  "summary": {
    "total_files_processed": 658,
    "total_nodes": 12450,
    "total_edges": 8932,
    "checkpoints_used": 234,
    "api_requests_saved": 234
  }
}
```

### O Que é Medido

1. **Tempo Efetivo (`effective_analysis_time_ms`)**:
   - Mede apenas tempo de trabalho real
   - Exclui automaticamente períodos de pausa por API
   - Representa o tempo real de processamento

2. **Tempo Total (`total_analysis_time_ms`)**:
   - Inclui tempo de pausas automáticas
   - Tempo decorrido desde início até fim
   - Útil para planejamento de tempo total

3. **Tempo de Pausa (`total_pause_time_ms`)**:
   - Tempo acumulado em pausas automáticas por API
   - Calculado automaticamente pelo sistema
   - Importante para métricas de eficiência

4. **Economia de Checkpoint**:
   - Arquivos com `analysis_time_ms: 0.0` foram reaproveitados
   - Redução significativa no uso da API
   - Economia de tempo e recursos

Para detalhes completos, veja [docs/checkpoint_system.md](docs/checkpoint_system.md).

## Estrutura do Projeto

```
analisador/
├── modules/              # Módulos principais
│   ├── analise/         # Análise de código
│   ├── sintese/         # Síntese de grafos
│   ├── grafo/           # Visualização
│   ├── dashboard/       # Dashboard analítico
│   └── auth/            # Autenticação
├── services/            # Serviços auxiliares
│   ├── ollama_service.py
│   ├── timing_logger_service.py
│   └── analysis_timer_service.py
├── storage/             # Dados persistentes
│   ├── export/          # Arquivos de timing
│   ├── data/            # Resultados JSON
│   └── *.db             # Bancos SQLite
├── docs/                # Documentação
└── main.py              # Ponto de entrada
```

## Logs e Debug

### Logs da Aplicação
- Localização: `log/app.log`
- Níveis: INFO, WARNING, ERROR
- Logs em tempo real na interface

### Logs de Timing
- Localização: `storage/export/timing_*.json`
- Gerado automaticamente após cada análise
- Inclui métricas detalhadas por arquivo

## Configuração

A configuração pode ser ajustada na interface ou diretamente no arquivo:

- `llm_modelo`: Modelo LLM a usar
- `llm_temperatura`: Criatividade da geração (0.0-1.0)
- `llm_tamanho_contexto`: Tamanho do contexto (tokens)

## Troubleshooting

### Problemas Comuns

1. **Ollama não conectado**
   - Verifique se `ollama serve` está rodando
   - Confirme a URL em `http://localhost:11434`

2. **Modelo não encontrado**
   - Use `ollama list` para ver modelos disponíveis
   - Baixe com `ollama pull <modelo>`

3. **Timeout na análise**
   - Aumente o timeout para análises complexas
   - Reduza o tamanho do contexto

4. **Arquivo de timing não gerado**
   - Verifique permissões em `storage/export/`
   - Confirme se a análise foi concluída com sucesso

## Contribuição

1. Fork o projeto
2. Crie uma branch de feature
3. Faça commit das mudanças
4. Abra um Pull Request

## Licença

MIT License - Veja o arquivo LICENSE para detalhes.

## Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação em `docs/`

- Verifique os logs em `log/app.log`


