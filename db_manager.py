"""
Gerenciador de banco de dados - garante persistência dos dados
"""
import os
import sys
import shutil

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
            print(f"📦 Primeira execução detectada!")
            print(f"   Extraindo banco de dados inicial...")
            
            # Caminho do banco empacotado dentro do exe
            if hasattr(sys, '_MEIPASS'):
                db_empacotado = os.path.join(sys._MEIPASS, db_name)
                
                # Se existe banco empacotado, copia
                if os.path.exists(db_empacotado):
                    shutil.copy2(db_empacotado, db_local)
                    print(f"   ✓ Banco de dados extraído com histórico!")
                else:
                    print(f"   ℹ Banco não encontrado no pacote, será criado vazio")
            else:
                print(f"   ℹ Banco será criado vazio na primeira execução")
        
        return db_local
    else:
        # Rodando normalmente (desenvolvimento)
        return db_name

def get_db_path():
    """Função principal para obter o caminho do banco"""
    return obter_caminho_db()
