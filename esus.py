import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import sqlite3
import pandas as pd
from cookie import obter_cookies
import time
from db_manager import get_db_path

API_TIMEOUT = 30
TIMEZONE_BR = ZoneInfo("America/Sao_Paulo")

# Obtém o caminho correto do banco de dados
DB_PATH = get_db_path()


def api_post(url, payload, headers, descricao):
    try:
        resposta_local = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        print(f"⚠ Erro de rede ao {descricao}: {exc}")
        return None

    if resposta_local.status_code != 200:
        print(f"⚠ Erro HTTP {resposta_local.status_code} ao {descricao}.")
        return None

    return resposta_local

tabela = pd.read_csv('pacientes.csv', dtype=str)

conexao = sqlite3.connect(DB_PATH)
cursor = conexao.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS pacientes (
    meu_id TEXT PRIMARY KEY,
    nome TEXT,
    cns TEXT,
    cpf TEXT,
    us_responsavel TEXT,
    ultima_atualizacao TEXT
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS atendimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meu_id TEXT,
    nome TEXT,
    atendimentos TEXT,
    data_convertida TEXT,
    unidade TEXT,
    FOREIGN KEY (meu_id) REFERENCES pacientes(meu_id)
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS divergencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cns_paciente TEXT,
    nome TEXT,
    data_atendimento TEXT,
    unidade_realizada TEXT,
    unidade_referencia TEXT,
    tipo_atendimento TEXT
)''')
conexao.commit()

# ============================================================
# CONFIGURAÇÃO MANUAL DE COOKIES (para testes)
# ============================================================
# Descomente as linhas abaixo para usar cookies manuais:
# cookies_string = "JSESSIONID=seu_jsessionid_aqui; XSRF-TOKEN=seu_token_aqui"
# token_csrf = "seu_token_csrf_aqui"
# USE_MANUAL = True

USE_MANUAL = False  # Mude para True para usar cookies manuais

if not USE_MANUAL:
    print("Obtendo cookies de autenticação automaticamente...")
    cookies_string, token_csrf = obter_cookies()
    print(f"Cookies obtidos: {cookies_string}")
else:
    print("Usando cookies manuais configurados no código")

# Verificar quais pacientes já foram processados
print("\n" + "="*60)
print("INICIANDO PROCESSAMENTO - Priorizando não processados")
print("="*60)

pacientes_processados = {}
for i in tabela.index:
    meu_cns_temp = str(tabela.loc[i, 'CNS']) if pd.notna(tabela.loc[i, 'CNS']) else ''
    meu_cpf_temp = str(tabela.loc[i, 'CPF']) if pd.notna(tabela.loc[i, 'CPF']) else ''
    meu_id_temp = meu_cpf_temp if len(meu_cns_temp) != 15 else meu_cns_temp
    
    cursor.execute('SELECT ultima_atualizacao FROM pacientes WHERE meu_id = ?', (meu_id_temp,))
    resultado = cursor.fetchone()
    if resultado and resultado[0]:
        pacientes_processados[i] = resultado[0]

nao_processados = [i for i in tabela.index if i not in pacientes_processados]
processados = sorted(pacientes_processados.keys(), key=lambda x: pacientes_processados[x])
indices_ordenados = nao_processados + processados

print(f"\nℹ Total de pacientes: {len(tabela)}")
print(f"  • Não processados: {len(nao_processados)}")
print(f"  • Já processados: {len(processados)}")
print(f"\nProcessando na ordem: não processados primeiro, depois os mais antigos\n")

for idx, i in enumerate(indices_ordenados, 1):
    meu_cns = str(tabela.loc[i, 'CNS']) if pd.notna(tabela.loc[i, 'CNS']) else ''
    meu_cpf = str(tabela.loc[i, 'CPF']) if pd.notna(tabela.loc[i, 'CPF']) else ''
    
    status = "[NÃO PROCESSADO]" if i in nao_processados else f"[ÚLTIMA ATUALIZAÇÃO: {pacientes_processados[i]}]"
    print(f"\n{'='*60}")
    print(f"Paciente {idx}/{len(tabela)} {status}")
    print(f"CNS: {meu_cns} / CPF: {meu_cpf}")
    print(f"{'='*60}")
    
    if (not meu_cns or meu_cns.strip() == '') and (not meu_cpf or meu_cpf.strip() == ''):
        print("✗ CNS e CPF ausentes, pulando paciente.")
        continue
    
    if len(meu_cns) != 15:
        meu_id = meu_cpf
        print(f"CNS inválido, usando CPF como ID: {meu_id}")
    else:
        meu_id = meu_cns
        print(f"CNS válido, usando como ID: {meu_id}")

    consulta_graphql = """
    query CidadaoListing($filtro: CidadaosQueryInput!) {\n  cidadaos(input: $filtro) {\n    content {\n      id\n      nome\n      nomeSocial\n      cpf\n      cns\n      nomeMae\n      dataNascimento\n      telefoneCelular\n      telefoneResidencial\n      sexo\n      identidadeGeneroDbEnum\n      dataAtualizado\n      ativo\n      unificado\n      unificacaoBase\n      prontuario {\n        id\n        __typename\n      }\n      possuiAgendamento\n      localidadeNascimento {\n        id\n        nome\n        uf {\n          id\n          nome\n          sigla\n          __typename\n        }\n        __typename\n      }\n      faleceu\n      cidadaoVinculacaoEquipe {\n        id\n        unidadeSaude {\n          id\n          nome\n          __typename\n        }\n        __typename\n      }\n      enderecoIndigena {\n        aldeiaResidencia {\n          id\n          nome\n          __typename\n        }\n        poloBaseResidencia {\n          id\n          nome\n          __typename\n        }\n        dseiResidencia {\n          id\n          nome\n          __typename\n        }\n        __typename\n      }\n      cidadaoAldeado {\n        id\n        nomeTradicional\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n
    """
    meu_envelope = {
        "query": consulta_graphql,
        "variables": {
            "filtro": {
                "query": meu_id,
                "pageParams":{
                    "size": 1,
                }
            }
        }

    }
    meus_headers = {
        "Content-Type": "application/json",
        "Cookie": cookies_string,
        "X-XSRF-TOKEN": token_csrf
    }
    print("Buscando dados do paciente na API...")
    resposta = api_post("https://esus.procempa.com.br/api/graphql", meu_envelope, meus_headers, "consultar a API")
    if resposta is None:
        print("⚠ Falha na consulta inicial, pulando paciente...")
        continue

    dados = resposta.json()
    if not dados:
        print("⚠ Resposta vazia da API, pulando paciente...")
        continue

    if dados.get('errors'):
        primeira = dados['errors'][0]
        msg = primeira.get('message', 'Erro desconhecido')
        print(f"⚠ Erro retornado pela API: {msg}")
        continue

    if not dados.get('data') or not dados['data'].get('cidadaos'):
        print("⚠ Estrutura inesperada da resposta da API, pulando paciente...")
        continue

    content = dados['data']['cidadaos'].get('content') or []
    if not content:
        print("⚠ Paciente não encontrado na API, pulando...")
        continue

    id_paciente = content[0].get('id')
    if not id_paciente:
        print("⚠ ID do paciente ausente na resposta, pulando...")
        continue

    print(f"✓ Paciente encontrado - ID: {id_paciente}")

    consulta_detalhes = """
        query BuscaDetailCidadao($id: ID!) {\n cidadao(id: $id) {\n id\n cpf\n cns\n nisPisPasep\n nome\n nomeSocial\n dataNascimento\n dataAtualizado\n dataObito\n numeroDocumentoObito\n sexo\n nomeMae\n nomePai\n telefoneResidencial\n telefoneCelular\n telefoneContato\n email\n area\n microArea\n endereco {\n cep\n uf {\n id\n nome\n __typename\n }\n municipio {\n id\n nome\n __typename\n }\n bairro\n tipoLogradouro {\n id\n nome\n __typename\n }\n logradouro\n numero\n semNumero\n complemento\n pontoReferencia\n __typename\n }\n localidadeExterior\n prontuario {\n id\n __typename\n }\n identidadeGeneroDbEnum\n etnia {\n id\n nome\n __typename\n }\n racaCor {\n id\n nome\n racaCorDbEnum\n __typename\n }\n area\n microArea\n cbo {\n id\n nome\n __typename\n }\n escolaridade {\n id\n nome\n __typename\n }\n ativo\n localidadeNascimento {\n id\n nome\n uf {\n id\n sigla\n __typename\n }\n __typename\n }\n faleceu\n possuiAgendamento\n prontuario {\n id\n gestacoes {\n id\n inicio\n fim\n __typename\n }\n preNatalAtivo {\n id\n altoRisco\n tipoGravidez {\n id\n descricao\n __typename\n }\n gravidezPlanejada\n ultimaDum\n __typename\n }\n puerpera\n __typename\n }\n unificado\n unificacaoBase\n cidadaoVinculacaoEquipe {\n id\n tpCdsOrigem\n utilizarCadastroIndividual\n unidadeSaude {\n id\n nome\n __typename\n }\n equipe {\n id\n nome\n ine\n __typename\n }\n __typename\n }\n tipoSanguineo\n orientacaoSexualDbEnum\n estadoCivil {\n id\n nome\n __typename\n }\n paisExterior {\n id\n nome\n __typename\n }\n localidadeExterior\n nacionalidade {\n id\n nacionalidadeDbEnum\n __typename\n }\n portariaNaturalizacao\n dataNaturalizacao\n paisNascimento {\n id\n nome\n __typename\n }\n dataEntradaBrasil\n stCompartilhaProntuario\n periodoAusenciaList {\n id\n dtAusencia\n dtRetorno\n __typename\n }\n cidadaoAldeado {\n id\n aldeiaNascimento {\n id\n nome\n __typename\n }\n funcaoSocial {\n id\n nome\n __typename\n }\n localOcorrencia {\n id\n nome\n __typename\n }\n beneficios\n nomeTradicional\n responsavelLegal\n stChefeFamilia\n unidadeFunai\n livro\n folha\n cadastroUnico\n ufNascimento {\n id\n sigla\n __typename\n }\n dtEmissao\n dtReconhecimento\n __typename\n }\n enderecoIndigena {\n aldeiaResidencia {\n id\n nome\n __typename\n }\n poloBaseResidencia {\n id\n nome\n __typename\n }\n dseiResidencia {\n id\n nome\n __typename\n }\n municipio {\n id\n nome\n __typename\n }\n uf {\n id\n sigla\n __typename\n }\n numero\n __typename\n }\n numeroFamilia\n tipoEndereco\n tipoLocalNascimento\n __typename\n }\n}\n
    """
    detalhes_envelope = {
        "query": consulta_detalhes,
        "variables": {
            "id": id_paciente
        }
    }
    print("Buscando detalhes do paciente...")
    detalhes_resposta = api_post("https://esus.procempa.com.br/api/graphql", detalhes_envelope, meus_headers, "buscar detalhes do paciente")
    if detalhes_resposta is None:
        print("⚠ Falha ao buscar detalhes, pulando paciente...")
        continue

    detalhes_dados = detalhes_resposta.json()
    
    # Verificar se paciente tem unidade vinculada
    cidadao_vinculacao = detalhes_dados['data']['cidadao'].get('cidadaoVinculacaoEquipe')
    if not cidadao_vinculacao or not cidadao_vinculacao.get('unidadeSaude'):
        print("⚠ Paciente sem unidade de saúde vinculada, pulando...")
        continue
    
    us_responsavel = cidadao_vinculacao['unidadeSaude']['nome']
    print(f"✓ Unidade de Saúde Responsável: {us_responsavel}")
    
    # Verificar se paciente tem prontuário
    prontuario = detalhes_dados['data']['cidadao'].get('prontuario')
    if not prontuario or not prontuario.get('id'):
        print("⚠ Paciente sem prontuário cadastrado, pulando...")
        continue
    
    id_prontuario = prontuario['id']
    print(f"✓ ID do Prontuário: {id_prontuario}")

    justificativa_envelope = {
        "query": """
        mutation SalvarJustificativaVisualizarProntuario($input: JustificativaVisualizarProntuarioInput!) {
        salvarJustificativaVisualizarProntuario(input: $input)
    }
    """,
        "variables": {
            "input": {
                "justificativa": "Monitoramento Bolsa Familia",
                "prontuarioId": id_prontuario
                }
        }
    }
    print("Salvando justificativa de acesso ao prontuário...")
    justificativa_resposta = api_post("https://esus.procempa.com.br/api/graphql", justificativa_envelope, meus_headers, "salvar justificativa")
    if justificativa_resposta is None:
        print("⚠ Falha ao salvar justificativa, pulando paciente...")
        continue

    justificativa_dados = justificativa_resposta.json()
    aprovação = justificativa_dados.get('data', {}).get('salvarJustificativaVisualizarProntuario', False)
    if aprovação:
        print("✓ Justificativa salva com sucesso.")
    else:
        print("✗ Falha ao salvar a justificativa.")

    historico_envelope = {
        "query": """
    query BuscaListagemHistoricoClinico($input: HistoricoQueryInput!) {\n  historico(input: $input) {\n    content {\n      idAtendRecente\n      idAtendProcessado\n      codigoUnicoRegistro\n      dataAtendimento\n      dataInativacao\n      dataUltimaRetificacao\n      turno\n      tipoApresentacao\n      tipoAtendProf\n      isCancelado\n      isInativo\n      isRetificado\n      coSubtipoAtendimento\n      origemAtendimento\n      cpfCnsCidadao\n      classificacaoRisco\n      idAtividadeColetiva\n      idCidadao\n      idadeGestacional {\n        dias\n        semanas\n        __typename\n      }\n      isAtendRecente\n      condicoesAvaliadas\n      examesRealizadosZika\n      profissional {\n        id\n        nome\n        nomeCivil\n        nomeSocial\n        __typename\n      }\n      cbo {\n        id\n        nome\n        cbo2002\n        __typename\n      }\n      estagiario {\n        id\n        nome\n        nomeCivil\n        nomeSocial\n        __typename\n      }\n      cboEstagio {\n        id\n        nome\n        cbo2002\n        __typename\n      }\n      unidadeSaude {\n        id\n        nome\n        cnes\n        __typename\n      }\n      equipe {\n        id\n        ine\n        nome\n        __typename\n      }\n      cnsProfissional\n      isVersaoFichaRetificavel\n      hasPrescricaoMedicamento\n      hasOrientacao\n      hasAtestado\n      hasLembrete\n      hasAlergia\n      hasSolicitacaoExame\n      hasResultadoExame\n      hasEncaminhamento\n      hasEncaminhamentoEspecializado\n      hasProcedimentoClinico\n      hasMarcadorConsumoAlimentar\n      hasCuidadoCompartilhado\n      hasGuiasEncaminhamentos\n      hasIvcf\n      hasAnexoArquivo\n      dadosClinicos\n      condicoesVacinacao {\n        idAtend\n        isViajante\n        condicaoMaternal\n        isComunicanteHanseniase\n        __typename\n      }\n      tipoConsultaOdonto\n      fichasConcatenadas {\n        uuidProcedimento\n        uuidZika\n        __typename\n      }\n      hasObservacao\n      isAtendObsFinalizado\n      inicioAtendimentoObservacao\n      fimAtendimentoObservacao\n      cuidadoCompartilhadoEvolucao {\n        ...HistoricoCuidadoCompartilhadoEvolucaoHeader\n        __typename\n      }\n      cuidadoCompartilhado {\n        ...HistoricoCuidadoCompartilhadoHeader\n        __typename\n      }\n      nomeFinalizadorObservacao\n      cnsFinalizadorObservacao\n      cboFinalizadorObservacao\n      ubsFinalizadorObservacao\n      ineFinalizadorObservacao\n      ...CuidadoCompartilhadoDw\n      __typename\n    }\n    pageInfo {\n      ...PageInfo\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment HistoricoCuidadoCompartilhadoEvolucaoHeader on CuidadoCompartilhadoEvolucao {\n  id\n  conduta\n  classificacaoPrioridade\n  reclassificacaoPrioridade\n  lotacaoExecutante {\n    ...LotacaoHistoricoCuidadoCompartilhadoHeader\n    __typename\n  }\n  cboExecutante {\n    ...CboHistoricoCuidadoCompartilhadoHeader\n    __typename\n  }\n  unidadeSaudeExecutante {\n    ...UnidadeSaudeHistoricoCuidadoCompartilhadoHeader\n    __typename\n  }\n  __typename\n}\n\nfragment LotacaoHistoricoCuidadoCompartilhadoHeader on Lotacao {\n  id\n  profissional {\n    id\n    cns\n    nome\n    nomeCivil\n    nomeSocial\n    __typename\n  }\n  cbo {\n    ...CboHistoricoCuidadoCompartilhadoHeader\n    __typename\n  }\n  equipe {\n    id\n    ine\n    nome\n    __typename\n  }\n  unidadeSaude {\n    ...UnidadeSaudeHistoricoCuidadoCompartilhadoHeader\n    __typename\n  }\n  __typename\n}\n\nfragment CboHistoricoCuidadoCompartilhadoHeader on Cbo {\n  id\n  nome\n  __typename\n}\n\nfragment UnidadeSaudeHistoricoCuidadoCompartilhadoHeader on UnidadeSaude {\n  id\n  nome\n  cnes\n  __typename\n}\n\nfragment HistoricoCuidadoCompartilhadoHeader on CuidadoCompartilhado {\n  id\n  cid10 {\n    ...Cid10\n    __typename\n  }\n  ciap {\n    ...Ciap\n    __typename\n  }\n  lotacaoSolicitante {\n    ...LotacaoHistoricoCuidadoCompartilhadoHeader\n    __typename\n  }\n  __typename\n}\n\nfragment Cid10 on Cid10 {\n  id\n  codigo\n  nome\n  __typename\n}\n\nfragment Ciap on Ciap {\n  id\n  codigo\n  descricao\n  __typename\n}\n\nfragment CuidadoCompartilhadoDw on Historico {\n  ciapNome\n  ciapCodigo\n  cidNome\n  cidCodigo\n  classificacaoPrioridade\n  reclassificacaoPrioridade\n  conduta\n  cnsSolicitante\n  nomeSolicitante\n  cboSolicitante\n  ineSolicitante\n  siglaEquipeSolicitante\n  nomeUbsSolicitante\n  cnsExecutante\n  nomeExecutante\n  cboExecutante\n  ineExecutante\n  siglaEquipeExecutante\n  nomeUbsExecutante\n  __typename\n}\n\nfragment PageInfo on PageInfo {\n  number\n  size\n  totalPages\n  totalElements\n  sort\n  first\n  last\n  numberOfElements\n  __typename\n}\n
        """,
        "variables": {
            "input": {
                "cidadaoId": id_paciente,
                "somenteMeusRegistros": False,
                "sortDirection": "DESC",
                "filtrosAvancados": {
                    "periodo": None,
                    "exibirRegistrosInativos": False
                },
                "pageParams": {
                    "size": 10
                }
            }
        }
    }
    print("Buscando histórico de atendimentos...")
    historico_resposta = api_post("https://esus.procempa.com.br/api/graphql", historico_envelope, meus_headers, "buscar histórico")
    if historico_resposta is None:
        print("⚠ Falha ao buscar histórico, pulando paciente...")
        continue

    historico_dados = historico_resposta.json()
    lista_atendimentos = historico_dados['data']['historico']['content']
    print(f"✓ Encontrados {len(lista_atendimentos)} atendimentos no histórico")
    print(f"Processando os 5 atendimentos mais recentes...")

    cursor.execute('DELETE FROM atendimentos WHERE meu_id = ?', (meu_id,))
    conexao.commit()
    print(f"Atendimentos anteriores removidos do banco de dados")

    nome_paciente = dados['data']['cidadaos']['content'][0]['nome']
    cursor.execute('''
    INSERT OR IGNORE INTO pacientes (meu_id, nome, cns, cpf, us_responsavel)
    VALUES (?, ?, ?, ?, ?)
    ''', (meu_id, nome_paciente, meu_cns, meu_cpf, us_responsavel))

    for registro in lista_atendimentos[:5]:
        timestamp_ms = registro['dataAtendimento']
        data_convertida = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%d/%m/%Y %H:%M')
        data = registro['dataAtendimento']
        profissional = registro['profissional']['nome'] if registro.get('profissional') else 'N/A'
        atendimento = registro.get('tipoApresentacao', 'N/A')
        unidade = registro['unidadeSaude']['nome'] if registro.get('unidadeSaude') else 'N/A'
        print(f"\n  [{registro.get('idAtendRecente', 'N/A')}] {data_convertida} | {atendimento} | {unidade}")

        cursor.execute('''
        INSERT INTO atendimentos (meu_id, nome, atendimentos, data_convertida, unidade)
        VALUES (?, ?, ?, ?, ?)
        ''', (meu_id, nome_paciente, atendimento, data_convertida, unidade))
        print(f"  ✓ Atendimento salvo no banco de dados")

        if unidade != us_responsavel:
            print(f"  ⚠ DIVERGÊNCIA: Atendimento em {unidade} (Referência: {us_responsavel})")
            cursor.execute('''
                INSERT INTO divergencias (cns_paciente, nome, data_atendimento, unidade_realizada, unidade_referencia, tipo_atendimento) 
                VALUES (?, ?, ?, ?, ?, ?)''', 
                (meu_cns, nome_paciente, data_convertida, unidade, us_responsavel, atendimento)
            )
            print(f"  ✓ Divergência registrada no banco de dados")
        
    # Atualizar timestamp de processamento
    data_hora_atual = datetime.now(TIMEZONE_BR).strftime('%d/%m/%Y %H:%M:%S')
    cursor.execute('''
        UPDATE pacientes SET ultima_atualizacao = ? WHERE meu_id = ?
    ''', (data_hora_atual, meu_id))
    
    conexao.commit()
    print(f"\n✓ Paciente {nome_paciente} processado com sucesso!")
    print(f"⏱ Última atualização: {data_hora_atual}")
    time.sleep(2)  # Pausa de 2 segundos entre o processamento de pacientes
    
print(f"\n{'='*60}")
print(f"PROCESSAMENTO CONCLUÍDO - {len(indices_ordenados)} pacientes processados")
print(f"{'='*60}\n")
conexao.close()