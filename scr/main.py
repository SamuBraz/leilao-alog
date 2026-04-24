from ui import UI
from validate import Validate
from monitor import Monitor
from automator import Automator


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
        print("Erros de validação:")
        for erro in resultado["erros"]:
            print(f"  - {erro}")
        return

    # 3. Monitoramento
    def ao_mudar(antigo, novo):
        print(f"\n>>> Mudança detectada: {antigo:,.2f} → {novo:,.2f}\n")

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
    )


if __name__ == "__main__":
    main()
