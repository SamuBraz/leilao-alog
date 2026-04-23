from selenium import webdriver
from selenium.webdriver.common.by import By
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
        iframes = self._driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Total de iframes: {len(iframes)}")

        for i, iframe in enumerate(iframes):
            try:
                self._driver.switch_to.frame(iframe)
                spans = self._driver.find_elements(
                    By.XPATH,
                    f"//span[contains(text(), '{self.item_buscar}')]"
                )

                if spans:
                    print(f"✅ Encontrado no iframe {i}!")
                    for s in spans:
                        print(f"  -> '{s.text}'")
                    break
                else:
                    self._driver.switch_to.default_content()

            except Exception as e:
                print(f"Erro no iframe {i}: {e}")
                self._driver.switch_to.default_content()


    def iniciar(self):
        self._driver = self._criar_driver()
        self._driver.get(self.url)
        time.sleep(8)  # aguarda carregamento inicia
        self.buscar_elemento()



if __name__ == '__main__':

    def ao_mudar(antigo, novo):
        print(f"\n>>> Preço mudou: {antigo:.2f} → {novo:.2f}\n")

    monitor = Monitor(
        url="https://b3.com.br/pt_br/para-voce",
        item_buscar="Cogna Educacao S.A",
        on_mudanca=ao_mudar,
        )
    monitor.iniciar()