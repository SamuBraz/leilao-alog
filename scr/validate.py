import re
from urllib.parse import urlparse


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

    def __str__(self):
        return (
            f"URL: {self.url} | "
            f"Campo: {self.item_buscar} | "
            f"Usuário: {self.nome_usuario} | "
            f"Timeout: {self.timeout}s"
        )

    def valida_nome(self) -> bool:
        """Valida nome do usuário"""
        nome = self.nome_usuario.strip()
        if len(nome) < 3:
            self.erros.append(f"Nome '{nome}' inválido: mínimo 3 caracteres.")
            return False
        return True

    def valida_url(self) -> bool:
        """Valida URL: esquema http/https e domínio presente."""
        url = self.url.strip()
        if not url:
            self.erros.append("URL não pode ser vazia.")
            return False

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            self.erros.append(f"Esquema inválido: '{parsed.scheme}'. Use http ou https.")
            return False

        if not parsed.netloc:
            self.erros.append(f"URL sem domínio: '{url}'.")
            return False

        return True

    def valida_campo(self) -> bool:
        """Verifica se o campo solicitado é compatível com valor numérico"""
        campo = self.item_buscar.strip().lower()
        if not campo:
            self.erros.append("O campo buscado não pode ser vazio.")
            return False

        nao_numericos = {"nome", "titulo", "descricao", "categoria", "imagem", "email", "endereco"}
        if campo in nao_numericos:
            self.erros.append(f"Campo '{self.item_buscar}' não é numérico.")
            return False

        return True

    def valida_timeout(self) -> bool:
        """Valida timeout"""
        try:
            valor = float(self.timeout)
        except (TypeError, ValueError):
            self.erros.append(f"Timeout '{self.timeout}' não é um número válido.")
            return False

        if not (1.0 <= valor <= 3600.0):
            self.erros.append(f"Timeout {valor}s fora do intervalo permitido (1s a 3600s).")
            return False

        return True


    def valida(self) -> dict:
        """
        Executa todas as validações e retorna relatório consolidado. 

        Returns
        -------
        dict com chaves 'valido' (bool) e 'erros' (list[str])
        """
        self.erros.clear()
        resultados = {
            "nome"    : self.valida_nome(),
            "url"     : self.valida_url(),
            "campo"   : self.valida_campo(),
            "timeout" : self.valida_timeout(),
        }
        return {
            "valido"  : all(resultados.values()),
            "erros"   : list(self.erros),
        }


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    validate = Validate('https://b3.com.br/pt_br/para-voce', 12, 'Alice')
    print(validate)
    resultado = validate.valida()
    print("Válido:", resultado["valido"])
    print("Erros: ", resultado["erros"])