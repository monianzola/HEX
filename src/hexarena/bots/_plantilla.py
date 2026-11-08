"""PLANTILLA: copia este archivo para crear tu propio bot.

1. Copia este archivo en esta misma carpeta con otro nombre, en minúsculas y
   sin espacios ni guiones, por ejemplo ``mi_bot.py``. (Los archivos que
   empiezan por ``_``, como este, se ignoran: esta plantilla no es un bot.)
2. Cambia las tres líneas marcadas con  <-- CAMBIA ESTO.
3. Escribe tu estrategia dentro de ``choose_move``.

Tutorial completo: https://hex-arena-cunef.readthedocs.io/es/latest/tutorial-bot/
"""

from __future__ import annotations

from hexarena.bots import Bot, Move, Observation, register_bot
from hexarena.bots.heuristics import center_distance, evaluate, with_stone


@register_bot("mi-bot")  # <-- CAMBIA ESTO: nombre único, en minúsculas.
class MiBot(Bot):  # <-- CAMBIA ESTO: nombre de la clase.
    name = "MiBot"
    author = "Nombre Apellido, Nombre Apellido"  # <-- CAMBIA ESTO: vuestros nombres.
    description = "Greedy: juega la casilla que más acorta su camino y más alarga el del rival."

    def choose_move(self, observation: Observation) -> Move:
        """Return the move to play: a tuple ``(row, col)`` from ``legal_moves``.

        Example strategy (greedy, one move ahead): try every legal move and
        keep the one with the best ``evaluate`` score; ties go to the centre.
        """
        board = observation.board  # board[fila][columna]: 0 vacía, 1 Rojo, 2 Azul
        me = observation.player  # 1 = Rojo (arriba-abajo), 2 = Azul (izquierda-derecha)

        def score(move: Move) -> tuple[float, float]:
            value = evaluate(with_stone(board, move, me), me)  # Más alto = mejor para mí.
            return value, -center_distance(move, observation.size)

        return max(observation.legal_moves, key=score)
