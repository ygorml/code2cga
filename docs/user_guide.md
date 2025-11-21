# Guia do Usuário

## Índice
1. [Introdução](#introdução)
2. [Instalação](#instalação)
3. [Configuração Inicial](#configuração-inicial)
4. [Análise de Código](#análise-de-código)
5. [Visualização de Grafos](#visualização-de-grafos)
6. [Síntese de Resultados](#síntese-de-resultados)
7. [Dashboard](#dashboard)
8. [Dicas e Truques](#dicas-e-truques)
9. [Solução de Problemas](#solução-de-problemas)

## Introdução

O Analisador de Grafos de Chamada é uma ferramenta poderosa para análise de código-fonte
que utiliza Modelos de Linguagem Grande (LLMs) para extrair informações estruturadas
sobre o fluxo de execução e dependências do seu código.

### Principais Funcionalidades
- Análise automatizada de múltiplos arquivos
- Geração de grafos de chamada interativos
- Identificação de dependências e acoplamentos
- Síntese automática dos resultados
- Suporte a múltiplas linguagens de programação
- Interface intuitiva baseada em Flet

## Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Ollama (para modelos LLM locais)
- Git

### Passos de Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-repo/analisador_grafos_chamada_LLM.git
   cd analisador_grafos_chamada_LLM
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instale e inicie o Ollama:**
   ```bash
   # Baixe e instale Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Inicie o serviço Ollama
   ollama serve

   # Baixe um modelo recomendado
   ollama pull codellama
   ollama pull llama2
   ```

## Configuração Inicial

### 1. Executar a Aplicação
```bash
python main.py
```

### 2. Configurar o LLM
Na tela inicial, configure:
- **URL do Ollama**: `http://localhost:11434` (padrão)
- **Modelo**: Selecione um modelo instalado (ex: `codellama`)
- **Tamanho do Contexto**: 4096 (recomendado)
- **Temperatura**: 0.7 (equilíbrio entre criatividade e precisão)

### 3. Testar Conexão
Clique em "Testar Conexão" para verificar se o Ollama está respondendo corretamente.

## Análise de Código

### Passo 1: Selecionar Arquivos
1. Navegue até o módulo "Análise"
2. Clique em "Selecionar Arquivos" ou arraste-os para a área indicada
3. Formatos suportados: `.py`, `.java`, `.c`, `.cpp`, `.js`, `.ts`

### Passo 2: Configurar Análise
Configure os parâmetros de análise:
- **Nível de Análise**:
  - `Simples`: Apenas estrutura básica
  - `Detalhado`: Informações completas (recomendado)
  - `Resumido`: Apenas pontos principais

- **Opções Adicionais**:
  - Incluir comentários na análise
  - Analisar dependências
  - Gerar arquivo JSON
  - Gerar explicabilidade

- **Limites**:
  - Limite de linhas por arquivo (padrão: 1000)
  - Linguagem de programação (detectada automaticamente)

### Passo 3: Executar Análise
1. Clique em "Iniciar Análise"
2. Monitore o progresso em tempo real
3. Use os botões para:
   - ⏸️ **Pausar**: Pausa temporariamente a análise
   - ▶️ **Retomar**: Continua análise pausada
   - ⏹️ **Parar**: Interrompe a análise

### Passo 4: Visualizar Resultados
Após a conclusão:
- Veja o resumo estatístico
- Acesse os detalhes de cada arquivo
- Exporte resultados em diversos formatos

## Visualização de Grafos

### Tipos de Grafos
1. **Grafo de Chamadas**: Mostra as relações de chamada entre funções
2. **Grafo de Dependências**: Exibe dependências entre módulos
3. **Grafo de Herança**: Visualiza hierarquias de classes (para POO)

### Interagindo com o Grafo
- **Zoom**: Use o scroll do mouse
- **Pan**: Clique e arraste
- **Selecionar Nó**: Clique em um nó para ver detalhes
- **Filtrar**: Use os controles para filtrar tipos de nós/arestas
- **Buscar**: Use a busca para encontrar nós específicos

### Exportando Grafos
- **PNG**: Imagem estática em alta resolução
- **SVG**: Vetor escalável (ideal para documentos)
- **JSON**: Dados brutos para processamento posterior
- **DOT**: Formato Graphviz

## Síntese de Resultados

### Gerando Sínteses
1. Após completar uma análise, vá para o módulo "Síntese"
2. Selecione os resultados a sintetizar
3. Escolha o tipo de síntese:
   - **Resumo Executivo**: Pontos principais em linguagem simples
   - **Análise Técnica**: Detalhes técnicos profundos
   - **Recomendações**: Sugestões de melhoria
   - **Storytelling**: Narrativa sobre a arquitetura

### Personalizando a Síntese
- **Template**: Use templates predefinidos ou crie o seu
- **Foco**: Direcione a análise para aspectos específicos
- **Formato**: Escolha entre Markdown, HTML ou texto puro

## Dashboard

### Métricas Principais
O dashboard exibe:
- **Total de Análises**: Quantidade de análises realizadas
- **Arquivos Processados**: Número total de arquivos analisados
- **Linhas de Código**: Total de linhas analisadas
- **Complexidade Acumulada**: Métrica de complexidade geral

### Histórico
- Visualize o histórico completo de análises
- Filtre por data, tipo ou resultado
- Compare análises diferentes

### Insights Automáticos
O sistema gera insights automaticamente:
- **Nós Críticos**: Funções/classes mais importantes
- **Gargalos**: Pontos de atenção no código
- **Recomendações**: Sugestões baseadas nos padrões encontrados

## Dicas e Truques

### Performance
- **Análise em Lote**: Analise múltiplos arquivos de uma vez
- **Limitar Contexto**: Reduza o tamanho do contexto para arquivos grandes
- **Modelos Leves**: Use modelos mais leves para análises rápidas

### Qualidade da Análise
- **Code Splitting**: Separe arquivos muito grandes
- **Documentação**: Mantenha comentários descritivos
- **Nomenclatura**: Use nomes claros e descritivos

### Comandos Úteis
```bash
# Ver modelos disponíveis no Ollama
ollama list

# Limpar cache de análises
rm -rf storage/temp/*

# Resetar configurações
rm -f config.json
```

## Solução de Problemas

### Problemas Comuns

#### 1. Ollama não conecta
- **Sintoma**: "Falha ao conectar ao Ollama"
- **Solução**:
  - Verifique se o Ollama está rodando: `ps aux | grep ollama`
  - Reinicie o serviço: `systemctl restart ollama`
  - Verifique a porta: `netstat -an | grep 11434`

#### 2. Análise muito lenta
- **Sintoma**: Análise demorando muito tempo
- **Solução**:
  - Reduza o número de threads
  - Diminua o limite de linhas
  - Use um modelo mais rápido (ex: `llama2` ao invés de `codellama`)

#### 3. Memória insuficiente
- **Sintoma**: Erro de memória durante análise
- **Solução**:
  - Analise arquivos menores
  - Reduza o tamanho do contexto
  - Feche outras aplicações

#### 4. JSON inválido na resposta
- **Sintoma**: "Falha ao extrair JSON válido"
- **Solução**:
  - Ajuste a temperatura do modelo (tente 0.3-0.5)
  - Use um prompt mais específico
  - Verifique se o código está sintaticamente correto

### Logs e Debug

Ative o modo debug para informações detalhadas:
```python
# No início do main.py
logging.basicConfig(level=logging.DEBUG)
```

Verifique os logs em:
- Console da aplicação
- Arquivo `log/app.log`
- Logs do Ollama: `journalctl -u ollama`

### Obtendo Ajuda

1. **Documentação**: Verifique a pasta `/docs`
2. **Issues**: Abra uma issue no GitHub
3. **Comunidade**: Participe do fórum da comunidade

## Atalhos e Comandos

### Atalhos de Teclado
- `Ctrl+O`: Abrir arquivos
- `Ctrl+S`: Salvar configurações
- `Ctrl+R`: Iniciar análise
- `Space`: Pausar/Retomar análise
- `Escape`: Parar análise
- `F5`: Atualizar visualização

### Comandos da CLI
```bash
# Executar com configuração customizada
python main.py --config custom.json

# Modo headless (sem UI)
python main.py --headless --input src/ --output results/

# Verificar dependências
python -c "import modules; print('OK')"
```