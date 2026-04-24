import logging
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class PaginaNaoCarregadaError(Exception):
    """Levantada quando a página não carrega por completo dentro do tempo limite."""
    pass


class Validate:
    """
    Valida as entradas do usuário antes do monitoramento.

    Parameters
    ----------
    url : str
        Endereço da página a ser monitorada.
    item_buscar : str
        Campo numérico a ser encontrado (ex: "preço", "lance", "dolar").
    nome_usuario : str
        Nome do usuário para log (mínimo 3 caracteres).
    timeout : float
        Intervalo em segundos entre verificações. Padrão: 30.
    """

    def __init__(self, url: str, item_buscar: str, nome_usuario: str = ""):
        self.url = url
        self.item_buscar = item_buscar
        self.nome_usuario = nome_usuario
        self.timeout = 30.0
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def __str__(self):
        return (
            f"URL: {self.url} | "
            f"Campo: {self.item_buscar} | "
            f"Usuário: {self.nome_usuario} | "
            f"Timeout: {self.timeout}s"
        )

    def valida_nome(self) -> bool:
        """Valida nome do usuário"""
        log.info("Validando nome do usuário...")
        nome = self.nome_usuario.strip()
        if len(nome) < 3:
            msg = f"Nome '{nome}' inválido: mínimo 3 caracteres."
            self.erros.append(msg)
            log.error("Nome inválido — %s", msg)
            return False
        log.info("Nome '%s' OK.", nome)
        return True

    def valida_url(self) -> bool:
        """Valida URL: esquema http/https e domínio presente."""
        log.info("Validando URL...")
        url = self.url.strip()
        if not url:
            msg = "URL não pode ser vazia."
            self.erros.append(msg)
            log.error(msg)
            return False

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            msg = f"Esquema inválido: '{parsed.scheme}'. Use http ou https."
            self.erros.append(msg)
            log.error(msg)
            return False

        if not parsed.netloc:
            msg = f"URL sem domínio: '{url}'."
            self.erros.append(msg)
            log.error(msg)
            return False

        log.info("URL '%s' OK.", url)
        return True

    def valida_campo(self) -> bool:
        """Verifica se o campo buscado é uma string e não um número. O(1)"""
        log.info("Validando campo buscado...")
        campo = self.item_buscar.strip()
        if not campo:
            msg = "O campo buscado não pode ser vazio."
            self.erros.append(msg)
            log.error(msg)
            return False

        try:
            int(campo)
            msg = f"Campo '{campo}' inválido: informe um nome de campo, não um número."
            self.erros.append(msg)
            log.error(msg)
            return False
        except ValueError:
            pass

        try:
            float(campo)
            msg = f"Campo '{campo}' inválido: informe um nome de campo, não um número."
            self.erros.append(msg)
            log.error(msg)
            return False
        except ValueError:
            log.info("Campo '%s' OK.", campo)
            return True

    def valida_acesso_url(self) -> bool:
        """Abre a URL com Selenium e verifica se a página carrega completamente antes do timeout."""
        log.info("Verificando acesso à URL via navegador...")
        if not self.valida_url():
            return False

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = None
        try:
            log.info("Iniciando Chrome (headless)...")
            driver = webdriver.Chrome(options=options)
            log.info("Acessando '%s'...", self.url.strip())
            driver.get(self.url.strip())
            log.info("Aguardando página carregar (timeout: %ss)...", self.timeout)
            try:
                WebDriverWait(driver, self.timeout).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                raise PaginaNaoCarregadaError(
                    f"A página '{self.url}' não carregou por completo dentro de {self.timeout}s."
                )
            log.info("Página carregada com sucesso.")
            return True
        except PaginaNaoCarregadaError:
            log.error("Timeout: página não carregou dentro de %ss.", self.timeout)
            raise
        except WebDriverException as e:
            log.error("Erro no navegador: %s", e.msg)
            raise Exception(f"Erro ao abrir o navegador para '{self.url}': {e.msg}.") from e
        except Exception as e:
            log.error("Erro inesperado ao acessar a URL: %s", e)
            raise Exception(f"Erro ao acessar o site '{self.url}': {e}.") from e
        finally:
            if driver:
                log.info("Encerrando navegador.")
                driver.quit()

    def valida_timeout(self) -> bool:
        """Valida timeout"""
        log.info("Validando timeout...")
        try:
            valor = float(self.timeout)
        except (TypeError, ValueError):
            msg = f"Timeout '{self.timeout}' não é um número válido."
            self.erros.append(msg)
            log.error(msg)
            return False

        if not (1.0 <= valor <= 3600.0):
            msg = f"Timeout {valor}s fora do intervalo permitido (1s a 3600s)."
            self.erros.append(msg)
            log.error(msg)
            return False

        log.info("Timeout %.1fs OK.", valor)
        return True

    def valida(self) -> dict:
        """
        Executa todas as validações e retorna relatório consolidado.

        Returns
        -------
        dict com chaves 'valido' (bool) e 'erros' (list[str])
        """
        log.info("=== Iniciando validação ===")
        self.erros.clear()
        self.avisos.clear()
        resultados = {
            "nome"    : self.valida_nome(),
            "url"     : self.valida_url(),
            "campo"   : self.valida_campo(),
            "timeout" : self.valida_timeout(),
        }
        self.valida_acesso_url()
        valido = all(resultados.values())
        if valido:
            log.info("=== Validação concluída: tudo OK ===")
        else:
            log.error("=== Validação concluída com erros: %s ===", self.erros)
        return {
            "valido"  : valido,
            "erros"   : list(self.erros),
            "avisos"  : list(self.avisos),
        }
