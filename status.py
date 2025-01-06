import requests
from config import API_TOKEN
import os

API_URL = "http://192.168.15.206/api/v1"

headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Função para obter ativos pelo ID do status
def listar_ativos_por_status_id(status_id, status_nome):
    url = f"{API_URL}/hardware?status_id={status_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        ativos = data.get('rows', [])

        if ativos:
            print(f"Ativos com status '{status_nome}':")
            for ativo in ativos:
                asset_tag = ativo.get('asset_tag', 'N/A')
                assigned_to = ativo.get('assigned_to', {})
                allocated_to = assigned_to.get('name', 'Não alocado')

                print(
                    f"ID: {ativo['id']} | "
                    f"Marcação: {asset_tag} | "
                    f"Alocado Para: {allocated_to}"
                )
        else:
            print(f"Nenhum ativo encontrado com status '{status_nome}'.")
    else:
        print(f"Erro ao buscar ativos: {response.status_code}, {response.text}")


def listar_ativos_em_pastas_otimizado(diretorio_raiz):
    print("\n______________________________________")
    print("\nAtivos com users:")

    for pasta in os.listdir(diretorio_raiz):
        caminho_pasta = os.path.join(diretorio_raiz, pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "ativo.txt")

        if os.path.isdir(caminho_pasta) and os.path.isfile(caminho_arquivo):
            conteudo = ""
            try:
                # Força leitura em UTF-16 para evitar os caracteres "ÿþ"
                with open(caminho_arquivo, "r", encoding="utf-16") as file:
                    conteudo = file.read().strip()
            except UnicodeError:
                print(f"Erro ao ler {caminho_arquivo}, encoding não suportado.")

            if conteudo:
                print(f"Pasta: {caminho_pasta}")
                print(f"Conteúdo do ativo.txt:\n{conteudo}\n")

def buscar_ativos_em_kits_com_erros(diretorio_raiz, status_id, status_nome):
    # 1. Obter os ativos na pasta ativo.txt
    usuarios_ativos = {}
    duplicados = {}

    for pasta in os.listdir(diretorio_raiz):
        caminho_pasta = os.path.join(diretorio_raiz, pasta)
        caminho_arquivo = os.path.join(caminho_pasta, "ativo.txt")

        if os.path.isdir(caminho_pasta) and os.path.isfile(caminho_arquivo):
            try:
                with open(caminho_arquivo, "r", encoding="utf-16") as file:
                    conteudo = file.read().strip()
                    # Dividir o conteúdo no formato "usuario,marcacao"
                    if conteudo:
                        usuario, marcacao = conteudo.split(",")
                        marcacao = marcacao.strip()
                        usuario = usuario.strip()

                        # Detectar duplicidades
                        if marcacao in usuarios_ativos:
                            if marcacao not in duplicados:
                                duplicados[marcacao] = [usuarios_ativos[marcacao]]
                            duplicados[marcacao].append(usuario)
                        else:
                            usuarios_ativos[marcacao] = usuario
            except Exception as e:
                print(f"Erro ao processar {caminho_arquivo}: {e}")

    # 2. Buscar os ativos do status especificado
    url = f"{API_URL}/hardware?status_id={status_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Erro ao buscar ativos da API: {response.status_code}, {response.text}")
        return

    ativos_api = response.json().get('rows', [])

    # 3. Bater as informações e exibir os resultados
    print(f"\nResultados cruzados para ativos no kit '{status_nome}':")
    encontrado = False
    for ativo in ativos_api:
        asset_tag = ativo.get('asset_tag', '').strip()
        allocated_to = ativo.get('assigned_to', {}).get('name', '').strip()

        # Procurar a marcação no dicionário de ativos da pasta
        if asset_tag in usuarios_ativos:
            encontrado = True
            usuario = usuarios_ativos[asset_tag]
            print(f"Kit: {allocated_to} -> Usuário: {usuario}")

    if not encontrado:
        print("Nenhum ativo encontrado correspondente entre os kits e os arquivos ativo.txt.")

    # 4. Exibir os erros (duplicidades)
    if duplicados:
        print("\nErros detectados: Uma mesma marcação está associada a múltiplos usuários.")
        for marcacao, usuarios in duplicados.items():
            print(f"Marcação: {marcacao} está associada aos usuários: {', '.join(usuarios)}")
    else:
        print("\nNenhum erro de duplicidade encontrado.")

# Exemplo de uso
diretorio_raiz = r"\\webmin\netlogon\ServidorDeArquivos"
status_id = 8
status_nome = "Em Uso (Kit)"
buscar_ativos_em_kits_com_erros(diretorio_raiz, status_id, status_nome)

