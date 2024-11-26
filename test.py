from ldap3 import Server, Connection, ALL

# Configurações do servidor e credenciais
ad_server = 'digitalup.intranet'
ad_user = 'administrator'
ad_password = '&ajhsRlm88s!@SF'

# Inicializa a conexão com o servidor AD
server = Server(ad_server, get_info=ALL)
conn = Connection(server, user=f'{ad_user}@{ad_server}', password=ad_password, auto_bind=True)

# Pesquisa no diretório para pegar todos os objetos do tipo usuário
conn.search(search_base='DC=digitalup,DC=intranet',
            search_filter='(objectClass=user)',
            attributes=['sAMAccountName'])

# Extrai usernames que não terminam com $
usernames = [entry.sAMAccountName.value for entry in conn.entries
             if entry.sAMAccountName.value and not entry.sAMAccountName.value.endswith('$')]

# Exibe os usernames
print("Usernames encontrados no AD (somente usuários):")
for username in usernames:
    print(username)

# Fecha a conexão
conn.unbind()
