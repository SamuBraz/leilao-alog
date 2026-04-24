import logging
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from monitor import Monitor

log = logging.getLogger(__name__)

FORM_URL = "https://forms.gle/Rg6WJkKy8XP6eDvr8"


def _mensagem_sem_mudanca(item_buscar: str, valor: float, username: str) -> str:
    return (
        f"Assunto: Monitoramento Concluído — Sem Alterações\n"
        f"\n"
        f"Prezado(a),\n"
        f"\n"
        f"O monitoramento do campo \"{item_buscar}\" foi concluído sem que nenhuma "
        f"alteração de valor fosse detectada durante o período monitorado.\n"
        f"\n"
        f"Valor observado: {valor:,.2f}\n"
        f"\n"
        f"Atenciosamente,\n"
        f"Sistema de Monitoramento de Leilão\n"
        f"\n"
        f"Relatório gerado com pedido do usuário {username}"
    )


def _mensagem_com_mudanca(item_buscar: str, historico: list[tuple], username: str) -> str:
    linhas = [
        f"Assunto: Alerta — Alteração Detectada em \"{item_buscar}\"",
        "",
        "Prezado(a),",
        "",
        f"Foram detectadas {len(historico)} alteração(ões) no campo monitorado. Segue o resumo:",
        "",
        f"Campo monitorado: {item_buscar}",
        "Mudanças registradas:",
    ]
    for i, (ts, antigo, novo) in enumerate(historico, 1):
        horario = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M:%S")
        variacao = novo - antigo
        sinal = "+" if variacao >= 0 else ""
        linhas.append(
            f"  {i}. {horario}  |  {antigo:,.2f} → {novo:,.2f}  ({sinal}{variacao:,.2f})"
        )
    linhas += [
        "",
        "Atenciosamente,",
        "Sistema de Monitoramento de Leilão",
        "",
        f"Relatório gerado com pedido do usuário {username}",
    ]
    return "\n".join(linhas)


class Automator:
    def __init__(self, driver: webdriver.Chrome):
        self._driver = driver

    def _preencher_campo(self, label: str, valor: str):
        log.info("Preenchendo campo '%s'...", label)
        seletores = [
            (By.XPATH, f"//input[@aria-label='{label}']"),
            (By.XPATH, f"//textarea[@aria-label='{label}']"),
            (By.XPATH, f"//*[normalize-space(text())='{label}']/following::input[1]"),
            (By.XPATH, f"//*[normalize-space(text())='{label}']/following::textarea[1]"),
            (By.XPATH, f"//*[contains(normalize-space(text()),'{label}')]/following::input[1]"),
            (By.XPATH, f"//*[contains(normalize-space(text()),'{label}')]/following::textarea[1]"),
        ]
        for by, seletor in seletores:
            try:
                campo = WebDriverWait(self._driver, 4).until(
                    EC.presence_of_element_located((by, seletor))
                )
                campo.clear()
                campo.send_keys(valor)
                log.info("Campo '%s' preenchido.", label)
                return
            except Exception:
                continue

        inputs = self._driver.find_elements(By.XPATH, "//input | //textarea")
        log.debug("Inputs na página (%d):", len(inputs))
        for el in inputs:
            log.debug("  tag=%s | aria-label='%s' | type='%s'",
                      el.tag_name, el.get_attribute("aria-label"), el.get_attribute("type"))
        raise Exception(f"Campo '{label}' não encontrado no formulário.")

    def enviar_resultado(self, item_buscar: str, historico: list[tuple], valor_atual: float, username: str):
        log.info("Gerando mensagem do relatório...")
        if historico:
            mensagem = _mensagem_com_mudanca(item_buscar, historico, username)
        else:
            mensagem = _mensagem_sem_mudanca(item_buscar, valor_atual, username)

        log.info("Enviando resultado ao formulário...\n%s", mensagem)

        self._driver.get(FORM_URL)
        WebDriverWait(self._driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )

        self._preencher_campo("Resultado", mensagem)

        log.info("Clicando em Enviar...")
        botao_enviar = WebDriverWait(self._driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Enviar']/..")
            )
        )
        botao_enviar.click()
        log.info("Formulário enviado com sucesso.")
        time.sleep(2)
