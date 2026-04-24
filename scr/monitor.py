from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re
import time

REGEX_FINANCEIRO = re.compile(
    r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b'   # 1,000 ou 26,918.0
    r'|\b\d{1,3}(?:\.\d{3})+(?:,\d+)?\b'  # 1.234 ou 1.234,56
)

class Monitor():
    def __init__(self, url: str, item_buscar: str, on_mudanca=None):
        self.url = url
        self.item_buscar = item_buscar
        self.timeout = 30.0
        self.on_mudanca = on_mudanca

        self.xpath_encontrado: str | None = None
        self.valor_atual: float | None = None
        self.historico: list[tuple] = []
        self._driver: webdriver.Chrome | None = None

    def __str__(self):
        return (
            f"Monitor | URL: {self.url} | "
            f"Campo: {self.item_buscar} | "
            f"Timeout: {self.timeout}s | "
            f"Valor atual: {self.valor_atual}"
        )

    def _criar_driver(self) -> webdriver.Chrome:
        '''Inicia o Chrome'''
        driver = webdriver.Chrome()
        driver.maximize_window()
        return driver

    def _extrair_numero_financeiro(self, texto: str) -> float | None:
        '''
        Extrai número apenas se bater no padrão financeiro válido:
          - 1,000        (milhar com vírgula)
          - 26,918.0     (milhar com vírgula + decimal com ponto)
          - 1.234,56     (padrão BR: milhar com ponto + decimal com vírgula)
        Retorna None se o texto não bater em nenhum desses padrões.
        '''
        matches = REGEX_FINANCEIRO.findall(texto)
        for m in matches:
            try:
                # Padrão BR: milhar=ponto, decimal=vírgula → 1.234,56
                if re.match(r'^\d{1,3}(\.\d{3})+(,\d+)?$', m):
                    normalizado = m.replace('.', '').replace(',', '.')
                # Padrão EN: milhar=vírgula, decimal=ponto → 1,000 ou 26,918.0
                elif re.match(r'^\d{1,3}(,\d{3})+(\.\d+)?$', m):
                    normalizado = m.replace(',', '')
                else:
                    continue
                return float(normalizado)
            except ValueError:
                continue
        return None

    def _verificar_fonte(self, elemento) -> float | None:
        '''
        Verifica texto visível e atributo value do elemento.
        Prioriza texto; usa value como fallback.
        Retorna o valor apenas se bater no padrão financeiro.
        '''
        texto  = (elemento.text or "").strip()
        value  = (elemento.get_attribute("value") or "").strip()

        numero_texto = self._extrair_numero_financeiro(texto)
        if numero_texto is not None:
            print(f"    ✔ Padrão válido no texto  : '{texto}' → {numero_texto}")
            return numero_texto

        numero_value = self._extrair_numero_financeiro(value)
        if numero_value is not None:
            print(f"    ✔ Padrão válido no value  : '{value}' → {numero_value}")
            return numero_value

        # Informa o que foi descartado para facilitar debug
        if texto or value:
            print(f"    ✗ Descartado (fora do padrão) | texto: '{texto}' | value: '{value}'")
        return None

    def buscar_elemento(self):
        '''Busca elementos com base no item_buscar, varrendo iframes.'''
        elementos_correspondentes = []
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Total de iframes: {len(iframes)}")

        for i, iframe in enumerate(iframes):
            try:
                self._driver.switch_to.frame(iframe)
                elements = self._driver.find_elements(
                    By.XPATH,
                    f"//*[contains(text(), '{self.item_buscar}')]"
                )
                if elements:
                    print(f"✅ Encontrado no iframe {i}!")
                    for s in elements:
                        print(f"  -> '{s.text}'")
                        elementos_correspondentes.append((i, s))
            except NoSuchElementException:
                print(f"  [iframe {i}] Elemento não encontrado neste iframe.")
            except Exception as e:
                print(f"Erro no iframe {i}: {e}")
            finally:
                self._driver.switch_to.default_content()

        return elementos_correspondentes

    def buscar_valor(self, elementos_correspondentes):
        '''
        Dado o label encontrado, tenta achar o valor numérico vizinho.
        Combina duas estratégias:
          2) Subida no DOM filtrando descendentes com regex financeiro
        Em ambas, só aceita valores que batam no padrão financeiro.
        '''
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")

        
        for iframe_index, elemento in reversed(elementos_correspondentes):
            try:
                self._driver.switch_to.frame(iframes[iframe_index])
                print(f"\nELEMENTO: '{elemento.text}' | tag: {elemento.tag_name}")

                # ── Estratégia 1: subida na hierarquia html─────
                atual = elemento
                for nivel in range(1, 6):
                    try:
                        pai = atual.find_element(By.XPATH, "..")
                    except:
                        break

                    print(f"  [DOM nível {nivel}] varrendo descendentes...")
                    descendentes = pai.find_elements(By.XPATH, ".//*")
                    for desc in descendentes:
                        if desc == elemento:
                            continue
                        try:
                            numero = self._verificar_fonte(desc)
                            if numero is not None:
                                print(f"  [DOM nível {nivel}] ✅ Valor aceito: {numero} | tag: {desc.tag_name}")
                                self.valor_atual = numero
                                return numero
                        except:
                            continue
                    atual = pai

            except Exception as e:
                print(f"Erro ao acessar iframe {iframe_index}: {e}")
            finally:
                self._driver.switch_to.default_content()

        print("⚠️  Valor não encontrado por nenhuma estratégia.")
        return None

    def iniciar(self):
        self._driver = self._criar_driver()
        self._driver.get(self.url)
        time.sleep(10)
        elementos = self.buscar_elemento()
        self.buscar_valor(elementos)

        print(self.valor_atual)


if __name__ == '__main__':
    def ao_mudar(antigo, novo):
        print(f"\n>>> Preço mudou: {antigo:.2f} → {novo:.2f}\n")

    monitor = Monitor(
        url="https://einvestidor.estadao.com.br/",
        item_buscar="US 100 Cash CFD",
        on_mudanca=ao_mudar,
    )
    monitor.iniciar()