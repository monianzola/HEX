# Tutorial: sube tu primer bot

En este tutorial crearás un bot de Hex, comprobarás que cumple las reglas de la plataforma y lo enviarás al repositorio con un *pull request*. Al fusionarse, tu bot aparecerá automáticamente en la **web** y en el **torneo**.

**Solo tendrás que crear un archivo.** No hace falta tocar el código del juego, ni el torneo, ni la web.

## 1. Haz un fork y clónalo

1. Entra en [github.com/monianzola/HEX](https://github.com/monianzola/HEX) y pulsa **Fork**. Así tendrás tu propia copia del repositorio en tu cuenta.
2. Clona tu fork e instala el proyecto con las herramientas de desarrollo:

```bash
git clone https://github.com/TU_USUARIO/HEX.git
cd HEX
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1     Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest            # Todo debe pasar antes de empezar
```

## 2. Crea una rama

Nunca trabajes directamente en `main`:

```bash
git switch -c bot/center-bot
```

## 3. Escribe tu bot

Crea el archivo `src/hexarena/bots/center_bot.py`:

```python title="src/hexarena/bots/center_bot.py"
"""CenterBot: plays the free cell closest to the centre of the board."""

from __future__ import annotations

from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.bots.heuristics import center_distance


@register_bot("center")  # (1)!
class CenterBot(Bot):
    """Always plays the empty cell closest to the centre."""

    name = "CenterBot"  # (2)!
    author = "Tu nombre"
    description = "Juega la casilla libre más cercana al centro."

    def choose_move(self, observation: Observation) -> Move:  # (3)!
        return min(
            observation.legal_moves,
            key=lambda move: center_distance(move, observation.size),
        )
```

1. Identificador **único** del bot. El torneo y la web lo usan para encontrarlo.
2. Nombre visible, autor y descripción. `name` y `description` son **obligatorios**: los tests lo comprueban.
3. El único método obligatorio. Recibe una `Observation` y devuelve una tupla `(fila, columna)`.

### Qué recibes en `observation`

| Campo | Tipo | Significado |
|---|---|---|
| `board` | `tuple[tuple[int, ...], ...]` | Tablero: `0` vacía, `1` Rojo, `2` Azul. `board[fila][columna]` |
| `size` | `int` | Lado N del tablero |
| `player` | `int` | Tu color: `1` (Rojo, arriba-abajo) o `2` (Azul, izquierda-derecha) |
| `legal_moves` | `tuple[tuple[int, int], ...]` | Todas las casillas libres |
| `time_limit` | `float` | Segundos que tienes para responder |

### Reglas que debe cumplir tu bot

- Se crea **sin argumentos**: `CenterBot()`. Si necesitas parámetros, dales valores por defecto.
- Devuelve **siempre** una jugada de `observation.legal_moves`.
- Responde dentro de `observation.time_limit`. Un buen margen es usar como mucho el 80 %.
- **No** modifica la observación, **no** accede a la red ni a archivos y **no** usa variables globales compartidas.

!!! tip "Herramientas que puedes reutilizar"
    - `hexarena.bots.heuristics.shortest_path_distance(board, player)`: cuántas fichas le faltan a un jugador para conectar.
    - `hexarena.bots.heuristics.evaluate(board, player)`: puntuación de una posición (más alta es mejor).
    - `hexarena.game.HexGame`: puedes simular jugadas con `HexGame(size).play(state, move)`.

    Consulta la [Referencia del API](api/bots.md).

## 4. Pruébalo

Primero, a mano:

```python
from hexarena.bots.center_bot import CenterBot
from hexarena.bots.random_bot import RandomBot
from hexarena.game import HexGame, play_game

result = play_game(HexGame(7), CenterBot(), RandomBot(seed=0))
print("Gana", "Rojo" if result.winner == 1 else "Azul")
```

Después, con los **tests de contrato**. Se aplican automáticamente a **todos** los bots registrados, así que tu bot ya está incluido sin escribir ningún test:

```bash
pytest tests/test_bots_contract.py -k center -v
```

Comprueban que tu bot:

- se puede crear sin argumentos y tiene `name` y `description`;
- devuelve una jugada legal en 7 posiciones distintas (inicio, mitad de partida, casi final, una sola casilla libre…);
- responde a tiempo;
- no modifica la observación;
- termina una partida 5×5 contra `RandomBot` jugando con Rojo y con Azul.

Por último, ejecuta **todos** los tests para asegurarte de que no has roto nada:

```bash
pytest
```

!!! note "Tests propios (recomendado)"
    Si tu bot tiene lógica interesante, añade `tests/test_center_bot.py` con casos concretos, por ejemplo que en un tablero vacío juega el centro.

## 5. Envía el pull request

```bash
git add src/hexarena/bots/center_bot.py
git commit -m "feat(bots): add CenterBot"
git push -u origin bot/center-bot
```

En GitHub aparecerá el botón **Compare & pull request**. En la descripción del PR indica:

- qué algoritmo usa tu bot y por qué;
- cómo le va contra `RandomBot` y `ShortestPathBot`;
- que `pytest` pasa en local.

El CI ejecutará los tests automáticamente. Una persona del equipo revisará el código y, si todo está bien, lo fusionará.

## 6. ¿Y después?

Cuando el PR se fusiona en `main`:

- tu bot aparece en el selector de oponentes de la **web**;
- participa en el próximo **torneo** y sale en la [clasificación](torneo.md).

Ideas para mejorar tu bot: búsqueda Minimax con poda alfa-beta, Monte Carlo Tree Search (MCTS), o una heurística que reconozca **puentes** (dos fichas con dos vecinas libres en común, que el rival no puede cortar).
