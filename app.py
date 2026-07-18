"""
app.py
Frontend web (Flask) para o Desafio de Automacao.

Permite ao usuario:
- Ver/editar as VLANs a serem configuradas (ID + Nome)
- Definir o hostname desejado
- Clicar em um botao para aplicar tudo no switch
- Ver o resultado: configuracao aplicada, backup gerado, e alertas de validacao
"""

from flask import Flask, render_template, request

from switch_automation import (
    conectar_switch,
    configurar_vlans,
    salvar_configuracao,
    fazer_backup,
    validar_configuracao,
    VLANS_PADRAO,
    HOSTNAME_DESEJADO,
)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    """Mostra o formulario, ja preenchido com as VLANs padrao do desafio."""
    return render_template(
        "index.html",
        vlans=VLANS_PADRAO,
        hostname=HOSTNAME_DESEJADO,
        resultado=None,
    )


@app.route("/configurar", methods=["POST"])
def configurar():
    """
    Recebe os dados do formulario, conecta no switch, aplica a
    configuracao, salva, faz backup e valida tudo em seguida.
    """
    # --- 1. Ler os dados enviados pelo formulario ---
    hostname = request.form.get("hostname", "").strip()

    vlans = []
    # O formulario manda listas paralelas: vlan_id[] e vlan_nome[]
    ids = request.form.getlist("vlan_id")
    nomes = request.form.getlist("vlan_nome")
    for vlan_id, vlan_nome in zip(ids, nomes):
        if vlan_id.strip() and vlan_nome.strip():
            vlans.append({"id": int(vlan_id), "nome": vlan_nome.strip()})

    resultado = {
        "sucesso": False,
        "mensagem": "",
        "backup_path": None,
        "validacao": None,
    }

    try:
        # --- 2. Conectar e aplicar configuracao ---
        connection = conectar_switch()
        configurar_vlans(connection, vlans, hostname=hostname)

        # --- 3. Salvar configuracao na NVRAM ---
        salvar_configuracao(connection)

        # --- 4. Fazer backup ---
        caminho_backup = fazer_backup(connection)

        # --- 5. Validar se ficou tudo certo ---
        validacao = validar_configuracao(
            connection, vlans_esperadas=vlans, hostname_esperado=hostname
        )

        connection.disconnect()

        resultado["sucesso"] = True
        resultado["mensagem"] = "Configuracao aplicada com sucesso!"
        resultado["backup_path"] = caminho_backup
        resultado["validacao"] = validacao

    except Exception as erro:
        # Se algo der errado (ex: switch offline, senha incorreta),
        # mostramos o erro no frontend em vez de travar o programa.
        resultado["sucesso"] = False
        resultado["mensagem"] = f"Erro ao configurar o switch: {erro}"

    return render_template(
        "index.html",
        vlans=vlans if vlans else VLANS_PADRAO,
        hostname=hostname or HOSTNAME_DESEJADO,
        resultado=resultado,
    )


if __name__ == "__main__":
    app.run(debug=True)