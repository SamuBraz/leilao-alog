from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import time

class Monitor():
    def __init__(self,url: str,item_buscar: str,on_mudanca=None,):
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
    

    def buscar_elemento(self):
        '''Busca elementos com base no elemento buscar.'''
        elementos_correspondentes = []  # agora guarda (iframe_index, elemento)
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
                        elementos_correspondentes.append((i, s))  # ← guarda o índice do iframe junto
            except NoSuchElementException:
                print(f"  [iframe {i}] Elemento nao encontrado neste iframe.")
            except Exception as e:
                print(f"Erro no iframe {i}: {e}")
            finally:
                self._driver.switch_to.default_content()
        return elementos_correspondentes
    
    def buscar_valor(self, elementos_correspondentes):
        '''Dado o label encontrado, tenta achar o valor numérico vizinho.'''
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")
        for iframe_index, s in elementos_correspondentes:
            try:
                print('\n ')
                # Volta para o iframe onde o elemento foi encontrado
                self._driver.switch_to.frame(iframes[iframe_index])
                print(f"ELEMENTO: '{s.text}' | tag: {s.tag_name}")
                atual = s
                for nivel in range(1, 5):
                    try:
                        atual = atual.find_element(By.XPATH, "..")
                        print(f"  NÍVEL {nivel} acima | tag: {atual.tag_name} | texto: '{atual.text[:300]}'")
                    except:
                        break
            except Exception as e:
                print(f"Erro ao acessar iframe {iframe_index}: {e}")
            finally:
                self._driver.switch_to.default_content()
    
                


    def iniciar(self):
        self._driver = self._criar_driver()
        self._driver.get(self.url)
        WebDriverWait(self._driver, self.timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        elementos = self.buscar_elemento()
        self.buscar_valor(elementos)


if __name__ == '__main__':

    def ao_mudar(antigo, novo):
        print(f"\n>>> Preço mudou: {antigo:.2f} → {novo:.2f}\n")

    monitor = Monitor(
        url="https://b3.com.br/pt_br/para-voce",
        item_buscar="TBCC4L",
        on_mudanca=ao_mudar,
        )
    monitor.iniciar()