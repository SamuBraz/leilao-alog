# Big O do sistema

## Variáveis

- **N** = número de iframes na página
- **P** = elementos DOM por iframe
- **E** = elementos que contém o texto buscado
- **D** = descendentes por nó DOM

---

## Módulo por módulo

**ui.py** → O(1)
widgets fixos, sem loop

**validate.py** → O(1)
só comparações de string e um page load com timeout fixo

**monitor.buscar_elemento()** → O(N × P)
percorre cada iframe e busca todos os elementos com o texto

**monitor.buscar_valor()** → O(E × D)
pra cada elemento encontrado, sobe 5 níveis no DOM checando os filhos

**monitor.monitorar()** → O((T/I) × (N + P))
loop de no máximo 5 iterações (50s / 10s), cada uma relê os iframes

**automator.py** → O(1)
histórico tem no máximo 2 entradas, 6 seletores fixos

---

## Resultado geral

**O(N × P)** na busca inicial, **O(N + P)** por iteração do loop.

O tempo real é dominado pelo Selenium e latência de rede, não pelo algoritmo em si.
