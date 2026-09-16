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

- `text` → usada na configuração para localizar o dispositivo Zigbee2MQTT
- `button` → ativar modo de aprendizado (ex.: `button.ir_qa_switch_learn_ir_code`)
- `sensor` → fallback do código IR aprendido (limitado a 255 caracteres no HA)

Esta integração conecta essas entidades e as expõe como um **remote padrão do HA**.

O envio **não** usa `text.set_value` quando o tópico MQTT é conhecido. A entidade `text` do Home Assistant ignora o mesmo valor repetido (ex.: vários `volume_up`) e corta códigos longos em 255 caracteres.

Os comandos são publicados via MQTT no `command_topic` do discovery da entidade text (ex.: `zigbee2mqtt2/ir_qa/set`), com `{"ir_code_to_send": "..."}`, em fila, com um intervalo entre cada envio. Assim o hub vai para a instância correta do Zigbee2MQTT (`zigbee2mqtt1`, `zigbee2mqtt2`, …) sem configurar o tópico na mão.

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
- Entidade text usada para localizar o hub (o tópico MQTT, inclusive o prefixo da instância Z2M, vem do discovery)
- Entidade button para ativar modo de aprendizado
- Entidade sensor que recebe o código aprendido (fallback)
- Intervalo entre envios IR (padrão **2,0 s**), para o hub Zigbee terminar cada comando antes do próximo

Esse intervalo também pode ser alterado depois em **opções da integração**, sem recriar.

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
- O código IR em Base64 é lido do MQTT do dispositivo (completo) ou do sensor
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
