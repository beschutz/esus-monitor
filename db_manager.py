"""
Gerenciador de banco de dados - garante persistencia dos dados
"""
import os
import sys
import shutil
import io

# Forca UTF-8 no stdout para Windows (apenas se stdout existir)
if sys.platform == 'win32' and sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def obter_caminho_db():
    """
    Retorna o caminho correto do banco de dados.
    Se rodando do .exe, usa a pasta do executável.
    Se rodando normal, usa a pasta atual.
    """
    # Caminho do banco de dados
    db_name = "esus_monitoramento.db"
    
    # Se rodando de um executável PyInstaller
    if getattr(sys, 'frozen', False):
        # Pasta onde o .exe está
        pasta_exe = os.path.dirname(sys.executable)
        db_local = os.path.join(pasta_exe, db_name)
        
        # Verifica se já existe o banco na pasta do exe
        if not os.path.exists(db_local):
            print(f"[INFO] Primeira execucao detectada!")
            print(f"   Extraindo banco de dados inicial...")
            
            # Caminho do banco empacotado dentro do exe
            if hasattr(sys, '_MEIPASS'):
                db_empacotado = os.path.join(sys._MEIPASS, db_name)
                
                # Se existe banco empacotado, copia
                if os.path.exists(db_empacotado):
                    shutil.copy2(db_empacotado, db_local)
                    print(f"   [OK] Banco de dados extraido com historico!")
                else:
                    print(f"   [INFO] Banco nao encontrado no pacote, sera criado vazio")
            else:
                print(f"   [INFO] Banco sera criado vazio na primeira execucao")
        
        return db_local
    else:
        # Rodando normalmente (desenvolvimento)
        return db_name

def get_db_path():
    """Função principal para obter o caminho do banco"""
    return obter_caminho_db()
