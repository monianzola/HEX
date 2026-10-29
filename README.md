# ⬢ hex-arena

[![Tests](https://github.com/monianzola/HEX/actions/workflows/tests.yml/badge.svg)](https://github.com/monianzola/HEX/actions/workflows/tests.yml)
[![Documentación](https://readthedocs.org/projects/hex-arena-cunef/badge/?version=latest)](https://hex-arena-cunef.readthedocs.io/es/latest/)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)

Motor del juego **Hex** en Python, plataforma abierta de bots y torneo automático entre ellos.

| | |
|---|---|
| ▶️ **Jugar en la web** | _Próximamente_ (Streamlit Community Cloud) |
| 📖 **Documentación** | [hex-arena-cunef.readthedocs.io](https://hex-arena-cunef.readthedocs.io/es/latest/) |
| 🏆 **Clasificación del torneo** | [monianzola.github.io/HEX](https://monianzola.github.io/HEX/) (GitHub Pages, se actualiza sola) |

## Qué incluye

- **Librería `hexarena`**: las reglas de Hex, instalable con `pip` y jugable desde código sin interfaz. Sin dependencias externas.
- **Interfaz web** con Streamlit: juegas con Rojo contra el bot que elijas, sobre un tablero hexagonal clicable.
- **Plataforma de bots**: cualquiera puede añadir un bot creando **un único archivo**. Unos tests automáticos validan cualquier bot nuevo.
- **Torneo automático** round-robin entre todos los bots, con clasificación Elo publicada automáticamente.

## Reglas de Hex

Hex se juega por turnos en un tablero de N×N casillas hexagonales (11×11 por defecto) con forma de rombo.

- 🔴 **Rojo** (jugador `1`) **empieza** y quiere unir el borde de **arriba** con el de **abajo**.
- 🔵 **Azul** (jugador `2`) quiere unir el borde de la **izquierda** con el de la **derecha**.
- En cada turno se coloca una ficha en una casilla vacía. Las fichas no se mueven nunca.
- Gana quien forme primero una cadena continua entre sus dos bordes. **Nunca hay empate.**

Cada casilla `(fila, columna)` tiene hasta 6 vecinas: `(r-1,c)`, `(r-1,c+1)`, `(r,c-1)`, `(r,c+1)`, `(r+1,c-1)` y `(r+1,c)`. Más detalles en las [reglas completas](https://hex-arena-cunef.readthedocs.io/es/latest/reglas/).

## Instalación

Requiere **Python 3.10 o superior**.

```bash
git clone https://github.com/monianzola/HEX.git
cd HEX
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"         # librería + herramientas de test
pytest                          # comprueba que todo funciona
```

Extras opcionales: `web` (Streamlit), `docs` (MkDocs) y `dev` (pytest). Se pueden combinar: `pip install -e ".[dev,web,docs]"`.

## Jugar desde código

```python
from hexarena.bots.random_bot import RandomBot
from hexarena.bots.shortest_path import ShortestPathBot
from hexarena.game import HexGame, play_game

game = HexGame(size=7)
result = play_game(game, ShortestPathBot(), RandomBot(seed=1))  # Rojo, Azul

print("Ganador:", "Rojo" if result.winner == 1 else "Azul")
print(game.render_ascii(result.final_state))
```

O jugada a jugada:

```python
from hexarena.game import HexGame

game = HexGame(size=5)
state = game.initial_state()
state = game.play(state, (2, 2))     # Rojo juega en el centro
print(game.legal_moves(state)[:3])   # [(0, 0), (0, 1), (0, 2)]
print(game.current_player(state))    # 2 (turno de Azul)
```

## Jugar en la web

```bash
pip install -e ".[web]"
streamlit run app/app.py
```

Se abre el navegador en `http://localhost:8501`. Tú juegas con Rojo y empiezas. Puedes elegir el tamaño del tablero (5–11) y el bot rival.

## Crear tu propio bot

Crea **un solo archivo** en `src/hexarena/bots/`. El registro lo descubre automáticamente: no hace falta tocar nada más.

```python
# src/hexarena/bots/center_bot.py
from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.bots.heuristics import center_distance


@register_bot("center")
class CenterBot(Bot):
    name = "CenterBot"
    author = "Tu nombre"
    description = "Juega la casilla libre más cercana al centro."

    def choose_move(self, observation: Observation) -> Move:
        return min(observation.legal_moves, key=lambda m: center_distance(m, observation.size))
```

Valídalo con los tests de contrato, que se aplican solos a todos los bots registrados:

```bash
pytest tests/test_bots_contract.py -k center
```

Guía completa: **[Tutorial: sube tu primer bot](https://hex-arena-cunef.readthedocs.io/es/latest/tutorial-bot/)**.

## Bots incluidos

| Bot | Registro | Estrategia |
|---|---|---|
| `RandomBot` | `random` | Jugada legal al azar. Sirve de referencia mínima. |
| `ShortestPathBot` | `shortest-path` | Para cada jugada calcula con 0-1 BFS cuántas fichas le faltan a cada jugador, y maximiza *distancia del rival − distancia propia*. |
| `AlphaBetaBot` | `alpha-beta` | Minimax con poda alfa-beta y profundización iterativa (80 % del tiempo), 20 candidatos por nodo ordenados por cercanía a los caminos más cortos. Gana el 85 % de las partidas a `ShortestPathBot`. |
| `MCTSBot` | `mcts` | Monte Carlo Tree Search (UCT, c = √2): ~9 000 simulaciones por jugada en 7×7 rellenando el tablero al azar. Gana el 80 % a `ShortestPathBot` y empata con `AlphaBetaBot` (45 %). |

## Torneo

Todos los bots registrados se enfrentan entre sí (round-robin) en tablero **7×7**, **20 partidas por pareja** (10 con cada color), **1 segundo por movimiento** y semilla fija. La clasificación usa **Elo** (inicial 1000, K = 32).

```bash
python -m hexarena.tournament                       # torneo oficial -> results/index.html
python -m hexarena.tournament --bots random shortest-path --games 4 --size 5
```

Cada bot se ejecuta en **su propio proceso**: si lanza una excepción, se pasa de tiempo, se cuelga o juega ilegalmente, **pierde esa partida** y el torneo continúa. GitHub Actions lo ejecuta en cada push a `main`, cada lunes y a mano, y publica la [clasificación](https://monianzola.github.io/HEX/) en GitHub Pages.

Para enfrentar a todos los bots entre sí y ver la tabla de enfrentamientos directos:

```bash
python scripts/compare_bots.py                    # 7x7, 20 partidas por pareja, 1 s por jugada
python scripts/compare_bots.py --games 6 --time-limit 0.5
```

## Estructura del repositorio

```
HEX/
├── src/hexarena/
│   ├── game/          # Reglas, estado inmutable, detección de victoria, play_game
│   ├── bots/          # API pública (Bot, registro) y un archivo por bot
│   └── tournament/    # Torneo round-robin robusto, ranking Elo y página de clasificación
├── app/               # Interfaz web Streamlit (app.py) y dibujo del tablero
├── tests/             # Tests con pytest
├── docs/              # Documentación MkDocs (publicada en ReadTheDocs)
├── .github/           # Workflows de CI y plantillas de pull request
├── pyproject.toml     # Empaquetado y dependencias
└── requirements.txt   # Dependencias para Streamlit Community Cloud
```

## Contribuir

Trabajamos con ramas y pull requests: `main` está protegida y cada PR necesita una revisión y que pase el CI. Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de empezar.

## Autores

<!-- Rellenar a mano: nombre completo y usuario de GitHub de cada integrante. -->

- Mónica Anzola Valero de Bernabé
- Cristina Colunga Martínez

## Licencia

Distribuido bajo licencia **MIT**. Consulta [LICENSE](LICENSE).
