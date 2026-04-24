import logging

from ui import UI
from validate import Validate
from monitor import Monitor
from automator import Automator

log = logging.getLogger(__name__)


def main():
    # 1. Interface
    ui = UI()
    dados = ui.executar()

    # 2. Validação
    validate = Validate(
        url=dados["url"],
        item_buscar=dados["item_buscar"],
        nome_usuario=dados["nome_usuario"],
    )
    resultado = validate.valida()

    if not resultado["valido"]:
        log.error("Erros de validação:")
        for erro in resultado["erros"]:
            log.error("  - %s", erro)
        return

    # 3. Monitoramento
    def ao_mudar(antigo, novo):
        log.info("Mudança detectada: %s → %s", f"{antigo:,.2f}", f"{novo:,.2f}")

    monitor = Monitor(
        url=dados["url"],
        item_buscar=dados["item_buscar"],
        on_mudanca=ao_mudar,
    )
    monitor.iniciar()

    # 4. Registro no formulário
    automator = Automator(driver=monitor._driver)
    automator.enviar_resultado(
        monitor.item_buscar,
        monitor.historico,
        monitor.valor_atual,
        username=dados["nome_usuario"],
    )


if __name__ == "__main__":
    main()
