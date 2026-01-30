# eSUS Monitor

Sistema de monitoramento de divergências em atendimentos do e-SUS.

## Requisitos

- Python 3.12+
- Google Chrome instalado
- Arquivo `pacientes.csv` com dados dos pacientes (CNS/CPF)

## Instalação (Desenvolvimento)

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar interface gráfica
python interface.py
```

## Uso do Executável (.exe)

1. Baixe o arquivo `eSUS-Monitor.exe` dos releases
2. **IMPORTANTE**: Coloque o arquivo `pacientes.csv` na mesma pasta do .exe
3. Execute `eSUS-Monitor.exe`
4. O banco de dados será criado automaticamente no primeiro uso

## Formato do CSV

O arquivo `pacientes.csv` deve conter as colunas:
- CNS: Cartão Nacional de Saúde
- CPF: Cadastro de Pessoas Físicas

## Build do Executável

O executável é gerado automaticamente via GitHub Actions quando há push para o repositório.

Para build local (Windows):
```bash
python build_exe.py
```

## Estrutura do Projeto

- `interface.py` - Interface gráfica principal
- `esus.py` - Processamento de dados e API do e-SUS
- `cookie.py` - Automação de login via Selenium
- `db_manager.py` - Gerenciamento do banco de dados
- `banco_dados.py` - Esquema do banco de dados

## Funcionalidades

- Login automático no e-SUS via Selenium
- Processamento de lista de pacientes
- Detecção de divergências (atendimentos em unidades diferentes da referência)
- Exportação de relatórios em Excel/CSV
- Interface gráfica com logs em tempo real
