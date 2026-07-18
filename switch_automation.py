"""
switch_automation.py
Modulo responsavel por toda a comunicacao com o switch Cisco:
- Conexao via SSH (Netmiko)
- Configuracao de VLANs e hostname
- Salvar configuracao (NVRAM)
- Backup da configuracao
- Validacao da configuracao aplicada
"""

import os
from datetime import datetime
from netmiko import ConnectHandler


# ---------------------------------------------------------------------------
# Parametros de conexao com o switch (ajuste IP/usuario/senha se precisar)
# ---------------------------------------------------------------------------
SWITCH = {
    "device_type": "cisco_ios",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "cisco123",
    "secret": "cisco123",
    "port": 22,
}

HOSTNAME_DESEJADO = "SWITCH_AUTOMATIZADO"

VLANS_PADRAO = [
    {"id": 10, "nome": "VLAN_DADOS"},
    {"id": 20, "nome": "VLAN_VOZ"},
    {"id": 50, "nome": "VLAN_SEGURANCA"},
]


# ---------------------------------------------------------------------------
# Conexao
# ---------------------------------------------------------------------------
def conectar_switch(params=None):
    """Abre conexao SSH com o switch e entra em modo privilegiado (enable)."""
    params = params or SWITCH
    connection = ConnectHandler(**params)
    connection.enable()
    return connection


# ---------------------------------------------------------------------------
# Configuracao de VLANs e hostname
# ---------------------------------------------------------------------------
def configurar_vlans(connection, vlans, hostname=None):
    """
    Aplica a configuracao de VLANs e (opcionalmente) o hostname no switch.

    Importante: o hostname e alterado em uma etapa separada dos comandos
    de VLAN. Isso e necessario porque, quando o hostname muda, o "prompt"
    do switch tambem muda (ex: de "SW-LAB#" para "SWITCH_AUTOMATIZADO#").
    O Netmiko usa o prompt para saber quando um comando terminou de
    executar, entao precisamos avisar explicitamente que o prompt mudou
    (com connection.set_base_prompt()) antes de continuar.
    """
    saida_completa = ""

    # --- 1. Trocar o hostname primeiro, isoladamente ---
    if hostname:
        saida_completa += connection.send_config_set([f"hostname {hostname}"])
        # Avisa ao Netmiko que o prompt mudou, para ele nao ficar
        # esperando pelo prompt antigo nos proximos comandos.
        connection.set_base_prompt()

    # --- 2. Configurar as VLANs normalmente ---
    comandos_vlan = []
    for vlan in vlans:
        comandos_vlan.append(f"vlan {vlan['id']}")
        comandos_vlan.append(f"name {vlan['nome']}")
        comandos_vlan.append("exit")

    if comandos_vlan:
        saida_completa += connection.send_config_set(comandos_vlan)

    return saida_completa

# ---------------------------------------------------------------------------
# Salvar configuracao (NVRAM)
# ---------------------------------------------------------------------------
def salvar_configuracao(connection):
    """Executa o equivalente a 'write memory' (salva na NVRAM)."""
    saida = connection.save_config()
    return saida


# ---------------------------------------------------------------------------
# Backup da configuracao
# ---------------------------------------------------------------------------
def fazer_backup(connection, pasta_destino="backups"):
    """Busca a config atual e salva em arquivo local com hostname + data/hora."""
    os.makedirs(pasta_destino, exist_ok=True)

    hostname_atual = connection.find_prompt().strip("#>")
    config_atual = connection.send_command("show running-config")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{hostname_atual}_{timestamp}.txt"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)

    with open(caminho_completo, "w", encoding="utf-8") as arquivo:
        arquivo.write(config_atual)

    return caminho_completo


# ---------------------------------------------------------------------------
# Validacao da configuracao
# ---------------------------------------------------------------------------
def validar_configuracao(connection, vlans_esperadas, hostname_esperado=None):
    """Confere se VLANs e hostname aplicados batem com o esperado."""
    alertas = []

    if hostname_esperado:
        hostname_atual = connection.find_prompt().strip("#>")
        if hostname_atual != hostname_esperado:
            alertas.append(
                "Hostname esperado '" + hostname_esperado +
                "', mas encontrado '" + hostname_atual + "'."
            )

    saida_vlans = connection.send_command("show vlan-switch brief")

    for vlan in vlans_esperadas:
        vlan_id = str(vlan["id"])
        vlan_nome = vlan["nome"]

        if vlan_id not in saida_vlans:
            alertas.append("VLAN " + vlan_id + " (" + vlan_nome + ") nao encontrada no switch.")
        elif vlan_nome not in saida_vlans:
            alertas.append("VLAN " + vlan_id + " existe, mas o nome nao confere (esperado '" + vlan_nome + "').")

    resultado = {
        "ok": len(alertas) == 0,
        "alertas": alertas,
    }
    return resultado