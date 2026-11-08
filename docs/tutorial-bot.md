# Tutorial: sube tu primer bot

En este tutorial crearás un bot que juega a Hex y lo enviarás a nuestro repositorio con un *pull request* (PR). Cuando lo aceptemos, tu bot aparecerá en la **[web](https://hex-arena-cunef.streamlit.app)** para que cualquiera juegue contra él, y competirá en el **[torneo](https://monianzola.github.io/HEX/)**.

**Solo tienes que crear un archivo de Python.** No hace falta tocar nada del juego.

Hay dos caminos. Elige uno:

| | Camino A: desde el navegador | Camino B: en tu ordenador |
|---|---|---|
| Qué necesitas | Solo una cuenta de GitHub | Python 3.10+ y Git instalados |
| Cómo se prueba el bot | Nuestro CI lo prueba solo al abrir el PR | Lo pruebas tú antes, con un comando |
| Tiempo | ~10 minutos | ~20 minutos la primera vez |
| Recomendado si… | Quieres subirlo rápido | Quieres probar y mejorar tu bot jugando partidas |

---

## Paso 1: escribe tu bot

Este es un bot completo que ya funciona. Cópialo y cambia las líneas marcadas con `<-- CAMBIA ESTO`:

```python title="mi_bot.py"
from __future__ import annotations

from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.bots.heuristics import center_distance, evaluate, with_stone


@register_bot("mi-bot")  # <-- CAMBIA ESTO: nombre único, en minúsculas.
class MiBot(Bot):  # <-- CAMBIA ESTO: nombre de la clase.
    name = "MiBot"
    author = "Nombre Apellido, Nombre Apellido"  # <-- CAMBIA ESTO: vuestros nombres.
    description = "Greedy: juega la casilla que más acorta su camino y más alarga el del rival."

    def choose_move(self, observation: Observation) -> Move:
        board = observation.board  # board[fila][columna]: 0 vacía, 1 Rojo, 2 Azul
        me = observation.player  # 1 = Rojo (arriba-abajo), 2 = Azul (izquierda-derecha)

        def score(move: Move) -> tuple[float, float]:
            value = evaluate(with_stone(board, move, me), me)  # Más alto = mejor para mí.
            return value, -center_distance(move, observation.size)

        return max(observation.legal_moves, key=score)
```

La misma plantilla está en el repositorio: [`src/hexarena/bots/_plantilla.py`](https://github.com/monianzola/HEX/blob/main/src/hexarena/bots/_plantilla.py).

### Qué recibe tu bot

En cada turno se llama a `choose_move(observation)`. Tiene que devolver una tupla `(fila, columna)` que esté en `observation.legal_moves`.

| Campo | Qué es |
|---|---|
| `observation.board` | El tablero: `board[fila][columna]` vale `0` (vacía), `1` (Rojo) o `2` (Azul) |
| `observation.size` | Lado del tablero, N (7 en el torneo) |
| `observation.player` | Tu color: `1` = Rojo, une **arriba con abajo**; `2` = Azul, une **izquierda con derecha** |
| `observation.legal_moves` | Todas las casillas libres, como tuplas `(fila, columna)` |
| `observation.time_limit` | Segundos que tienes para responder (1 en el torneo) |

### Las reglas de la plataforma

- El nombre de `@register_bot("...")` es **único** y en minúsculas, por ejemplo `"greedy-ana-luis"`.
- `name` y `description` no están vacíos.
- El nombre del archivo va en minúsculas, sin espacios, guiones ni tildes: `greedy_ana_luis.py`.
- Siempre devuelve una jugada de `observation.legal_moves`.
- Responde en menos de `observation.time_limit` segundos.
- No usa internet, ni archivos, ni librerías externas (solo Python estándar y `hexarena`).

Si tu bot falla, se cuelga o hace una jugada ilegal, **pierde esa partida**, pero no rompe el torneo.

---

## Paso 2 (camino A): súbelo desde el navegador

**1. Haz un fork.** Entra en [github.com/monianzola/HEX](https://github.com/monianzola/HEX) y pulsa **Fork** (arriba a la derecha), luego **Create fork**. Ahora tienes tu propia copia en `github.com/TU_USUARIO/HEX`.

**2. Crea el archivo en tu fork.**

1. En tu fork, entra en las carpetas `src` → `hexarena` → `bots`.
2. Pulsa **Add file** → **Create new file**.
3. Escribe el nombre del archivo, por ejemplo `greedy_ana_luis.py`.
4. Pega el código de tu bot.

**3. Guárdalo en una rama nueva.**

1. Pulsa **Commit changes…**.
2. Mensaje: `feat(bots): add GreedyAnaLuis`.
3. Elige **Create a new branch for this commit and start a pull request**.
4. Pulsa **Propose changes**.

**4. Abre el pull request.** GitHub te lleva a la página *Open a pull request*. Comprueba que arriba pone **base repository: `monianzola/HEX`**, **base: `main`**. Cuenta en la descripción qué hace tu bot y pulsa **Create pull request**.

**5. Mira el resultado de los tests.** Al final del PR aparecerán las comprobaciones automáticas (*Tests (Python 3.10)*, etc.):

- 🟡 **"Waiting for approval"** o **"workflows awaiting approval"**: es normal la primera vez. Uno de nosotros pulsa *Approve and run* y empiezan.
- ✅ **Todo verde**: tu bot cumple las reglas. Lo revisamos y lo fusionamos.
- ❌ **Algo en rojo**: pulsa **Details** y busca la línea que pone `FAILED`, que dice qué falló (ver [Problemas frecuentes](#problemas-frecuentes)). Para corregirlo, abre tu archivo en tu fork (en la rama del PR), pulsa el lápiz ✏️, edítalo y haz **Commit changes**. **El PR se actualiza solo** y los tests se vuelven a ejecutar.

---

## Paso 2 (camino B): pruébalo en tu ordenador

**1. Haz un fork** como en el camino A. Después clónalo e instala el proyecto:

```bash
git clone https://github.com/TU_USUARIO/HEX.git
cd HEX
python -m venv .venv
```

=== "Windows (PowerShell)"

    ```powershell
    .venv\Scripts\python.exe -m pip install -e ".[dev]"
    ```

    En Windows usa siempre `.venv\Scripts\python.exe` en lugar de `python`. Así no hace falta "activar" el entorno, que PowerShell suele bloquear.

=== "Linux / macOS"

    ```bash
    source .venv/bin/activate
    pip install -e ".[dev]"
    ```

**2. Crea una rama y tu archivo** en `src/hexarena/bots/` (por ejemplo, copiando `_plantilla.py`):

```bash
git switch -c bot/greedy-ana-luis
```

**3. Compruébalo** con el nombre que pusiste en `@register_bot`:

```bash
python -m hexarena.check greedy-ana-luis
```

```text
Comprobando el bot 'greedy-ana-luis'

  ✅ Se carga correctamente (hexarena.bots.greedy_ana_luis.GreedyAnaLuis)
  ✅ Se crea sin argumentos
  ✅ Tiene nombre: 'GreedyAnaLuis'
  ✅ Tiene descripción: 'Greedy: juega la casilla que ...'
  ✅ tablero vacío 7x7: juega (3, 3) en 0.01 s
  ...
  ℹ️ Contra RandomBot: 4 de 4 partidas ganadas (7x7, 1 s)
  ℹ️ Contra ShortestPathBot: 2 de 4 partidas ganadas (7x7, 1 s)

✅ Todo correcto: tu bot cumple las reglas. ¡Ya puedes abrir el pull request!
```

Puedes jugar contra tu bot en la web local con `streamlit run app/app.py` (antes, `pip install -e ".[web]"`). Si quieres, ejecuta también los mismos tests que el CI: `pytest tests/test_bots_contract.py -k greedy-ana-luis`.

**4. Súbelo y abre el PR:**

```bash
git add src/hexarena/bots/greedy_ana_luis.py
git commit -m "feat(bots): add GreedyAnaLuis"
git push -u origin bot/greedy-ana-luis
```

En GitHub aparecerá **Compare & pull request**. Púlsalo y crea el PR hacia `monianzola/HEX`, rama `main`.

---

## Paso 3: qué pasa después

1. Revisamos tu código: que se entiende, que no hace nada peligroso y que pasa los tests.
2. Si hay que cambiar algo, te dejamos un comentario en el PR.
3. Cuando lo fusionamos, tu bot aparece en el selector de rivales de la **[web](https://hex-arena-cunef.streamlit.app)**, y el **[torneo](https://monianzola.github.io/HEX/)** se vuelve a jugar automáticamente con él.

---

## Ideas de bots con lo visto en clase

Te damos hechas estas funciones en `hexarena.bots.heuristics`:

| Función | Qué hace |
|---|---|
| `shortest_path_distance(board, player)` | Cuántas fichas le faltan a `player` para ganar. Es un camino mínimo (BFS/Dijkstra): casilla propia = 0, vacía = 1, rival = muro |
| `evaluate(board, player)` | `distancia del rival − distancia propia`: más alto es mejor para `player` |
| `with_stone(board, move, player)` | Copia del tablero con una ficha más (para "imaginar" jugadas) |
| `center_distance(move, size)` | Distancia de una casilla al centro |

Cuatro estrategias, de más fácil a más difícil:

**1. Heurística simple.** Jugar la casilla más cercana al centro, o junto a tu última ficha.

**2. Greedy.** Probar todas las jugadas y quedarse con la de mejor `evaluate`. Es lo que hace la plantilla.

**3. Defensa primero.** Si el rival está a 1 ficha de ganar, tapar esa casilla:

```python
from hexarena.bots.heuristics import shortest_path_distance, with_stone

rival = 3 - me
for move in observation.legal_moves:
    if shortest_path_distance(with_stone(board, move, rival), rival) == 0:
        return move  # El rival ganaría ahí: lo tapamos.
```

**4. Minimax (maximin) a 2 jugadas con poda alfa-beta.** Para cada jugada mía, suponer que el rival responde con su mejor jugada, y quedarme con la jugada cuyo peor caso sea el mejor. Si va lento, limita las jugadas que miras a las 10 o 15 mejores según `evaluate`.

Puedes ver bots completos en la carpeta [`src/hexarena/bots/`](https://github.com/monianzola/HEX/tree/main/src/hexarena/bots): `random_bot.py` (el más simple), `shortest_path.py` (greedy) y `alpha_beta.py` (minimax con poda).

---

## Problemas frecuentes

| Qué ves | Qué significa | Solución |
|---|---|---|
| `No bot named 'xxx'` / `No se encuentra el bot` | El nombre no coincide | Usa el nombre de `@register_bot("...")`, no el del archivo |
| `Some bot files failed to import` | Tu archivo tiene un error de Python | `python -m hexarena.check tu-bot` muestra el error y la línea |
| `Bot name 'xxx' is already used` | Otro bot ya usa ese nombre | Cambia el nombre de `@register_bot` |
| `returned illegal move` | Devuelves una casilla ocupada o fuera del tablero | Devuelve siempre algo de `observation.legal_moves` |
| `took 1.4s with a time limit of 0.5s` | Tu bot es demasiado lento | Mira menos jugadas o usa `time.perf_counter()` para parar a tiempo |
| `test_bot_has_name_and_description` | Falta `name` o `description` | Rellena los dos atributos de la clase |
| `ModuleNotFoundError: No module named 'numpy'` (u otra) | Usas una librería que no está instalada | Usa solo Python estándar y `hexarena` |
| El PR dice *"This branch is out-of-date"* | Han entrado otros cambios en `main` | No hagas nada: lo actualizamos nosotros con **Update branch** |
| `git` o `python` "no se reconoce" | No están instalados o falta reiniciar la terminal | Instálalos y vuelve a abrir la terminal, o usa el camino A |

¿Algo no funciona? Abre un [issue](https://github.com/monianzola/HEX/issues) o pregúntanos en el PR.
