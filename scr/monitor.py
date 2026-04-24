from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re
import time

REGEX_NUMERO = re.compile(r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b|\b\d+[.,]\d+\b')

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

    def _extrair_numero_do_texto(self, texto: str) -> float | None:
        '''Extrai o primeiro número financeiro de um texto via regex.'''
        matches = REGEX_NUMERO.findall(texto)
        for m in matches:
            try:
                normalizado = m.replace('.', '').replace(',', '.')
                return float(normalizado)
            except ValueError:
                continue
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
          1) Atributos semânticos (data-*, aria-*, classes CSS)
          2) Subida no DOM filtrando descendentes com regex numérico
        '''
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")

        for iframe_index, elemento in elementos_correspondentes:
            try:
                self._driver.switch_to.frame(iframes[iframe_index])
                print(f"\nELEMENTO: '{elemento.text}' | tag: {elemento.tag_name}")

                # ── Estratégia 1: atributos semânticos ──────────────────────
                # Sobe níveis procurando um container com data-* ou aria-*
                # que indique preço, e extrai o valor do texto ou atributo
                chaves_preco = {"price", "value", "last", "close",
                                "bid", "ask", "rate", "quote", "preco", "valor"}
                atual = elemento
                for nivel in range(1, 6):
                    try:
                        atual = atual.find_element(By.XPATH, "..")
                    except:
                        break

                    descendentes = atual.find_elements(By.XPATH, ".//*")
                    for desc in descendentes:
                        if desc == elemento:
                            continue

                        # Verifica atributos data-* e aria-*
                        for attr in ["data-field", "data-type", "data-name",
                                     "aria-label", "class", "id"]:
                            try:
                                val_attr = (desc.get_attribute(attr) or "").lower()
                                if any(chave in val_attr for chave in chaves_preco):
                                    texto = desc.text.strip() or desc.get_attribute("value") or ""
                                    numero = self._extrair_numero_do_texto(texto)
                                    if numero is not None:
                                        print(f"  [Atributo '{attr}' nível {nivel}] "
                                              f"Valor: {numero} | texto: '{texto}'")
                                        self.valor_atual = str(texto)
                                        return numero
                            except:
                                continue

                # ── Estratégia 2: subida no DOM + regex nos descendentes ─────
                # Sobe níveis e varre todos os descendentes do pai
                # filtrando qualquer texto que bata com padrão numérico
                atual = elemento
                for nivel in range(1, 6):
                    try:
                        pai = atual.find_element(By.XPATH, "..")
                    except:
                        break

                    descendentes = pai.find_elements(By.XPATH, ".//*")
                    for desc in descendentes:
                        if desc == elemento:
                            continue
                        try:
                            texto = desc.text.strip()
                            if not texto:
                                continue
                            numero = self._extrair_numero_do_texto(texto)
                            if numero is not None:
                                print(f"  [DOM nível {nivel}] "
                                      f"Valor: {numero} | texto: '{texto}' | tag: {desc.tag_name}")
                                self.valor_atual = str(texto)
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

        print(f'valor atual do {self.item_buscar} {self.valor_atual}')


if __name__ == '__main__':
    def ao_mudar(antigo, novo):
        print(f"\n>>> Preço mudou: {antigo:.2f} → {novo:.2f}\n")

    monitor = Monitor(
        url="https://b3.com.br/pt_br/para-voce",
        item_buscar="TERRA BRAVIAPN",
        on_mudanca=ao_mudar,
    )
    monitor.iniciar()