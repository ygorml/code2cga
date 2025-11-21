# 📚 Documentação do Agente Analista de Código

Bem-vindo à documentação oficial do Agente Analista de Código v2.0 (Simplificado).

## 📖 Documentação Disponível

### 🛠️ [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
Guia completo para desenvolvedores v2.0:
- Padrões de código e arquitetura simplificada
- Como adicionar novos módulos
- Componentes genéricos reutilizáveis
- Debug e troubleshooting
- Exemplos práticos de uso

### 📊 [SIMPLIFICATION_REPORT.md](SIMPLIFICATION_REPORT.md)
Relatório completo da refatoração de Novembro 2025:
- Reduções alcançadas (timing: 67%, controller: 32%)
- Benefícios da simplificação
- Arquitetura antes vs depois
- Métricas de impacto

### 📋 Estrutura do Projeto

```
analisador/                     # Raiz
├── README.md                  # Visão geral e instalação
├── CLAUDE.md                   # Instruções Claude Code
└── docs/                      # 📁 Documentação técnica
    ├── DEVELOPMENT_GUIDE.md    # Guia para devs
    └── SIMPLIFICATION_REPORT.md # Histórico de refatoração
```

---

## 🎯 **Como Usar a Documentação**

### **Para Novos Desenvolvedores**
1. Comece com `README.md` na raiz
2. Depois use `docs/DEVELOPMENT_GUIDE.md` para desenvolvimento
3. Consulte docstrings no código para referências específicas

### **Para Manutenção**
1. `docs/DEVELOPMENT_GUIDE.md` para padrões e arquitetura
2. Docstrings no código para interfaces específicas
3. `docs/SIMPLIFICATION_REPORT.md` para entender decisões de design

### **Para Debug**
- Use logs de debug conforme guia de desenvolvimento
- Consulte `README.md` para problemas comuns
- Use docstrings para entender APIs

---

**Última Atualização:** 18 de Novembro de 2025
**Versão:** 2.0 (Simplificado)
**Arquitetura:** DRY e KISS aplicados