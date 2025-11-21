# 📖 Guia de Desenvolvimento

Guia para desenvolver e estender o Agente Analista de Código v2.0 (Simplificado).

## 🎯 **Princípios da Arquitetura Simplificada**
- **DRY**: Componentes genéricos reutilizáveis
- **KISS**: Soluções simples, sem over-engineering
- **Single Responsibility**: Cada componente com responsabilidade clara
- **Template Method**: Padrões consistentes entre controllers

---

## 🏗️ **Estrutura do Projeto**

```
analisador/
├── core/                           # 🆕 Componentes compartilhados
│   ├── base_controller.py          # Controller genérico base
│   ├── ui_components.py            # Cards genéricos (Config, Execution, Files)
│   └── view_manager_template.py     # Template para views
├── services/                       # Serviços especializados
│   └── unified_timing_service.py   # ⚡ Timing unificado (3→1)
├── modules/                        # Módulos específicos
│   ├── analise/                    # Análise de código (refatorada)
│   ├── sintese/                    # Síntese de grafos
│   ├── grafo/                      # Visualização
│   └── dashboard/                  # Analytics com RAG
├── storage/                        # Dados persistentes
│   ├── data/                       # Resultados de análises
│   ├── export/                     # Exportações e timing
│   └── analytics.db                 # Banco de dados
└── docs/                           # Documentação
    ├── SIMPLIFICATION_REPORT.md    # Relatório da refatoração
    └── DEVELOPMENT_GUIDE.md         # Este guia
```

---

## 🎮 **Desenvolvimento de Controllers**

### **Usando o BaseController**

Todos os controllers devem herdar de `BaseController` para aproveitar funcionalidades comuns:

```python
from core.base_controller import BaseController

class MyController(BaseController):
    def __init__(self, model, notifier, auth_controller=None):
        super().__init__(model, notifier, auth_controller)

        # Apenas serviços específicos do módulo
        self.specific_service = SpecificService()

    def start_operation_example(self):
        """Exemplo de operação usando padrão unificado"""
        if not self.start_operation("minha operação"):
            return False

        try:
            # Sua lógica específica aqui
            result = self.model.specific_operation()

            # Finaliza com sucesso usando BaseController
            self.finish_operation(True, result)
            return True

        except Exception as e:
            # Finaliza com erro usando BaseController
            self.finish_operation(False, None, str(e))
            return False
```

### **Padrões de UI Integration**

O BaseController gerencia automaticamente componentes UI:

```python
# Os componentes UI são conectados automaticamente
def setup_ui(self):
    # Os cards da UI usarão este método para conectar os componentes
    pass  # BaseController já implementa set_ui_components()
```

---

## 🎨 **Componentes UI Genéricos**

### **ConfigCard - Configurações Dinâmicas**

Use `ConfigCard` para criar interfaces de configuração consistentes:

```python
from core.ui_components import ConfigCard

def create_config_card(controller):
    """Exemplo de criação de ConfigCard"""
    fields = [
        {
            'name': 'model',
            'label': 'Modelo LLM',
            'type': 'dropdown',
            'options': ['codellama', 'llama2', 'mistral'],
            'default': 'codellama',
            'width': 300,
            'icon': ft.Icons.SMART_TOY
        },
        {
            'name': 'temperature',
            'label': 'Temperatura',
            'type': 'slider',
            'min': 0.0,
            'max': 2.0,
            'default': 0.7,
            'divisions': 20
        },
        {
            'name': 'detailed_analysis',
            'label': 'Análise Detalhada',
            'type': 'checkbox',
            'default': True
        }
    ]

    return ConfigCard(
        title="Configuração do Módulo",
        fields=fields,
        on_save=controller.update_config,
        on_load=controller.get_default_config
    )
```

**Tipos de Campo Suportados:**
- `text`: Campo de texto
- `dropdown`: Menu suspenso
- `checkbox`: Caixa de seleção
- `slider`: Slider numérico
- `switch`: Interruptor

### **ExecutionCard - Controle de Execução**

Use `ExecutionCard` para controle padronizado de operações:

```python
from core.ui_components import ExecutionCard

def create_execution_card(controller):
    """Exemplo de criação de ExecutionCard"""
    return ExecutionCard(
        title="Controle de Execução",
        on_start=lambda: controller.start_operation_example(),
        on_pause=controller.pause_operation if hasattr(controller, 'pause_operation') else None,
        on_stop=controller.stop_operation if hasattr(controller, 'stop_operation') else None,
        on_reset=lambda: controller.reset_ui()
    )
```

### **FilesCard - Seleção de Arquivos**

Use `FilesCard` para seleção consistente de arquivos:

```python
from core.ui_components import FilesCard

def create_files_card():
    """Exemplo de criação de FilesCard"""
    return FilesCard(
        title="Seleção de Arquivos",
        file_extensions=['.c', '.h', '.cpp', '.hpp', '.py', '.js', '.ts'],
        on_files_selected=lambda: open_file_dialog(),
        on_clear=lambda: clear_file_selection()
    )
```

---

## ⏱️ **Usando o UnifiedTimingService**

O `UnifiedTimingService` substitui 3 serviços anteriores:

```python
from services.unified_timing_service import UnifiedTimingService

class MyController(BaseController):
    def __init__(self, model, notifier, auth_controller=None):
        super().__init__(model, notifier, auth_controller)

        # Substitui: AnalysisTimerService + TimingLoggerService + Ollama timing
        self.timing_service = UnifiedTimingService()

    def start_analysis_example(self, files, config):
        """Exemplo de uso do serviço de timing"""
        # Inicia medição (interface compatível com múltiplos formatos)
        self.timing_service.start_analysis(
            project_name="meu_projeto",
            file_count=len(files),
            files=files,
            config=config,
            language="Python",  # Novo parâmetro
            project_root="/path/to/project"  # Novo parâmetro
        )

        # Durante o processamento
        for file in files:
            # Registra tempo de processamento do arquivo
            self.timing_service.add_file_timing(
                file_path=file,
                analysis_time_ms=1500.0,
                nodes_count=10,
                edges_count=5
            )

            # Registra chamada LLM (novo recurso)
            self.timing_service.add_llm_timing(
                operation=f"analyze_{file}",
                duration_ms=1200.0,
                model=config.get('model', 'unknown')
            )

        # Finaliza análise
        self.timing_service.finish_analysis(
            success=True,
            results_count=len(files)
        )

        # Obtém estatísticas consolidadas
        stats = self.timing_service.get_statistics()
        print(f"Total de análises: {stats['total_analyses']}")
        print(f"Tempo total LLM: {stats['total_llm_time_seconds']}s")
```

---

## 🔌 **Adicionando Novos Módulos**

### **Passo 1: Criar o Controller**

```python
# modules/meu_modulo/controller.py
from core.base_controller import BaseController

class MeuModuloController(BaseController):
    def __init__(self, model, notifier, auth_controller=None):
        super().__init__(model, notifier, auth_controller)

        # Serviços específicos do módulo
        self.meu_servico = MeuServico()

    def minha_operacao(self, params):
        """Operação principal do módulo"""
        if not self.start_operation("minha operação"):
            return False

        try:
            # Sua lógica aqui
            result = self.meu_servico.processar(params)

            # Atualiza UI via BaseController
            self.update_progress(1.0, "Operação concluída")
            self.finish_operation(True, result)
            return True

        except Exception as e:
            self.finish_operation(False, None, str(e))
            return False
```

### **Passo 2: Criar a View com Componentes Genéricos**

```python
# modules/meu_modulo/view/view_manager.py
from core.ui_components import ConfigCard, ExecutionCard, FilesCard
import flet as ft

class ViewManager:
    def __init__(self, controller, notifier, page):
        self.controller = controller
        self.notifier = notifier
        self.page = page

    def build(self):
        """Constrói view usando componentes genéricos"""

        # ConfigCard para configurações do módulo
        config_card = ConfigCard(
            title="Configuração - Meu Módulo",
            fields=[
                {
                    'name': 'opcao1',
                    'label': 'Opção 1',
                    'type': 'text',
                    'default': 'valor_padrao'
                },
                {
                    'name': 'opcao2',
                    'label': 'Opção 2',
                    'type': 'checkbox',
                    'default': True
                }
            ],
            on_save=self.controller.update_config,
            on_load=self.controller.get_default_config
        )

        # ExecutionCard para controle da operação
        execution_card = ExecutionCard(
            title="Controle de Execução",
            on_start=lambda: self.controller.minha_operacao({}),
            on_stop=lambda: self.controller.stop_operation()
        )

        # Layout responsivo
        return ft.Column([
            ft.Row([config_card, execution_card]),
            # Outros componentes específicos do módulo
        ])
```

### **Passo 3: Registrar no Main**

```python
# main.py
from modules.meu_modulo.controller import MeuModuloController
from modules.meu_modulo.model import MeuModuloModel
from modules.meu_modulo.view.view_manager import ViewManager

class MainApp:
    def _initialize_modules(self):
        # Adicionar à lista de módulos existentes
        # ...

        # Meu novo módulo
        meu_modulo_model = MeuModuloModel(self.notifier)
        self.meu_modulo_controller = MeuModuloController(
            meu_modulo_model,
            self.notifier,
            self.auth_controller
        )
        self.meu_modulo_controller.auth_controller = self.auth_controller

    def _show_main_interface(self):
        # Adicionar nova aba
        tabs = ft.Tabs(
            tabs=[
                # Abas existentes...
                ft.Tab(
                    text="Meu Módulo",
                    icon=ft.Icons.EXTENSION,
                    content=ft.Container(
                        content=ViewManager(
                            self.meu_modulo_controller,
                            self.notifier,
                            self.page
                        ).build(),
                        padding=10
                    )
                )
            ]
        )
```

---

## 🧪 **Testes e Debug**

### **Debug Integrado**

O BaseController inclui logging detalhado:

```python
# Ativar debug em modo desenvolvimento
import logging
logging.getLogger('core.base_controller').setLevel(logging.DEBUG)
logging.getLogger('modules.meu_modulo').setLevel(logging.DEBUG)
```

### **Testes Unitários**

```python
# tests/test_base_controller.py
import unittest
from core.base_controller import BaseController
from unittest.mock import Mock

class TestBaseController(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.notifier = Mock()
        self.controller = BaseController(self.model, self.notifier)

    def test_start_operation(self):
        """Testa gerenciamento de operação"""
        result = self.controller.start_operation("teste")
        self.assertTrue(result)
        self.assertTrue(self.controller.is_active)
        self.assertEqual(self.controller.current_operation, "teste")
```

---

## 🔄 **Padrões de Código**

### **Controllers**
- ✅ Sempre herdar de `BaseController`
- ✅ Usar `start_operation()` e `finish_operation()`
- ✅ Implementar callbacks via BaseController
- ✅ Logging com `logger.debug()` para debug

### **UI Components**
- ✅ Usar componentes genéricos do `core/`
- ✅ Não duplicar ConfigCard, ExecutionCard, FilesCard
- ✅ Usar `ConfigCard` com configuração dinâmica
- ✅ Manter consistência visual

### **Services**
- ✅ Usar `UnifiedTimingService` para timing
- ✅ Evitar criar múltiplos serviços para mesma função
- ✅ Compatibilidade com dados existentes

---

## 🐛 **Debug e Troubleshooting**

### **Logs de Debug**

O projeto tem logging detalhado em múltiplos níveis:

```python
# Ver logs específicos
import logging

# Ativar debug para componentes específicos
logging.getLogger('core.base_controller').setLevel(logging.DEBUG)
logging.getLogger('services.unified_timing_service').setLevel(logging.DEBUG)
logging.getLogger('modules.analise').setLevel(logging.DEBUG)

# Ativar debug para todos os módulos
logging.getLogger().setLevel(logging.DEBUG)
```

### **Problemas Comuns e Soluções**

1. **UI não atualiza:**
   - Verifique se `set_ui_components()` foi chamado
   - Confirme se `page` foi passada corretamente
   - Use logs de debug do BaseController

2. **Configuração não salva:**
   - Verifique callbacks do ConfigCard
   - Confirme se `update_config()` está implementado
   - Use logs para validar fluxo

3. **Timing não registra:**
   - Use `UnifiedTimingService` em vez de serviços antigos
   - Verifique se `finish_analysis()` foi chamado
   - Confirme compatibilidade com formato de dados

---

## 🐛 **Sistema UltraThink de Debug**

O sistema UltraThink fornece rastreamento completo de instâncias e callbacks para diagnóstico avançado.

### **Ativação do Sistema UltraThink**

O UltraThink está sempre ativo e pode ser configurado através do nível de log:

```python
# Nível INFO para ver mensagens UltraThink
logging.getLogger('modules.analise').setLevel(logging.INFO)

# Nível DEBUG para mensagens detalhadas
logging.getLogger('modules.analise').setLevel(logging.DEBUG)
```

### **Formato dos Logs UltraThink**

```
🆔 [ULTRATHINK] IDENTIFICAÇÃO: Mensagem principal
🔍 [ULTRATHINK] DEBUG: Informação detalhada
📊 [ULTRATHINK] MÉTRICAS: Dados numéricos
🚀 [ULTRATHINK] OPERAÇÃO: Início/Fim de operações
⚡ [ULTRATHINK] ESTADO: Estado do sistema
✅ [ULTRATHINK] SUCESSO: Operação bem-sucedida
❌ [ULTRATHINK] ERRO: Falha com detalhes
```

### **Identificação de Instâncias**

Cada componente tem um ID único para rastreamento:

```python
# IDs no AnaliseController
controller_id = "64a01969"  # UUID abreviado
thread_id = "82752"       # Thread ID

# IDs no UnifiedTimingService
service_id = "a1b2c3d4"    # UUID do serviço
instance_id = "0x1f52c6d8050"  # Endereço de memória
```

### **Fluxo de Rastreamento**

1. **Criação**: Controller e serviços criados com IDs únicos
2. **Início**: `start_analysis()` rastreado com IDs
3. **Callbacks**: Cada chamada registrada com thread e controller
4. **Métricas**: `add_file_timing()` e `add_llm_timing()` rastreados
5. **Finalização**: `finish_analysis()` com estado completo

### **Exemplo de Diagnóstico**

```bash
# Procurar por arquivos não registrados
grep "📊.*File timing" app.log | wc -l
# Deve corresponder ao número de arquivos analisados

# Verificar se callbacks foram chamados
grep "🆔.*CALLBACK INICIADO" app.log

# Identificar problemas de instâncias
grep "🆔.*controller.*ID" app.log | sort | uniq -c
```

### **Problemas Comuns Detectáveis**

1. **Múltiplas Instâncias**:
   ```bash
   grep "🆔.*AnaliseController CRIADO" app.log
   # Se aparecer mais de uma vez, há instâncias duplicadas
   ```

2. **Callbacks Não Chamados**:
   ```bash
   grep "📞.*EXECUTANDO progress_callback" app.log
   grep "🆔.*CALLBACK INICIADO" app.log
   # O primeiro deve existir, segundo deve corresponder
   ```

3. **Métricas Não Registradas**:
   ```bash
   grep "📊.*add_file_timing" app.log
   # Deve aparecer para cada arquivo analisado
   ```

### **Tips de Debug UltraThink**

- Use IDs para correlacionar logs entre componentes
- Verifique se `Controller ID` é o mesmo no início e fim
- Confirme se `Thread ID` corresponde entre model e controller
- Monitore `files` e `llm_calls` arrays no `finish_analysis`

---

## 📚 **Documentação de Referência**

- **[SIMPLIFICATION_REPORT.md](SIMPLIFICATION_REPORT.md)**: Relatório completo da refatoração
- **[BUG_FIX_REPORT.md](BUG_FIX_REPORT.md)**: Correções realizadas
- **[README.md](README.md)**: Visão geral e instruções de uso

---

## 🚀 **Boas Práticas**

1. **Use os componentes genéricos** - Não crie novos Cards
2. **Herdade BaseController** - Elimine código duplicado
3. **Padronize callbacks** - Use métodos do BaseController
4. **Log consistentemente** - Use logger.debug() para troubleshooting
5. **Mantenha compatibilidade** - Preserve dados e interfaces existentes
6. **Teste incrementalmente** - Valide cada mudança

---

**Status:** ✅ **Guia Atualizado v2.0**
**Last Update:** 18 de Novembro de 2025
**Compatível:** Python 3.8+ | Flet | Simplified Architecture