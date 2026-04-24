import tkinter as tk
from tkinter import messagebox


class UI:
    def __init__(self):
        self.nome_usuario: str = ""
        self.item_buscar: str = ""
        self.url: str = ""

        self._root = tk.Tk()
        self._root.title("Monitor de Leilão")
        self._root.resizable(False, False)
        self._construir()

    def _construir(self):
        frame = tk.Frame(self._root, padx=20, pady=20)
        frame.pack()

        tk.Label(frame, text="Nome de usuário").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._entry_nome = tk.Entry(frame, width=40)
        self._entry_nome.grid(row=1, column=0, pady=(0, 12))

        tk.Label(frame, text="Elemento a buscar").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self._entry_item = tk.Entry(frame, width=40)
        self._entry_item.grid(row=3, column=0, pady=(0, 12))

        tk.Label(frame, text="Link da página").grid(row=4, column=0, sticky="w", pady=(0, 4))
        self._entry_url = tk.Entry(frame, width=40)
        self._entry_url.grid(row=5, column=0, pady=(0, 20))

        tk.Button(frame, text="Iniciar monitoramento", command=self._confirmar).grid(row=6, column=0)

    def _confirmar(self):
        nome = self._entry_nome.get().strip()
        item = self._entry_item.get().strip()
        url  = self._entry_url.get().strip()

        if not nome or not item or not url:
            messagebox.showerror("Campos obrigatórios", "Preencha todos os campos antes de continuar.")
            return

        self.nome_usuario = nome
        self.item_buscar  = item
        self.url          = url
        self._root.destroy()

    def executar(self) -> dict:
        self._root.mainloop()
        return {
            "nome_usuario": self.nome_usuario,
            "item_buscar" : self.item_buscar,
            "url"         : self.url,
        }
