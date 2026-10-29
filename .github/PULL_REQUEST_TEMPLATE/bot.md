## Nuevo bot: <!-- NombreDelBot -->

**Archivo:** `src/hexarena/bots/<!-- archivo -->.py`
**Nombre de registro:** `<!-- nombre-en-register_bot -->`
**Autor/es:** <!-- nombre y usuario de GitHub -->

## Algoritmo

<!-- Explica cómo elige la jugada: heurística, búsqueda (minimax, alfa-beta, MCTS...),
     cómo gestiona el tiempo y por qué crees que funciona. -->

## Rendimiento

<!-- Resultados en 7x7 con 1 s por jugada, alternando colores. -->

| Rival | Victorias / partidas |
|---|---|
| RandomBot | / |
| ShortestPathBot | / |

## Checklist

- [ ] El bot está en **un único archivo** y no modifica ningún otro archivo del juego.
- [ ] Se puede crear sin argumentos y define `name`, `author` y `description`.
- [ ] Pasa los tests de contrato: `pytest tests/test_bots_contract.py -k <nombre>`.
- [ ] Pasa **todos** los tests: `pytest`.
- [ ] Responde siempre dentro de `observation.time_limit`.
- [ ] **No** accede a la red ni a archivos, **no** lanza procesos ni usa variables globales compartidas.
- [ ] (Opcional) Incluye tests propios en `tests/test_<nombre>.py`.
