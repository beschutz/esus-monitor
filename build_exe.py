"""
Script para gerar o executável do e-SUS Monitor
Execute: python build_exe.py
"""
import PyInstaller.__main__
import os

# Configurações do build
app_name = "eSUS-Monitor"
main_file = "interface.py"

# Arquivos adicionais necessários
# Nota: pacientes.csv NÃO é incluído - usuário deve colocar na pasta do .exe
# Nota: esus_monitoramento.db é opcional - será criado na primeira execução
arquivos_extras = [
    ('esus.py', '.'),  # Script principal
    ('cookie.py', '.'),  # Script de cookies
    ('db_manager.py', '.'),  # Gerenciador do banco
    ('banco_dados.py', '.'),  # Se tiver
]

# Monta os parâmetros --add-data
add_data_params = []
for arquivo, destino in arquivos_extras:
    if os.path.exists(arquivo):
        separador = ';' if os.name == 'nt' else ':'
        add_data_params.append(f'--add-data={arquivo}{separador}{destino}')
        print(f"  ✓ Incluindo: {arquivo}")
    else:
        print(f"  ⚠ Arquivo não encontrado (será ignorado): {arquivo}")

# Bibliotecas ocultas (imports dinâmicos)
hidden_imports = [
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome.service',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'pandas',
    'sqlite3',
    'tkinter',
    'requests',
]

# Parâmetros do PyInstaller
parametros = [
    main_file,
    '--onefile',                    # Arquivo único
    '--windowed',                   # Sem console
    f'--name={app_name}',          # Nome do exe
    '--clean',                      # Limpa cache
    '--noconfirm',                  # Sobrescreve sem perguntar
]

# Adiciona os arquivos extras
parametros.extend(add_data_params)

# Adiciona os imports ocultos
for imp in hidden_imports:
    parametros.append(f'--hidden-import={imp}')

print("="*60)
print(f"GERANDO EXECUTÁVEL: {app_name}.exe")
print("="*60)
print("\nParâmetros:")
for p in parametros:
    print(f"  {p}")
print("\n" + "="*60)

# Executa o PyInstaller
PyInstaller.__main__.run(parametros)

print("\n" + "="*60)
print("BUILD CONCLUÍDO!")
print("="*60)
print(f"\nExecutável gerado em: dist/{app_name}.exe")
print("\n⚠️  COMO FUNCIONA:")
print("1. O banco de dados está INCLUÍDO no .exe como base inicial")
print("2. Na PRIMEIRA execução, ele será extraído para a pasta do .exe")
print("3. Nas execuções seguintes, usa sempre o banco LOCAL (fora do .exe)")
print("4. Novos dados são salvos no banco LOCAL e persistem entre execuções")
print("5. Faça backup do arquivo 'esus_monitoramento.db' periodicamente!")
print("\n📦 DISTRIBUIÇÃO:")
print(f"   Basta enviar o arquivo: dist/{app_name}.exe")
print("   O banco com histórico vai junto automaticamente!")
print("="*60)
