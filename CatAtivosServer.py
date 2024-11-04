import os
import csv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

base_path = r'\\webmin\netlogon\ServidorDeArquivos'

output_file = 'ativosCatch.csv'

data = []

logging.info("Iniciando a verificação nas pastas diretas dentro de %s", base_path)

for dir_name in os.listdir(base_path):
    dir_path = os.path.join(base_path, dir_name)

    if os.path.isdir(dir_path):
        logging.info("Verificando a pasta: %s", dir_path)

        file_path = os.path.join(dir_path, 'ativo.txt')

        if os.path.exists(file_path):
            try:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='utf-16') as file:
                        content = file.read().strip()

                logging.info("Arquivo encontrado e lido com sucesso: %s", file_path)

                username, ativo = content.split(',')
                data.append([username, ativo])
            except Exception as e:
                logging.error("Erro ao ler o arquivo %s: %s", file_path, e)
        else:
            logging.info("Arquivo 'ativo.txt' não encontrado em %s", dir_path)

try:
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['username', 'ativo'])  # Cabeçalho no CSV
        csv_writer.writerows(data)
    logging.info("Dados extraídos e salvos com sucesso em %s", output_file)
except Exception as e:
    logging.error("Erro ao salvar o arquivo CSV %s: %s", output_file, e)
