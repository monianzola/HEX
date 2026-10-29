# Cómo contribuir a hex-arena

¡Gracias por colaborar! Esta guía resume cómo trabajamos. La versión ampliada está en la [documentación](https://hex-arena-cunef.readthedocs.io/es/latest/contribuir/).

## 1. Prepara el entorno

```bash
git clone https://github.com/monianzola/HEX.git
cd HEX
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"
pytest
```

Si no tienes permisos de escritura en el repositorio, haz antes un **fork** y clona tu copia.

## 2. Crea una rama

`main` está protegida: nunca se sube nada directamente.

| Tipo de cambio | Nombre de la rama |
|---|---|
| Funcionalidad nueva | `feature/descripcion-corta` |
| Corrección | `fix/descripcion-corta` |
| Bot nuevo | `bot/nombre-del-bot` |
| Documentación | `docs/descripcion-corta` |

```bash
git switch main
git pull
git switch -c feature/descripcion-corta
```

## 3. Haz commits con Conventional Commits

```
<tipo>(<ámbito opcional>): <descripción en imperativo>
```

| Tipo | Uso | Ejemplo |
|---|---|---|
| `feat` | Funcionalidad nueva | `feat(bots): add MCTSBot` |
| `fix` | Corrección | `fix(game): reject boolean coordinates` |
| `test` | Tests | `test(game): cover 1x1 board` |
| `docs` | Documentación | `docs: add bot tutorial` |
| `refactor` | Cambio interno sin cambiar el comportamiento | `refactor(bots): extract heuristics module` |
| `chore` | Mantenimiento | `chore: update dependencies` |

## 4. Antes de abrir el pull request

- [ ] `pytest` pasa en local.
- [ ] El código nuevo tiene **type hints** y **docstrings** en estilo Google (`Args:`, `Returns:`, `Raises:`).
- [ ] Hay tests para lo nuevo.
- [ ] Si cambia el API público, la documentación en `docs/` está actualizada.

## 5. Abre el pull request

```bash
git push -u origin feature/descripcion-corta
```

En GitHub, pulsa **Compare & pull request** y rellena la plantilla. Si es un bot, añade `?template=bot.md` a la URL del PR para usar la plantilla de bots.

- El CI ejecuta los tests en Python 3.10, 3.11 y 3.12.
- Hace falta **al menos una aprobación** de otra persona del equipo.
- Quien revisa comprueba que el código se entiende, está probado y no rompe nada.

## Añadir un bot

Sigue el [tutorial](https://hex-arena-cunef.readthedocs.io/es/latest/tutorial-bot/). Requisitos:

- **Un único archivo** en `src/hexarena/bots/`, registrado con `@register_bot("nombre-unico")`.
- Se puede crear sin argumentos y tiene `name` y `description`.
- Pasa los tests de contrato: `pytest tests/test_bots_contract.py -k nombre-unico`.
- Responde dentro de `observation.time_limit`.
- **No** accede a la red ni a archivos, **no** lanza procesos y **no** modifica nada fuera de sí mismo.
- Es claramente mejor que `RandomBot`.

## Estilo de código

- Python 3.10+, type hints en todas las funciones públicas.
- La lógica del juego (`hexarena.game`) no depende de los bots ni de la web.
- La librería no añade dependencias externas: solo la librería estándar. Streamlit, Pillow y MkDocs van en extras opcionales.

## Reportar un problema

Abre un *issue* indicando los pasos para reproducirlo, qué esperabas y qué pasó.
