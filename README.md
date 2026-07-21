# 🔧 Automação de Switch Cisco — Desafio Mercado Livre

Projeto desenvolvido para o **Desafio de Automação — Laboratório de Candidatos (Networking Mercado Livre)**.

Consiste em um script Python, com frontend web em Flask, que se conecta via SSH a um switch Cisco (simulado no **GNS3**, usando um roteador c3725 com módulo NM-16ESW) para:

- Configurar VLANs (ID + nome) definidas pelo usuário
- Alterar o hostname do switch
- Salvar a configuração na NVRAM
- Gerar backup local da configuração (nomeado com hostname + data/hora)
- Validar se a configuração aplicada corresponde ao esperado, exibindo alertas em caso de divergência

> 📄 Este repositório também contém o planejamento da **Parte 2** do desafio (VPN IPSec entre FortiGate e Palo Alto): veja [`plano-vpn-ipsec.md`](./plano-vpn-ipsec.md).

---

## 🗂️ Estrutura do projeto

```
Automacao-ML/
├── app.py
├── switch_automation.py
├── templates/
│   └── index.html
├── backups/
├── evidencias/
├── plano-vpn-ipsec.md
└── requirements.txt
```
---

## ⚙️ Como executar

### Pré-requisitos
- Python 3.10+
- Um switch Cisco acessível via SSH (real, ou simulado — este projeto foi testado com **GNS3**, roteador c3725 + módulo NM-16ESW, com SSH habilitado)

### Instalação

```bash
git clone https://github.com/viniciusk1/Automacao-ML.git
cd Automacao-ML
pip install -r requirements.txt
```

### Configuração

Edite o dicionário `SWITCH` no início do arquivo `switch_automation.py` com o IP, usuário e senha do seu switch:

```python
SWITCH = {
    "device_type": "cisco_ios",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "cisco123",
    "secret": "cisco123",
    "port": 22,
}
```

### Executar

```bash
python app.py
```

Acesse no navegador: **http://127.0.0.1:5000**

---

## 🖥️ Como usar o frontend

1. Ao abrir a página, o formulário já vem preenchido com o hostname padrão (`SWITCH_AUTOMATIZADO`) e as 3 VLANs mínimas exigidas pelo desafio (VLAN 10 — VLAN_DADOS, VLAN 20 — VLAN_VOZ, VLAN 50 — VLAN_SEGURANCA).
2. É possível editar qualquer campo antes de aplicar.
3. Ao clicar em **"Aplicar Configuração no Switch"**, o sistema:
   - Conecta ao switch via SSH (Netmiko)
   - Aplica hostname e VLANs
   - Salva a configuração na NVRAM
   - Gera um backup local
   - Valida se tudo foi aplicado corretamente
4. O resultado é exibido na própria página, incluindo eventuais alertas de divergência.

---

## 📸 Evidências

| Descrição | Arquivo |
|---|---|
| Frontend após configuração aplicada com sucesso | `evidencias/01_frontend_sucesso.png` |
| CLI do switch confirmando VLANs e hostname | `evidencias/02_switch_vlans.png` |
| Arquivo de backup gerado localmente | `evidencias/03_backup_gerado.png` |

---

## 🧠 Notas de implementação

- **Ambiente de simulação:** O GNS3, por emular um IOS real, permite essa ponte via um nó *Cloud* conectado a um adaptador de rede do host (neste projeto, um adaptador **TAP-Windows**).
- **Compatibilidade SSH:** o IOS usado no laboratório é uma versão antiga, exigindo algoritmos criptográficos legados (`diffie-hellman-group1-sha1`, `ssh-rsa`, `aes128-cbc`, `hmac-sha1`) para negociar a conexão SSH via cliente OpenSSH. A biblioteca Netmiko/Paramiko, usada pelo script, já suporta esses algoritmos nativamente.
- **Comando de validação específico do hardware:** o roteador c3725 com módulo NM-16ESW usa o comando `show vlan-switch brief` (em vez do tradicional `show vlan brief`) para listar VLANs — o script foi ajustado para isso.
- **Troca de hostname:** implementada como uma etapa isolada dos demais comandos, pois a alteração do hostname muda o prompt do dispositivo em tempo real; o script atualiza explicitamente o prompt esperado pelo Netmiko (`set_base_prompt()`) para evitar falhas de sincronismo.
- **Idempotência:** o script pode ser executado múltiplas vezes sem causar erros — VLANs já existentes são apenas confirmadas/corrigidas.

---

## ✅ Requisitos atendidos (Parte 1)

- [x] Script de automação em Python com Netmiko
- [x] Frontend web (Flask) para inserir VLANs
- [x] Configuração de VLAN 10, 20 e 50 via frontend
- [x] Alteração de hostname via script
- [x] Salvamento da configuração na NVRAM
- [x] Backup local com hostname + data/hora no nome
- [x] Validação da configuração aplicada, com alertas de divergência
- [x] Controle de versões via Git, com commits organizados

