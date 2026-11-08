"""Game control for the web app, independent of Streamlit (so it is easy to test).

A :class:`Match` knows who controls each colour (a human or a registered
bot), applies human moves, asks bots for their moves and supports undo.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from hexarena.bots import Bot, create_bot
from hexarena.game import BLUE, EMPTY, RED, HexGame, HexState, IllegalMoveError, Move, opponent

HUMAN = "human"
"""Controller name for a colour played by a person."""

COLOUR_NAMES = {RED: "Rojo", BLUE: "Azul"}


@dataclass
class Match:
    """A game in progress in the web app.

    Attributes:
        size: Side of the board.
        players: Who plays each colour: ``HUMAN`` or a registered bot name.
        time_limit: Seconds each bot may think per move.
    """

    size: int
    players: dict[int, str]
    time_limit: float = 0.25
    game: HexGame = field(init=False)
    state: HexState = field(init=False)
    moves: list[Move] = field(init=False, default_factory=list)
    bots: dict[int, Bot] = field(init=False, default_factory=dict)
    forfeit: str | None = field(init=False, default=None)
    last_think_time: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.game = HexGame(self.size)
        self.state = self.game.initial_state()
        self.bots = {
            colour: create_bot(name) for colour, name in self.players.items() if name != HUMAN
        }

    # ------------------------------------------------------------------ queries

    @property
    def finished(self) -> bool:
        return self.game.is_terminal(self.state)

    @property
    def winner(self) -> int | None:
        return self.game.winner(self.state)

    @property
    def to_move(self) -> int:
        return self.game.current_player(self.state)

    def is_human(self, colour: int) -> bool:
        return self.players[colour] == HUMAN

    @property
    def has_human(self) -> bool:
        return any(self.is_human(colour) for colour in (RED, BLUE))

    def is_human_turn(self) -> bool:
        return not self.finished and self.is_human(self.to_move)

    def is_bot_turn(self) -> bool:
        return not self.finished and not self.is_human(self.to_move)

    def player_name(self, colour: int) -> str:
        """``"Tú"`` for the human, otherwise the bot's display name."""
        return "Tú" if self.is_human(colour) else self.bots[colour].name

    @property
    def last_move(self) -> Move | None:
        return self.moves[-1] if self.moves else None

    # ------------------------------------------------------------------ actions

    def play_human(self, cell: Move) -> str | None:
        """Play ``cell`` for the human. Returns a message if the move is refused."""
        if self.finished:
            return "La partida ha terminado. Pulsa «Nueva partida» para jugar otra."
        if not self.is_human(self.to_move):
            return "Espera: le toca al bot."
        if self.state.board[cell[0]][cell[1]] != EMPTY:
            return f"La casilla {cell} ya está ocupada."
        try:
            self.state = self.game.play(self.state, cell)
        except IllegalMoveError as exc:
            return f"Jugada ilegal: {exc}"
        self.moves.append(cell)
        return None

    def play_bot(self) -> Move | None:
        """Ask the bot whose turn it is for a move and play it.

        A bot that raises or returns an illegal move loses the game
        (the app never crashes because of a bot). Returns the move played.
        """
        if not self.is_bot_turn():
            return None
        colour = self.to_move
        bot = self.bots[colour]
        observation = self.game.observation(self.state, colour, self.time_limit)
        start = time.perf_counter()
        try:
            move = bot.choose_move(observation)
            self.state = self.game.play(self.state, move)
        except Exception as exc:  # noqa: BLE001 - a broken bot must not crash the app
            self.state = HexState(board=self.state.board, to_move=colour, winner=opponent(colour))
            self.forfeit = f"{bot.name} ha fallado ({type(exc).__name__}: {exc}) y pierde la partida."
            return None
        finally:
            self.last_think_time = time.perf_counter() - start
        self.moves.append(move)
        return move

    def can_undo(self) -> bool:
        """There is at least one human move to take back."""
        return any(self.is_human(RED if i % 2 == 0 else BLUE) for i in range(len(self.moves)))

    def undo(self) -> None:
        """Take back moves until the last human move is undone."""
        if not self.can_undo():
            return
        while self.moves:
            colour = RED if (len(self.moves) - 1) % 2 == 0 else BLUE
            self.moves.pop()
            if self.is_human(colour):
                break
        self.state = self.game.initial_state()
        for move in self.moves:
            self.state = self.game.play(self.state, move)
        self.forfeit = None
