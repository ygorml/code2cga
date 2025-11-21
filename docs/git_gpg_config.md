# Configuração Git - Assinatura GPG Automática

## Configurações Aplicadas (Global)

As seguintes configurações foram aplicadas ao Git para garantir que todos os commits futuros sejam assinados automaticamente com GPG:

### ✅ Configurações Ativadas

```bash
# Ativa assinatura GPG para todos os commits
git config --global commit.gpgsign true

# Permite assinatura sem TTY (terminal)
git config --global gpg.allow-sign-with-notty true
git config --global gpg.allowsignwithnotty true
```

### 🔐 Configurações Verificadas

- **user.name**: Ygor W. S. Moreira Lima
- **user.email**: eu@ygor.ml
- **user.signingkey**: 343E1D0F0093E32B3FBBF7DD447410069D97A299
- **commit.gpgsign**: true ✅
- **gpg.allow-sign-with-notty**: true ✅
- **gpg.allowsignwithnotty**: true ✅

### 📁 Local da Configuração

As configurações estão salvas em: `~/.gitconfig`

### 🚀 Uso

A partir de agora, todos os comandos `git commit` (independente de flags) criarão commits assinados:

```bash
# Todos estes comandos criarão commits assinados:
git commit -m "mensagem"
git commit -am "mensagem"
git commit --no-edit
git commit --amend
# etc...
```

### ⚠️ Notas Importantes

1. **Assinatura Automática**: Não é necessário usar `-S` ou `--gpg-sign`
2. **Segurança**: Mantenha sua chave GPG segura
3. **Fallback**: Se houver problemas com a assinatura, pode ser temporariamente desativado com:
   ```bash
   git commit --no-gpg-sign -m "mensagem"
   ```

### 🔧 Verificação

Para verificar se um commit está assinado:
```bash
git verify-commit HEAD
git log --show-signature
git cat-file commit HEAD | grep -A 5 "gpgsig"
```

---

**Configurado em:** $(date)
**Status:** ✅ Ativo e funcionando