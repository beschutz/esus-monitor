import sqlite3
conexao = sqlite3.connect('esus_monitoramento.db')
cursor = conexao.cursor()
cursor.execute("DROP TABLE IF EXISTS divergencias")
conexao.commit()
conexao.close()