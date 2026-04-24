import logging
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

log = logging.getLogger(__name__)

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
        self.iframe_index_encontrado: int | None = None
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
        log.info("Iniciando Chrome...")
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.maximize_window()
        log.info("Chrome iniciado.")
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
            return numero_texto

        numero_value = self._extrair_numero_financeiro(value)
        if numero_value is not None:
            return numero_value

        if texto or value:
            pass
        return None

    def _obter_xpath_elemento(self, elemento) -> str:
        '''Retorna o XPath absoluto do elemento via JavaScript.'''
        return self._driver.execute_script("""
            function getXPath(el) {
                if (!el) return '';
                if (el.id) return '//' + el.tagName.toLowerCase() + '[@id="' + el.id + '"]';
                var parts = [];
                while (el && el.nodeType === 1) {
                    var idx = 1, s = el.previousElementSibling;
                    while (s) { if (s.tagName === el.tagName) idx++; s = s.previousElementSibling; }
                    parts.unshift(el.tagName.toLowerCase() + '[' + idx + ']');
                    el = el.parentElement;
                }
                return '/' + parts.join('/');
            }
            return getXPath(arguments[0]);
        """, elemento)

    def buscar_elemento(self):
        '''Busca elementos com base no item_buscar, varrendo iframes.'''
        log.info("Buscando elemento '%s' na página...", self.item_buscar)
        elementos_correspondentes = []
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")
        log.info("Total de iframes: %d", len(iframes))

        for i, iframe in enumerate(iframes):
            try:
                self._driver.switch_to.frame(iframe)
                elements = self._driver.find_elements(
                    By.XPATH,
                    f"//*[contains(text(), '{self.item_buscar}')]"
                )
                if elements:
                    log.info("Encontrado no iframe %d!", i)
                    for s in elements:
                        log.info("  -> '%s'", s.text)
                        elementos_correspondentes.append((i, s))
            except NoSuchElementException:
                log.debug("[iframe %d] Elemento não encontrado.", i)
            except Exception as e:
                log.warning("Erro no iframe %d: %s", i, e)
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
        log.info("Buscando valor numérico associado ao elemento...")
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")

        for iframe_index, elemento in reversed(elementos_correspondentes):
            try:
                self._driver.switch_to.frame(iframes[iframe_index])
                log.info("ELEMENTO: '%s' | tag: %s", elemento.text, elemento.tag_name)

                # ── Estratégia 1: subida na hierarquia html─────
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
                            numero = self._verificar_fonte(desc)
                            if numero is not None:
                                log.info("[DOM nível %d] Valor aceito: %s | tag: %s", nivel, numero, desc.tag_name)
                                self.valor_atual = numero
                                self.iframe_index_encontrado = iframe_index
                                self.xpath_encontrado = self._obter_xpath_elemento(desc)
                                return numero, self.xpath_encontrado
                        except:
                            continue
                    atual = pai

            except Exception as e:
                log.error("Erro ao acessar iframe %d: %s", iframe_index, e)
            finally:
                self._driver.switch_to.default_content()

        log.warning("Valor não encontrado por nenhuma estratégia.")
        return None, None

    def _ler_valor_no_xpath(self) -> float | None:
        '''Lê o valor diretamente pelo xpath salvo, sem varrer o DOM todo.'''
        if self.xpath_encontrado is None or self.iframe_index_encontrado is None:
            return None
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")
        try:
            self._driver.switch_to.frame(iframes[self.iframe_index_encontrado])
            elemento = self._driver.find_element(By.XPATH, self.xpath_encontrado)
            return self._verificar_fonte(elemento)
        except Exception as e:
            log.error("Erro ao reler valor: %s", e)
            return None
        finally:
            self._driver.switch_to.default_content()

    def monitorar(self, intervalo: int = 10, timeout: int = 50):
        '''
        Loop de monitoração: atualiza a página a cada `intervalo` segundos,
        lê o campo pelo xpath salvo e dispara on_mudanca se o valor mudar.
        Para ao atingir 2 mudanças ou `timeout` segundos, o que ocorrer primeiro.
        '''
        log.info("Monitorando '%s' | valor inicial: %s | intervalo: %ds | timeout: %ds",
                 self.item_buscar, self.valor_atual, intervalo, timeout)
        mudancas = 0
        inicio = time.time()
        while True:
            decorrido = time.time() - inicio
            if decorrido >= timeout:
                log.info("Timeout de %ds atingido. Encerrando monitoração.", timeout)
                break

            time.sleep(intervalo)
            try:
                log.info("Atualizando página...")
                self._driver.refresh()
                time.sleep(5)
                novo_valor = self._ler_valor_no_xpath()
            except Exception as e:
                log.error("Erro durante monitoração: %s", e)
                continue

            if novo_valor is None:
                log.warning("Não foi possível ler o valor.")
                continue

            if novo_valor != self.valor_atual:
                antigo = self.valor_atual
                self.valor_atual = novo_valor
                self.historico.append((time.time(), antigo, novo_valor))
                mudancas += 1
                log.info("Mudança %d/2: %s → %s", mudancas, antigo, novo_valor)
                if self.on_mudanca:
                    self.on_mudanca(antigo, novo_valor)
                if mudancas >= 2:
                    log.info("Duas mudanças detectadas. Encerrando monitoração.")
                    break
            else:
                log.info("Sem mudança: %s", self.valor_atual)

    def iniciar(self):
        log.info("=== Iniciando monitor ===")
        self._driver = self._criar_driver()
        try:
            log.info("Abrindo URL '%s'...", self.url)
            self._driver.get(self.url)
        except TimeoutException:
            log.warning("Page load timeout (%ss) — continuando com o que foi carregado.", self.timeout)
        time.sleep(30)
        elementos = self.buscar_elemento()
        _, xpath = self.buscar_valor(elementos)

        if xpath:
            log.info("Valor referente ao campo '%s': %s", self.item_buscar, self.valor_atual)
            self.monitorar()

        log.info("Histórico de mudanças: %s", self.historico)
