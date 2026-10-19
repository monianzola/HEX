# hex-arena

Motor del juego Hex en Python, plataforma de bots y torneo automático.

> README provisional: se completará en el bloque C.1.

## Instalación para desarrollo

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"
pytest
```

## Jugar en la web

▶️ **[Jugar a Hex contra un bot](https://ENLACE-PENDIENTE.streamlit.app)** (Streamlit Community Cloud)

Para ejecutarla en local:

```bash
pip install -e ".[web]"
streamlit run app/app.py
```

## Licencia

MIT. Consulta [LICENSE](LICENSE).
