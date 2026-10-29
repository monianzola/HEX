# hex-arena

**hex-arena** es un proyecto open-source en Python sobre el juego de tablero **Hex**. Incluye:

- **Una librería instalable** (`hexarena`) con las reglas de Hex, que se puede usar desde código sin ninguna interfaz.
- **Una interfaz web** con Streamlit para jugar contra los bots desde el navegador.
- **Una plataforma de bots**: cualquiera puede añadir su propio bot creando **un único archivo**, sin tocar el código del juego.
- **Un torneo automático** entre todos los bots del repositorio, con clasificación Elo.

## Empieza aquí

| Quiero… | Ve a |
|---|---|
| Entender cómo se juega | [Reglas de Hex](reglas.md) |
| Instalar la librería | [Instalación](instalacion.md) |
| Programar mi propio bot | [Tutorial: sube tu primer bot](tutorial-bot.md) |
| Consultar clases y funciones | [Referencia del API](api/game.md) |
| Ver cómo funciona el torneo | [Torneo y clasificación](torneo.md) |
| Colaborar en el proyecto | [Contribuir](contribuir.md) |

## Un vistazo rápido

```python
from hexarena.bots.random_bot import RandomBot
from hexarena.bots.shortest_path import ShortestPathBot
from hexarena.game import HexGame, play_game

game = HexGame(size=7)
result = play_game(game, ShortestPathBot(), RandomBot(seed=1))

print("Ganador:", "Rojo" if result.winner == 1 else "Azul")
print("Jugadas:", len(result.moves))
print(game.render_ascii(result.final_state))
```

## Enlaces

- ▶️ Jugar en la web: [hex-arena-cunef.streamlit.app](https://hex-arena-cunef.streamlit.app)
- 🏆 Clasificación del torneo: [monianzola.github.io/HEX](https://monianzola.github.io/HEX/)
- Código fuente: [github.com/monianzola/HEX](https://github.com/monianzola/HEX)
- Licencia: MIT
