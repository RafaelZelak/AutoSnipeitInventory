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
    Lista os ativos do arquivo ativo.txt em subpastas, lidando com diferentes codificações.

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
                    conteudo = None
                    for encoding in ['utf-8', 'utf-16', 'latin-1']:  # Tenta várias codificações
                        try:
                            with open(ativo_file_path, 'r', encoding=encoding) as file:
                                conteudo = file.read().strip()
                                break  # Sai do loop se a leitura for bem-sucedida
                        except UnicodeDecodeError:
                            continue

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
        dict: Informações do ativo.
    """
    url = f"{API_URL}/hardware/bytag/{asset_tag}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar ativo: {str(e)}")
        return {}

def consultar_usuario_do_ativo(ativo_id):
    """
    Consulta a API para buscar informações de alocação do ativo que representa o Kit.

    Args:
        ativo_id (int): ID do ativo (Kit).

    Returns:
        str: Nome do usuário associado ao ativo.
    """
    url = f"{API_URL}/hardware/{ativo_id}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Verifica se o campo "assigned_to" existe
        assigned_to = data.get("assigned_to")
        if assigned_to:
            return assigned_to.get("username", "Não alocado").strip()
        else:
            return "Kit não alocado."
    except requests.exceptions.RequestException as e:
        return f"Erro ao consultar ativo: {str(e)}"

def remover_usuario_do_kit(kit_id):
    """
    Remove o usuário associado a um Kit.

    Args:
        kit_id (int): ID do Kit.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    url = f"{API_URL}/hardware/{kit_id}"

    try:
        data = {
            "assigned_user": None,  # Remove a associação do usuário
        }
        response = requests.patch(url, headers=HEADERS, json=data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao remover usuário do Kit: {str(e)}")
        return False


def comparar_usuarios(usuario_snipeit, usuario_ldap, kit_id):
    """
    Compara os usuários do SnipeIT e do LDAP e, se forem diferentes, remove o usuário do Kit.

    Args:
        usuario_snipeit (str): Usuário obtido do SnipeIT.
        usuario_ldap (str): Usuário obtido do LDAP.
        kit_id (int): ID do Kit.

    Returns:
        bool: True se os usuários forem iguais, False caso contrário.
    """
    if usuario_snipeit != usuario_ldap:
        print(f"Usuários diferentes: {usuario_snipeit} e {usuario_ldap}. Removendo usuário do Kit {kit_id}.")
        sucesso = remover_usuario_do_kit(kit_id)
        if sucesso:
            print(f"Usuário {usuario_snipeit} removido do Kit {kit_id}.")
        else:
            print(f"Falha ao remover o usuário do Kit {kit_id}.")
        return False
    return True


def processar_ativos_filtrados(base_path):
    """
    Processa os ativos vinculados a kits e busca os usuários associados aos kits.

    Args:
        base_path (str): Caminho da pasta raiz.

    Returns:
        list: Resultados contendo o ativo, o kit, os usuários associados ao kit e ao LDAP e a comparação dos usuários.
    """
    resultados = []
    ativos = listar_ativos(base_path)

    for linha in ativos:
        try:
            usuario_ldap, asset_tag = linha.split(",")
            ativo_info = consultar_ativo(asset_tag)

            if ativo_info.get("rows"):
                asset = ativo_info["rows"][0]
                assigned_to = asset.get("assigned_to")

                # Verifica se o ativo está vinculado a um Kit
                if assigned_to and "Kit #" in assigned_to.get("name", ""):
                    kit_id = assigned_to.get("id")
                    kit_nome = assigned_to.get("name")

                    # Consulta o usuário associado ao Kit
                    kit_usuario = consultar_usuario_do_ativo(kit_id)

                    # Compara os usuários e verifica diferenças
                    usuarios_iguais = comparar_usuarios(kit_usuario, usuario_ldap, kit_id)

                    # Registra os resultados
                    resultados.append(
                        f"Ativo: {asset_tag} - Kit: {kit_nome} - Usuário SnipeIT: {kit_usuario} - Usuário LDAP: {usuario_ldap} - {usuarios_iguais}"
                    )
        except ValueError:
            print(f"Erro ao processar linha: {linha}")
        except Exception as e:
            print(f"Erro inesperado: {e}")

    return resultados

# Exemplo de uso
base_path = r"\\webmin\netlogon\ServidorDeArquivos"
resultados_filtrados = processar_ativos_filtrados(base_path)

# Imprime os resultados filtrados
for resultado in resultados_filtrados:
    print(resultado)
