import csv

# Função para processar o arquivo CSV
def process_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    output_lines = []
    current_name = ""

    for line in lines:
        line = line.strip()
        if not line:  # Ignorar linhas vazias
            continue

        if not line.startswith("0"):  # Linha com nome ou "Vago"
            current_name = line if line else ""
        else:  # Linha com valor começando com "0"
            if current_name == "":
                current_name = "Vago"
            output_lines.append(f"{current_name},ST{line}")

    # Escrever a saída em um novo arquivo
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("\n".join(output_lines))

# Exemplo de uso
input_file = './OrganizaCsv/entrada.csv'  # Substitua pelo caminho do arquivo de entrada
output_file = './OrganizaCsv/saida.csv'  # Substitua pelo caminho do arquivo de saída
process_csv(input_file, output_file)

print(f"Arquivo processado e salvo em: {output_file}")
