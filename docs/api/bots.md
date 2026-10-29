# Referencia del API: bots

Lo necesario para escribir un bot se importa desde `hexarena.bots`:

```python
from hexarena.bots import Bot, Move, Observation, register_bot
```

El [tutorial](../tutorial-bot.md) explica el proceso completo paso a paso.

## Clase base

::: hexarena.bots.base.Bot

## Registro de bots

::: hexarena.bots.registry
    options:
      show_root_heading: false
      members:
        - register_bot
        - available_bots
        - get_bot
        - create_bot
        - discover_bots
        - discovery_errors
        - unregister_bot

## Heurísticas reutilizables

::: hexarena.bots.heuristics
    options:
      show_root_heading: false
      members:
        - shortest_path_distance
        - evaluate
        - with_stone
        - center_distance
        - distance_map
        - path_slack
        - WIN_SCORE

## Bots incluidos

::: hexarena.bots.random_bot.RandomBot

::: hexarena.bots.shortest_path.ShortestPathBot

::: hexarena.bots.alpha_beta.AlphaBetaBot

::: hexarena.bots.alpha_beta.AlphaBetaSearch

::: hexarena.bots.mcts.MCTSBot

::: hexarena.bots.mcts.ucb1
