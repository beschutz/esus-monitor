import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import time
import threading
import sys
import sqlite3
import pandas as pd
import subprocess
from db_manager import get_db_path

# =============================================================================
# INTERFACE INTEGRADA COM O SISTEMA e-SUS
# =============================================================================

class InterfacePreview:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitoramento e-SUS Automático")
        self.root.geometry("1000x700")
        
        # Variáveis de controle
        self.processo_ativo = None
        self.thread_execucao = None
        self.db_path = get_db_path()
        
        # Configuração de Estilo
        style = ttk.Style()
        try:
            style.theme_use('clam')  # Tenta usar um tema mais limpo se disponível
        except tk.TclError:
            pass # Usa o padrão se 'clam' não existir
            
        style.configure("Bold.TButton", font=('Segoe UI', 10, 'bold'))
        style.configure("Title.TLabel", font=('Segoe UI', 12, 'bold'))
        style.configure("Status.TLabel", foreground="gray")

        # --- SISTEMA DE ABAS ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Aba 1: Painel de Controle
        self.tab_run = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_run, text=" ⚙️ Painel de Controle ")
        self.setup_run_tab()

        # Aba 2: Visualizador de Dados
        self.tab_db = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_db, text=" 📊 Visualizar Banco de Dados ")
        self.setup_db_tab()

    def setup_run_tab(self):
        # Container Principal
        main_frame = ttk.Frame(self.tab_run, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Título da Seção
        ttk.Label(main_frame, text="Controle do Robô", style="Title.TLabel").pack(anchor='w', pady=(0, 15))

        # Box de Ações (Card)
        frame_controls = ttk.LabelFrame(main_frame, text="Ações de Execução", padding=15)
        frame_controls.pack(fill='x', pady=5)

        # Botões
        self.btn_iniciar = ttk.Button(frame_controls, text="▶ INICIAR PROCESSO", style="Bold.TButton", command=self.simular_inicio)
        self.btn_iniciar.pack(side='left', padx=(0, 10))

        self.btn_parar = ttk.Button(frame_controls, text="⏹ PARAR", command=self.simular_parada, state='disabled')
        self.btn_parar.pack(side='left', padx=(0, 10))

        # Status ao lado dos botões
        self.lbl_status = ttk.Label(frame_controls, text="Status: Aguardando comando", style="Status.TLabel")
        self.lbl_status.pack(side='left', padx=20)

        # Barra de Progresso
        ttk.Label(main_frame, text="Progresso da Tarefa:").pack(anchor='w', pady=(20, 5))
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=5)

        # Área de Logs
        ttk.Label(main_frame, text="Logs do Sistema (Saída em Tempo Real):").pack(anchor='w', pady=(20, 5))
        
        self.txt_log = scrolledtext.ScrolledText(main_frame, height=15, state='disabled', font=('Consolas', 9))
        self.txt_log.pack(fill='both', expand=True, pady=5)
        
        # Configuração de cores para simulação
        self.txt_log.tag_config('success', foreground='green')
        self.txt_log.tag_config('error', foreground='red')
        self.txt_log.tag_config('warning', foreground='#FF8C00')
        self.txt_log.tag_config('info', foreground='black')

        # Log inicial
        self.log("Interface carregada. Aguardando interação...", "info")

    def setup_db_tab(self):
        # Container Principal
        main_frame = ttk.Frame(self.tab_db, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Barra de Ferramentas Superior
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill='x', pady=(0, 15))

        ttk.Label(toolbar, text="Tabela:").pack(side='left', padx=(0, 5))
        
        self.combo_tabelas = ttk.Combobox(toolbar, values=["pacientes", "atendimentos", "divergencias"], state="readonly", width=20)
        self.combo_tabelas.current(0)
        self.combo_tabelas.pack(side='left', padx=5)

        ttk.Button(toolbar, text="🔄 Carregar Dados", command=self.simular_carga_dados).pack(side='left', padx=10)
        
        # Espaçador
        ttk.Frame(toolbar).pack(side='left', fill='x', expand=True)
        
        ttk.Button(toolbar, text="💾 Exportar Excel", command=self.simular_exportacao).pack(side='right')

        # Tabela (Treeview)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)

        # Scrollbars
        scroll_y = ttk.Scrollbar(tree_frame)
        scroll_y.pack(side='right', fill='y')
        scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        scroll_x.pack(side='bottom', fill='x')

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.pack(fill='both', expand=True)

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        # Configuração inicial de colunas (Exemplo)
        self.definir_colunas_exemplo()

    # --- MÉTODOS DE SIMULAÇÃO (PARA VER O COMPORTAMENTO) ---

    def log(self, message, level='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, full_msg, level)
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')

    def simular_inicio(self):
        """Inicia o processo real do esus.py em uma thread separada"""
        if self.thread_execucao and self.thread_execucao.is_alive():
            messagebox.showwarning("Aviso", "O processo já está em execução!")
            return
            
        self.btn_iniciar.config(state='disabled')
        self.btn_parar.config(state='normal')
        self.lbl_status.config(text="Status: Executando...", foreground="green")
        self.progress.start(10)
        
        self.log("=== INICIANDO PROCESSAMENTO REAL ===", "info")
        
        # Executa em thread para não travar a interface
        self.thread_execucao = threading.Thread(target=self.executar_esus, daemon=True)
        self.thread_execucao.start()

    def executar_esus(self):
        """Executa o script esus.py e captura a saída"""
        try:
            # Executa o script Python
            self.processo_ativo = subprocess.Popen(
                [sys.executable, "esus.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Lê a saída linha por linha
            for linha in self.processo_ativo.stdout:
                linha = linha.strip()
                if linha:
                    # Determina o tipo de log baseado no conteúdo
                    if "✓" in linha or "sucesso" in linha.lower():
                        nivel = "success"
                    elif "⚠" in linha or "aviso" in linha.lower():
                        nivel = "warning"
                    elif "✗" in linha or "erro" in linha.lower():
                        nivel = "error"
                    else:
                        nivel = "info"
                    
                    self.root.after(0, lambda l=linha, n=nivel: self.log(l, n))
            
            self.processo_ativo.wait()
            
            # Finaliza
            self.root.after(0, self.finalizar_execucao)
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Erro ao executar: {e}", "error"))
            self.root.after(0, self.finalizar_execucao)

    def finalizar_execucao(self):
        """Finaliza a execução e restaura os botões"""
        self.progress.stop()
        self.btn_iniciar.config(state='normal')
        self.btn_parar.config(state='disabled')
        self.lbl_status.config(text="Status: Concluído", foreground="gray")
        self.log("=== PROCESSAMENTO FINALIZADO ===", "info")
        self.processo_ativo = None

    def simular_parada(self):
        """Para o processo em execução"""
        if self.processo_ativo:
            try:
                self.processo_ativo.terminate()
                self.log("Processo interrompido pelo usuário.", "error")
            except:
                self.log("Erro ao tentar parar o processo.", "error")
        
        self.finalizar_execucao()

    def definir_colunas_exemplo(self):
        colunas = ["ID", "Nome", "CNS", "Última Atualização", "Status"]
        self.tree["columns"] = colunas
        self.tree["show"] = "headings"
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

    def simular_carga_dados(self):
        """Carrega dados reais do banco de dados"""
        tabela = self.combo_tabelas.get()
        
        # Limpa tabela
        self.tree.delete(*self.tree.get_children())
        
        try:
            conexao = sqlite3.connect(self.db_path)
            cursor = conexao.cursor()
            
            if tabela == "pacientes":
                cursor.execute("SELECT meu_id, nome, cns, cpf, us_responsavel, ultima_atualizacao FROM pacientes LIMIT 100")
                colunas = ["ID", "Nome", "CNS", "CPF", "US Responsável", "Última Atualização"]
            elif tabela == "atendimentos":
                cursor.execute("SELECT id, meu_id, nome, atendimentos, data_convertida, unidade FROM atendimentos LIMIT 100")
                colunas = ["ID", "Paciente ID", "Nome", "Tipo", "Data", "Unidade"]
            elif tabela == "divergencias":
                cursor.execute("SELECT id, cns_paciente, nome, data_atendimento, unidade_realizada, unidade_referencia, tipo_atendimento FROM divergencias LIMIT 100")
                colunas = ["ID", "CNS", "Nome", "Data", "Unidade Realizada", "Unidade Referência", "Tipo"]
            
            dados = cursor.fetchall()
            conexao.close()
            
            # Configura colunas
            self.tree["columns"] = colunas
            self.tree["show"] = "headings"
            for col in colunas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120)
            
            # Insere dados
            for item in dados:
                self.tree.insert("", "end", values=item)
            
            self.log(f"✓ {len(dados)} registros carregados da tabela '{tabela}'", "success")
            
        except sqlite3.Error as e:
            self.log(f"Erro ao carregar dados: {e}", "error")
            messagebox.showerror("Erro", f"Não foi possível carregar os dados: {e}")

    def simular_exportacao(self):
        """Exporta a tabela atual para Excel"""
        tabela = self.combo_tabelas.get()
        
        try:
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")],
                initialfile=f"{tabela}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if not arquivo:
                return
            
            conexao = sqlite3.connect(self.db_path)
            
            if tabela == "pacientes":
                df = pd.read_sql_query("SELECT * FROM pacientes", conexao)
            elif tabela == "atendimentos":
                df = pd.read_sql_query("SELECT * FROM atendimentos", conexao)
            elif tabela == "divergencias":
                df = pd.read_sql_query("SELECT * FROM divergencias", conexao)
            
            conexao.close()
            
            if arquivo.endswith('.xlsx'):
                df.to_excel(arquivo, index=False)
            else:
                df.to_csv(arquivo, index=False)
            
            self.log(f"✓ Dados exportados para: {arquivo}", "success")
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso!\n{arquivo}")
            
        except Exception as e:
            self.log(f"Erro ao exportar: {e}", "error")
            messagebox.showerror("Erro", f"Não foi possível exportar: {e}")

if __name__ == "__main__":
    try:
        # Tenta iniciar a interface gráfica
        root = tk.Tk()
        app = InterfacePreview(root)
        root.mainloop()
    except tk.TclError as e:
        # Captura o erro se não houver display (Codespaces/Nuvem)
        print("\n" + "="*60)
        print("AVISO DE AMBIENTE: NÃO É POSSÍVEL ABRIR A JANELA AQUI")
        print("="*60)
        print("O código funciona, mas o Tkinter precisa de um monitor/tela para desenhar a janela.")
        print("Ambientes de nuvem como Codespaces não possuem interface gráfica (headless).")
        print("\nO QUE FAZER:")
        print("1. Copie este código.")
        print("2. Salve como 'interface_preview.py' no seu computador (Windows/Mac/Linux).")
        print("3. Execute localmente para ver a janela.")
        print("="*60 + "\n")
        print(f"Erro técnico original: {e}")