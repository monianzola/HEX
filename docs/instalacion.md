# Instalación

## Requisitos

- **Python 3.10 o superior** (probado en 3.10, 3.11 y 3.12).
- **Git**, para clonar el repositorio.

La librería `hexarena` **no tiene dependencias externas**: solo usa la librería estándar de Python.

## Instalar desde el repositorio

```bash
git clone https://github.com/monianzola/HEX.git
cd HEX
python -m venv .venv
```

Activa el entorno virtual:

=== "Windows (PowerShell)"

    ```powershell
    .venv\Scripts\Activate.ps1
    ```

    Si PowerShell bloquea el script, ejecuta antes
    `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o llama directamente a
    `.venv\Scripts\python.exe` en lugar de `python`.

=== "Linux / macOS"

    ```bash
    source .venv/bin/activate
    ```

Instala el paquete en modo editable:

```bash
pip install -e .
```

## Extras opcionales

| Extra | Para qué | Comando |
|---|---|---|
| `dev` | Ejecutar los tests (pytest, cobertura) | `pip install -e ".[dev]"` |
| `web` | Interfaz web con Streamlit | `pip install -e ".[web]"` |
| `docs` | Generar esta documentación | `pip install -e ".[docs]"` |

Se pueden combinar: `pip install -e ".[dev,web,docs]"`.

## Comprobar que funciona

```bash
python -c "from hexarena.game import HexGame; g = HexGame(5); print(g.render_ascii(g.initial_state()))"
```

Debe aparecer un tablero vacío de 5×5. Para ejecutar los tests:

```bash
pytest
```

## Jugar en la web

La versión publicada está en **[hex-arena-cunef.streamlit.app](https://hex-arena-cunef.streamlit.app)**. Para ejecutarla en local:

```bash
pip install -e ".[web]"
streamlit run app/app.py
```

Se abrirá el navegador en `http://localhost:8501`.

## Generar la documentación en local

```bash
pip install -e ".[docs]"
mkdocs serve
```

Abre `http://127.0.0.1:8000`. La página se recarga sola al editar los archivos de `docs/`.
