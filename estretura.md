auction-assistant/
├── src/
│   ├── monitor.py        # Lógica de scraping e detecção
│   ├── automator.py      # Interação com 2ª página (Gmail)
│   ├── logger.py         # Log de ações do usuário
│   ├── validator.py      # Validações (URL, timeout, campo numérico)
│   └── ui.py             # Interface (Streamlit ou Tkinter)
├── tests/
│   └── test_*.py         # Testes unitários com pytest
├── docs/                 # MkDocs
├── main.py
└── requirements.txt