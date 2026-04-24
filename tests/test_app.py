import pytest
from unittest.mock import MagicMock, patch

from validate import Validate, PaginaNaoCarregadaError
from monitor import Monitor
from automator import _mensagem_sem_mudanca, _mensagem_com_mudanca


# ── Validate ─────────────────────────────────────────────────────────────────

class TestValidaNome:
    def test_nome_valido(self):
        v = Validate("http://example.com", "lance", "João")
        assert v.valida_nome() is True

    def test_nome_muito_curto(self):
        v = Validate("http://example.com", "lance", "Jo")
        assert v.valida_nome() is False
        assert len(v.erros) == 1


class TestValidaUrl:
    def test_url_valida(self):
        v = Validate("https://example.com", "lance", "Teste")
        assert v.valida_url() is True

    def test_url_esquema_invalido(self):
        v = Validate("ftp://example.com", "lance", "Teste")
        assert v.valida_url() is False

    def test_url_vazia(self):
        v = Validate("", "lance", "Teste")
        assert v.valida_url() is False


class TestValidaCampo:
    def test_campo_valido(self):
        v = Validate("http://example.com", "lance", "Teste")
        assert v.valida_campo() is True

    def test_campo_vazio(self):
        v = Validate("http://example.com", "", "Teste")
        assert v.valida_campo() is False

    def test_campo_numerico(self):
        v = Validate("http://example.com", "42", "Teste")
        assert v.valida_campo() is False


class TestValidaTimeout:
    def test_timeout_padrao_valido(self):
        v = Validate("http://example.com", "lance", "Teste")
        assert v.valida_timeout() is True

    def test_timeout_fora_do_intervalo(self):
        v = Validate("http://example.com", "lance", "Teste")
        v.timeout = 0.0
        assert v.valida_timeout() is False


# ── Monitor ───────────────────────────────────────────────────────────────────

class TestExtrairNumeroFinanceiro:
    def setup_method(self):
        self.m = Monitor("http://example.com", "lance")

    def test_formato_en(self):
        assert self.m._extrair_numero_financeiro("1,000") == 1000.0

    def test_formato_br(self):
        assert self.m._extrair_numero_financeiro("1.234,56") == 1234.56

    def test_numero_simples_retorna_none(self):
        assert self.m._extrair_numero_financeiro("42") is None

    def test_texto_sem_numero_retorna_none(self):
        assert self.m._extrair_numero_financeiro("lance atual") is None


# ── Automator ────────────────────────────────────────────────────────────────

class TestMensagens:
    def test_mensagem_sem_mudanca_contem_valor(self):
        msg = _mensagem_sem_mudanca("lance", 1500.0, "João")
        assert "lance" in msg
        assert "1,500.00" in msg
        assert "João" in msg

    def test_mensagem_com_mudanca_variacao_positiva(self):
        historico = [(1700000000.0, 1000.0, 1500.0)]
        msg = _mensagem_com_mudanca("lance", historico, "João")
        assert "+500.00" in msg
        assert "1,000.00" in msg
        assert "1,500.00" in msg

    def test_mensagem_com_mudanca_variacao_negativa(self):
        historico = [(1700000000.0, 2000.0, 1500.0)]
        msg = _mensagem_com_mudanca("lance", historico, "João")
        assert "-500.00" in msg
