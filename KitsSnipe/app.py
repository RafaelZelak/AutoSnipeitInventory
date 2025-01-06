import requests
import os
from config import API_TOKEN

API_URL = "http://192.168.15.206/api/v1"
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

def listar_ativos(base_path):
    """
    Lista o conteúdo dos arquivos ativo.txt em subpastas.

    Args:
        base_path (str): Caminho da pasta raiz.

    Returns:
        list: Lista de linhas com dados de usuário e asset_tag.
    """
    ativos = []

    try:
        for folder_name in os.listdir(base_path):
            folder_path = os.path.join(base_path, folder_name)

            if os.path.isdir(folder_path):
                ativo_file_path = os.path.join(folder_path, "ativo.txt")

                if os.path.isfile(ativo_file_path):
                    conteudo = ""

                    try:
                        with open(ativo_file_path, 'r', encoding='utf-8') as file:
                            conteudo = file.read().strip()
                    except UnicodeDecodeError:
                        try:
                            with open(ativo_file_path, 'r', encoding='utf-16') as file:
                                conteudo = file.read().strip()
                        except UnicodeDecodeError:
                            conteudo = ""

                    if conteudo:
                        ativos.extend(conteudo.splitlines())
    except Exception as e:
        print(f"Erro ao listar ativos: {e}")

    return ativos

def consultar_ativo(asset_tag):
    """
    Consulta a API para buscar informações de alocação de um ativo.

    Args:
        asset_tag (str): Tag do ativo.

    Returns:
        str: Nome da pessoa alocada ao ativo ou uma mensagem de erro.
    """
    url = f"{API_URL}/hardware/bytag/{asset_tag}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        if data.get("rows"):
            asset = data["rows"][0]
            assigned_to = asset.get("assigned_to")
            return assigned_to.get("name", "").strip() if assigned_to else "Ativo não está alocado."
        else:
            return "Nenhum ativo encontrado com essa marcação."

    except requests.exceptions.RequestException as e:
        return f"Erro ao consultar ativo: {str(e)}"

def processar_ativos(base_path):
    """
    Processa os ativos listados e busca as informações de alocação para cada um.

    Args:
        base_path (str): Caminho da pasta raiz.

    Returns:
        list: Resultados combinados (usuário, ativo e alocação).
    """
    resultados = []
    ativos = listar_ativos(base_path)

    for linha in ativos:
        try:
            usuario, asset_tag = linha.split(",")
            alocacao = consultar_ativo(asset_tag)

            if alocacao.startswith("(Kit #"):
                resultados.append(f"{alocacao} - {usuario}")
        except ValueError:
            print(f"Erro ao processar linha: {linha}")

    return resultados

# Exemplo de uso
base_path = r"\\webmin\netlogon\ServidorDeArquivos"
resultados = processar_ativos(base_path)

# Imprime os resultados
for resultado in resultados:
    print(resultado)