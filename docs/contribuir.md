# Contribuir

¡Gracias por querer colaborar con hex-arena! Esta guía resume cómo trabajamos.

## Flujo de trabajo

1. **Nunca se trabaja directamente en `main`.** La rama `main` está protegida.
2. Crea una rama con un nombre descriptivo:
    - `feature/descripcion-corta` para funcionalidades nuevas;
    - `fix/descripcion-corta` para correcciones;
    - `bot/nombre-del-bot` para bots nuevos.
3. Haz commits pequeños siguiendo [Conventional Commits](https://www.conventionalcommits.org/es/):

    | Prefijo | Uso | Ejemplo |
    |---|---|---|
    | `feat` | Funcionalidad nueva | `feat(bots): add MCTSBot` |
    | `fix` | Corrección de un error | `fix(game): reject boolean coordinates` |
    | `test` | Tests | `test(game): cover 1x1 board` |
    | `docs` | Documentación | `docs: add bot tutorial` |
    | `chore` | Mantenimiento | `chore: update dependencies` |

4. Abre un **pull request** hacia `main`. El CI ejecutará los tests en Python 3.10, 3.11 y 3.12.
5. Otra persona del equipo **revisa** el PR. Hace falta al menos **una aprobación** y que el CI pase para poder fusionar.

## Antes de abrir el PR

- [ ] `pytest` pasa en local.
- [ ] El código nuevo tiene **type hints** y **docstrings** (estilo Google).
- [ ] Hay tests para la funcionalidad nueva.
- [ ] Si cambia el API público, la documentación está actualizada.

## Estilo de código

- Python 3.10+, con type hints en todas las funciones públicas.
- Docstrings en estilo Google: `Args:`, `Returns:`, `Raises:`. Así aparecen en la [referencia del API](api/game.md).
- La lógica del juego (`hexarena.game`) **no depende** de los bots ni de la web.
- La librería no añade dependencias externas: solo librería estándar.

## Añadir un bot

Sigue el [tutorial](tutorial-bot.md). Un bot nuevo debe:

- estar en **un único archivo** en `src/hexarena/bots/`;
- pasar los tests de contrato (`tests/test_bots_contract.py`);
- no acceder a la red ni a archivos, ni ejecutar código peligroso;
- ser razonablemente mejor que `RandomBot`.

## Documentación

```bash
pip install -e ".[docs]"
mkdocs serve
```

Las páginas están en `docs/`. La referencia del API se genera sola a partir de los docstrings con mkdocstrings.

## Reportar un problema

Abre un *issue* en GitHub con los pasos para reproducirlo, lo que esperabas que pasara y lo que pasó en realidad.
