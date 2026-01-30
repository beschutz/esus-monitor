"""
Script para gerar o executavel do e-SUS Monitor
Execute: python build_exe.py
"""
import PyInstaller.__main__
import os
import sys

# Força UTF-8 no stdout para evitar erros de encoding no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuracoes do build
app_name = "eSUS-Monitor"
main_file = "interface.py"

# Arquivos adicionais necessarios
# Nota: pacientes.csv NAO e incluido - usuario deve colocar na pasta do .exe
# Nota: esus_monitoramento.db e opcional - sera criado na primeira execucao
arquivos_extras = [
    ('esus.py', '.'),  # Script principal
    ('cookie.py', '.'),  # Script de cookies
    ('db_manager.py', '.'),  # Gerenciador do banco
    ('banco_dados.py', '.'),  # Se tiver
]

# Monta os parametros --add-data
add_data_params = []
for arquivo, destino in arquivos_extras:
    if os.path.exists(arquivo):
        separador = ';' if os.name == 'nt' else ':'
        add_data_params.append(f'--add-data={arquivo}{separador}{destino}')
        print(f"  [OK] Incluindo: {arquivo}")
    else:
        print(f"  [AVISO] Arquivo nao encontrado (sera ignorado): {arquivo}")

# Bibliotecas ocultas (imports dinamicos)
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

# Parametros do PyInstaller
parametros = [
    main_file,
    '--onefile',                    # Arquivo unico
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
print(f"GERANDO EXECUTAVEL: {app_name}.exe")
print("="*60)
print("\nParametros:")
for p in parametros:
    print(f"  {p}")
print("\n" + "="*60)

# Executa o PyInstaller
PyInstaller.__main__.run(parametros)

print("\n" + "="*60)
print("BUILD CONCLUIDO!")
print("="*60)
print(f"\nExecutavel gerado em: dist/{app_name}.exe")
print("\n[AVISO] COMO FUNCIONA:")
print("1. O banco de dados esta INCLUIDO no .exe como base inicial")
print("2. Na PRIMEIRA execucao, ele sera extraido para a pasta do .exe")
print("3. Nas execucoes seguintes, usa sempre o banco LOCAL (fora do .exe)")
print("4. Novos dados sao salvos no banco LOCAL e persistem entre execucoes")
print("5. Faca backup do arquivo 'esus_monitoramento.db' periodicamente!")
print("\n[INFO] DISTRIBUICAO:")
print(f"   Basta enviar o arquivo: dist/{app_name}.exe")
print("   O banco com historico vai junto automaticamente!")
print("="*60)
