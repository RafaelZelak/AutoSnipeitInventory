import requests
import csv
import time
from config import API_TOKEN #<- Arquivo config.py que tem apenas a variavel com o token do SnipeIT: API_TOKEN='token'

API_URL = "http://192.168.15.206/api/v1"
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

MAX_REQUESTS_PER_MINUTE = 60
REQUEST_DELAY = 60 / MAX_REQUESTS_PER_MINUTE

MAX_RETRIES = 5
RETRY_DELAY = 3

STATUS_LABELS = {
    6: "Descartado",
    5: "Defeito",
    4: "Em Uso",
    1: "Pendente",
    3: "Estoque"
}
def rate_limit():
    time.sleep(REQUEST_DELAY)

def obter_tag_ativo(asset_id):
    url = f"{API_URL}/hardware/{asset_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get('asset_tag', 'Tag desconhecida')
    return None

def obter_id_usuario(username, retry_count=0):
    rate_limit()
    url = f"{API_URL}/users?search={username}"
    response = requests.get(url, headers=headers)

    if response.status_code == 429:
        if retry_count < MAX_RETRIES:
            delay = RETRY_DELAY * (2 ** retry_count)
            print(f"Aguardando {delay} segundos antes de tentar novamente para {username}...")
            time.sleep(delay)
            return obter_id_usuario(username, retry_count + 1)
        else:
            print(f"Erro: Não foi possível obter o ID de {username} após {MAX_RETRIES} tentativas.")
            return None
    elif response.status_code == 200:
        data = response.json()
        if data['total'] > 0:
            return data['rows'][0]['id']
    else:
        print(f"Erro ao obter o ID de {username}: {response.status_code}, {response.text}")
    return None

def obter_status_id(status_name):
    for status_id, status in STATUS_LABELS.items():
        if status_name.lower() in status.lower():
            return status_id
    return None

def obter_id_ativo(asset_tag):
    asset_tag = asset_tag.strip().upper()
    url = f"{API_URL}/hardware?search={asset_tag}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data['total'] > 0:
            for item in data['rows']:
                if item['asset_tag'] == asset_tag:
                    return item['id']
        else:
            print(f"Nenhum ativo encontrado para a tag {asset_tag}")
    else:
        print(f"Erro ao consultar ativo {asset_tag}: {response.status_code}, {response.text}")
    return None

# Função para verificar quem está usando o ativo
def verificar_usuario_ativo(asset_id):
    url = f"{API_URL}/hardware/{asset_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        assigned_user = data.get('assigned_to', None)  # Pode ser None
        asset_tag = data.get('asset_tag', 'Tag desconhecida')  # Obtém a tag do ativo

        # Acessa o campo correto para status
        status_info = data.get('status_label', {})  # Pega a chave status_label
        status_id = status_info.get('id', None)  # Obtém o ID do status
        status = STATUS_LABELS.get(status_id, status_info.get('name', "Desconhecido"))  # Verifica o nome

        if assigned_user:
            # Verifica se o campo 'username' existe no assigned_user
            if 'username' in assigned_user:
                print(f"Ativo {asset_tag} está com {assigned_user['username']}, Status: {status}")
                return assigned_user, status
            else:
                # Loga o erro e retorna o ativo com o problema
                print(f"Erro: 'username' não encontrado no assigned_user para o ativo {asset_tag}. Dados retornados: {assigned_user}")
                return None, status
        else:
            print(f"Ativo {asset_tag} não está atribuído a ninguém. Status: {status}")
            return None, status
    else:
        print(f"Erro ao verificar o ativo {asset_id}: {response.status_code}, {response.text}")
        return None, None


def checkin_ativo(asset_id):
    url = f"{API_URL}/hardware/{asset_id}/checkin"
    payload = {'status_id': 3}  # Status 'Estoque'
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return True
    else:
        print(f"Erro ao fazer check-in: {response.status_code}, {response.text}")
        return False

def checkout_ativo(user_id, asset_id):
    status_id = obter_status_id("Em Uso")

    if not status_id:
        print("Erro: Status 'Em Uso' não encontrado.")
        return False

    url = f"{API_URL}/hardware/{asset_id}/checkout"
    payload = {
        'assigned_user': user_id,
        'checkout_to_type': 'user',
        'status_id': status_id
    }
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"Ativo {asset_id} foi atribuído com sucesso.")
        return True
    else:
        print(f"Erro ao fazer checkout: {response.status_code}, {response.text}")
        return False

def processar_ativos_para_usuario(username, ativos):
    if username.lower() == "vago":
        for ativo in ativos:
            asset_id = obter_id_ativo(ativo)
            if asset_id:
                current_user, current_status = verificar_usuario_ativo(asset_id)

                # Remove qualquer entidade atribuída e coloca o ativo no estoque
                if current_user or current_status != "Estoque":
                    if checkin_ativo(asset_id):
                        asset_tag = obter_tag_ativo(asset_id)
                        print(f"Ativo {asset_tag} foi movido para o estoque.")
                else:
                    asset_tag = obter_tag_ativo(asset_id)
                    print(f"Ativo {asset_tag} já estava no status Estoque.")
    else:
        user_id = obter_id_usuario(username)
        if user_id:
            for ativo in ativos:
                asset_id = obter_id_ativo(ativo)
                if asset_id:
                    current_user, current_status = verificar_usuario_ativo(asset_id)
                    if current_user:
                        if current_user.get('id') != user_id:
                            if checkin_ativo(asset_id):
                                asset_tag = obter_tag_ativo(asset_id)
                                print(f"Ativo {asset_tag} que estava com {current_user['username']} foi passado para {username}.")
                                if checkout_ativo(user_id, asset_id):
                                    print(f"Ativo {asset_tag} atribuído a {username}.")
                    else:
                        if checkout_ativo(user_id, asset_id):
                            asset_tag = obter_tag_ativo(asset_id)
                            print(f"Ativo {asset_tag} que estava no estoque foi atribuído a {username}.")
        else:
            print(f"Usuário {username} não encontrado.")

def verificar_disponibilidade_ativo(asset_id):
    url = f"{API_URL}/hardware/{asset_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['assigned_to'] is None
    return False

def ler_arquivo_csv(caminho_csv):
    usuarios = {}
    with open(caminho_csv, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            username, ativo = row
            if username in usuarios:
                usuarios[username].append(ativo)
            else:
                usuarios[username] = [ativo]
    return usuarios

def main():
    caminho_csv = "./history/ativos30-12-2024.csv"
    usuarios_ativos = ler_arquivo_csv(caminho_csv)
    for user, ativos in usuarios_ativos.items():
        processar_ativos_para_usuario(user, ativos)

main()
