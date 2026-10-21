# Referencia del API: juego

Todo lo de esta página se puede importar desde `hexarena.game`:

```python
from hexarena.game import HexGame, HexState, IllegalMoveError, Observation, play_game, RED, BLUE, EMPTY
```

## Reglas

::: hexarena.game.hex_game.HexGame

::: hexarena.game.hex_game.IllegalMoveError

::: hexarena.game.hex_game.neighbors

::: hexarena.game.hex_game.find_winner

## Estado y tipos

::: hexarena.game.state
    options:
      show_root_heading: false
      members:
        - EMPTY
        - RED
        - BLUE
        - Board
        - Move
        - HexState
        - opponent

## Observación

::: hexarena.game.observation.Observation

## Jugar una partida

::: hexarena.game.match.play_game

::: hexarena.game.match.GameResult

::: hexarena.game.match.MoveChooser
