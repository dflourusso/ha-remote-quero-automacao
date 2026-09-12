# QA IR Remote

Integração para Home Assistant que transforma um hub IR da **QA** em uma
entidade `remote` nativa do HA.

Essa integração permite:

- Enviar comandos IR via `remote.send_command`
- Aprender comandos IR via `remote.learn_command`
- Persistir códigos IR em arquivos locais do Home Assistant
- Controlar múltiplos dispositivos (ar-condicionado, TV, receiver, etc.)
- Integrar facilmente com outras integrações como `climate`, `media_player` e automações

---

## ✨ Conceito

O hub QA expõe entidades do Home Assistant:

- `text` → envio de código IR em Base64
- `button` → ativar modo de aprendizado (ex.: `button.ir_qa_switch_learn_ir_code`)
- `sensor` → receber o código IR aprendido

Esta integração conecta essas entidades e as expõe como um **remote padrão do HA**.

---

## 📦 O que esta integração cria

- Uma entidade: `remote.qa_<nome>`
- Um diretório de armazenamento: `/config/qa_ir/`
- Um arquivo por perfil: `/config/qa_ir/<profile>.json`

---

## 🗂️ Estrutura do arquivo IR

```json
{
  "commands": {
    "climate_sala": {
      "cool_auto_24": "BASE64...",
      "off": "BASE64..."
    },
    "tv": {
      "on": "BASE64...",
      "mute": "BASE64..."
    }
  }
}
```
- Um único arquivo pode conter vários dispositivos
- Cada dispositivo pode ter qualquer conjunto de comandos

---
## ⚙️ Configuração

Durante a configuração você precisará informar:

- Nome
- Perfil QA (nome do arquivo)
- Entidade text usada para envio do IR
- Entidade button para ativar modo de aprendizado
- Entidade sensor que recebe o código aprendido

## ▶️ Enviar comando IR

```yaml
action: remote.send_command
target:
  entity_id: remote.qa_sala
data:
  device: climate_sala
  command: cool_auto_24
```

## 🎓 Aprender comando IR
```yaml
action: remote.learn_command
target:
  entity_id: remote.qa_sala
data:
  device: climate_sala
  command: cool_auto_24
```
Fluxo de aprendizado

- O botão de aprendizado é pressionado
- O usuário aponta o controle físico para o hub
- O sensor recebe o código IR em Base64
- O código é salvo automaticamente no arquivo

---
## Instalação (HACS)

Esta integração pode ser instalada utilizando o HACS (Home Assistant Community Store).

### Pré-requisitos
- Home Assistant instalado e funcionando
- HACS instalado e configurado

### Passo a passo

- Abra o HACS no Home Assistant
- Vá em Integrações
- Clique no menu ⋮ (três pontos) no canto superior direito
- Selecione Repositórios personalizados
- Adicione o repositório:
- Repositório: `https://github.com/dflourusso/ha-remote-quero-automacao`
- Categoria: Integração
- Clique em Adicionar
- Procure por QA Remote no HACS
- Clique em Download
- Reinicie o Home Assistant

#### Após a instalação

- Vá em Configurações → Dispositivos e Serviços
- Clique em Adicionar Integração
- Procure por QA Remote
- Siga o fluxo de configuração
