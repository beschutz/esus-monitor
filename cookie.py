from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests
import os
from selenium.webdriver.chrome.options import Options

# ============================================================
# CONFIGURAÇÃO DE PERFIL PERSISTENTE
# ============================================================
# Defina o caminho para salvar o perfil do Chrome
# Se usar perfil persistente, os cookies e sessão são mantidos entre execuções
USAR_PERFIL_PERSISTENTE = True
PERFIL_DIR = "/workspaces/codespaces-blank/.chrome_profile"

opcoes = Options()
opcoes.add_argument("--headless=new")  # Executa o Chrome em modo headless (sem interface gráfica)
opcoes.add_argument("--no-sandbox")
opcoes.add_argument("--disable-dev-shm-usage")

if USAR_PERFIL_PERSISTENTE:
    # Cria diretório se não existir
    os.makedirs(PERFIL_DIR, exist_ok=True)
    opcoes.add_argument(f"--user-data-dir={PERFIL_DIR}")
    print(f"🔧 Usando perfil persistente em: {PERFIL_DIR}")
else:
    print("🔧 Usando perfil temporário (sessão única)")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)


def testar_api(cookies_string, token_csrf):
    """Testa se os cookies estão válidos fazendo uma requisição simples"""
    print("\n🔍 Testando validade dos cookies na API...")
    
    consulta_teste = """
    query CidadaoListing($filtro: CidadaosQueryInput!) {
      cidadaos(input: $filtro) {
        content {
          id
          nome
        }
      }
    }
    """
    
    envelope_teste = {
        "query": consulta_teste,
        "variables": {
            "filtro": {
                "query": "709609681809877",  # CNS de teste
                "pageParams": {
                    "size": 1
                }
            }
        }
    }
    
    headers_teste = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json",
        "Cookie": cookies_string,
        "Origin": "https://esus.procempa.com.br/cidadao",
        "Referer": "https://esus.procempa.com.br/cidadao",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-XSRF-TOKEN": token_csrf,
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }
    
    try:
        resposta = requests.post(
            "https://esus.procempa.com.br/api/graphql",
            json=envelope_teste,
            headers=headers_teste,
            timeout=10
        )
        
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados.get('errors'):
                erro_msg = dados['errors'][0].get('message', 'Erro desconhecido')
                print(f"❌ API retornou erro: {erro_msg}")
                
                # Se for acesso negado, interrompe tudo
                if "acesso não permitido" in erro_msg.lower() or "não permitido" in erro_msg.lower():
                    print("\n" + "="*60)
                    print("❌ ERRO CRÍTICO: Acesso negado pela API")
                    print("="*60)
                    print("Os cookies não têm permissão de acesso.")
                    print("Verifique se o usuário tem as permissões necessárias.")
                    print("O programa será encerrado.")
                    print("="*60 + "\n")
                    exit(1)
                
                return False
            else:
                print("✅ Cookies válidos! API respondeu com sucesso")
                return True
        else:
            print(f"❌ API retornou status {resposta.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
        return False


def obter_cookies():
    meu_jsessionid = None
    meu_token = None
    
    print("Acessando sistema...")
    navegador.get("https://esus.procempa.com.br/cidadao")
    print(f"Título: {navegador.title}")
    print(f"URL atual: {navegador.current_url}")
    
    time.sleep(2)
    
    navegador.find_element(By.NAME, "username").send_keys("04015739078")
    print("✓ Campo de usuário preenchido")
    time.sleep(1)
    
    navegador.find_element(By.NAME, "password").send_keys("Vancouver8&*")
    print("✓ Campo de senha preenchido")
    time.sleep(1)
    
    botao_entrar = navegador.find_element(By.CLASS_NAME, "css-1mc6ylg")
    navegador.execute_script("arguments[0].click();", botao_entrar)
    print("✓ Botão de entrar clicado")
    
    time.sleep(5)
    
    # Tentar clicar no botão "Continuar" se aparecer
    try:
        botao_continuar = navegador.find_element(By.CSS_SELECTOR, '[data-testid="confirmarAcaoConfirmacao"]')
        if botao_continuar.is_displayed():
            navegador.execute_script("arguments[0].click();", botao_continuar)
            print("✓ Botão 'Continuar' clicado")
            time.sleep(2)
    except:
        print("ℹ Botão 'Continuar' não encontrado (pode não ter aparecido)")
    
    # VERIFICAR SE O LOGIN FOI BEM-SUCEDIDO
    url_atual = navegador.current_url
    titulo_atual = navegador.title
    
    print(f"\n🔍 Verificando se login foi bem-sucedido...")
    print(f"  URL atual: {url_atual}")
    print(f"  Título: {titulo_atual}")
    
    # Tenta encontrar elementos que só existem na página de login
    try:
        # Se ainda consegue encontrar o campo de login, ainda está na tela de login
        campo_login = navegador.find_elements(By.NAME, "username")
        if campo_login and campo_login[0].is_displayed():
            print("❌ ERRO: Ainda na página de login! Campo de usuário ainda visível.")
            print("   Possíveis causas:")
            print("   • Credenciais incorretas")
            print("   • Já existe sessão ativa em outro lugar")
            print("   • Erro no servidor")
            print("   • Captcha ou autenticação adicional necessária")
            return None, None
    except:
        pass  # Elemento não encontrado, provavelmente saiu da tela de login
    
    # Tenta encontrar elementos que indicam que está logado
    # (ajuste conforme os elementos reais da página logada)
    try:
        # Procura por menus, botões ou elementos típicos do sistema
        # Você pode ajustar esse seletor para algo específico do e-SUS
        elementos_logado = navegador.find_elements(By.TAG_NAME, "nav") or \
                          navegador.find_elements(By.CLASS_NAME, "menu") or \
                          navegador.find_elements(By.XPATH, "//*[contains(@class, 'header')]")
        
        if elementos_logado:
            print("✅ Login bem-sucedido! Elementos da interface logada detectados")
        else:
            print("⚠️ Difícil confirmar login - não encontrou elementos esperados")
    except:
        print("⚠️ Não foi possível verificar elementos da página logada")
    
    # Selecionar "Secretaria Municipal de Saude de Porto Alegre"
    try:
        print("\n🔍 Procurando opção de acesso...")
        cards = navegador.find_elements(By.CSS_SELECTOR, '[data-cy="Acesso.card"]')
        print(f"  Encontrados {len(cards)} cards de acesso")
        
        for idx, card in enumerate(cards, 1):
            try:
                h3 = card.find_element(By.TAG_NAME, "h3")
                texto = h3.text
                print(f"  Card {idx}: {texto}")
                
                if "Secretaria Municipal de Saude" in texto:
                    navegador.execute_script("arguments[0].click();", card)
                    print(f"✓ Clicado em: {texto}")
                    time.sleep(2)
                    break
            except:
                continue
        else:
            print("⚠️ Card 'Secretaria Municipal de Saude' não encontrado")
    except Exception as e:
        print(f"ℹ Seleção de unidade não necessária ou erro: {e}")

    
    # Captura TODOS os cookies
    cookies = navegador.get_cookies()
    print(f"\n📋 Total de cookies capturados: {len(cookies)}")
    print("\nCookies encontrados:")
    print("-" * 80)
    
    # Lista todos os cookies
    cookies_list = []
    for cookie in cookies:
        nome = cookie['name']
        valor = cookie['value']
        print(f"  • {nome}: {valor}")
        cookies_list.append(f"{nome}={valor}")
        
        # Guarda os importantes
        if nome == 'JSESSIONID':
            meu_jsessionid = valor
        if nome == 'XSRF-TOKEN':
            meu_token = valor
    
    print("-" * 80)
    
    # Monta string com TODOS os cookies
    cookies_string = "; ".join(cookies_list)
    
    print(f"\n🔑 JSESSIONID: {meu_jsessionid}")
    print(f"🔑 XSRF-TOKEN: {meu_token}")
    print(f"\n📦 String completa de cookies ({len(cookies_list)} cookies):")
    print(f"{cookies_string[:200]}..." if len(cookies_string) > 200 else cookies_string)
    
    # Testa se os cookies são válidos
    if testar_api(cookies_string, meu_token):
        print("\n✓ Cookies validados e prontos para uso!\n")
        return cookies_string, meu_token
    else:
        print("\n⚠ ATENÇÃO: Cookies obtidos mas podem não estar funcionando!\n")
        return cookies_string, meu_token


if __name__ == "__main__":
    # Executa apenas se o arquivo for rodado diretamente
    obter_cookies()
