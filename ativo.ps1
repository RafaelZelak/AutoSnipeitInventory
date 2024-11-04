function CriarArquivoAtivo {
    # Obtém o hostname do PC
    $hostname = $env:COMPUTERNAME

    # Obtém o nome de usuário de quem executou o script
    $username = $env:USERNAME

    # Define o caminho do arquivo
    $path = "\\webmin\netlogon\ServidorDeArquivos\$username\ativo.txt"

    # Verifica se o diretório existe, se não, cria o diretório
    if (-not (Test-Path -Path (Split-Path -Path $path -Parent))) {
        New-Item -Path (Split-Path -Path $path -Parent) -ItemType Directory -Force
    }

    # Cria ou sobrescreve o arquivo e escreve o conteúdo
    "$username,$hostname" | Out-File -FilePath $path -Force

    # Mensagem de confirmação
    Write-Output "Arquivo ativo.txt criado em $path com sucesso."
}

# Chama a função para execução
CriarArquivoAtivo
