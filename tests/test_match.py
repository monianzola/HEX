"""Tests for play_game: full games played from code without an interface."""

from __future__ import annotations

import random

import pytest

from hexarena.game import BLUE, RED, HexGame, IllegalMoveError, Move, Observation, find_winner, play_game


class RandomPlayer:
    """Minimal test player: picks a random legal move."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.seen_players: set[int] = set()

    def choose_move(self, observation: Observation) -> Move:
        self.seen_players.add(observation.player)
        return self.rng.choice(observation.legal_moves)


class FixedPlayer:
    """Plays a predefined list of moves."""

    def __init__(self, moves: list[Move]) -> None:
        self.moves = iter(moves)

    def choose_move(self, observation: Observation) -> Move:
        return next(self.moves)


@pytest.mark.parametrize("size", [1, 3, 5, 7, 11])
def test_play_game_with_two_random_players(size: int) -> None:
    red, blue = RandomPlayer(1), RandomPlayer(2)
    result = play_game(HexGame(size), red, blue)

    assert result.winner in (RED, BLUE)
    assert result.winner == find_winner(result.final_state.board)
    assert len(result.moves) == len(set(result.moves))  # No cell played twice.
    # The history reproduces the final board, alternating Red and Blue.
    for i, (r, c) in enumerate(result.moves):
        assert result.final_state.board[r][c] == (RED if i % 2 == 0 else BLUE)
    assert red.seen_players == {RED}
    assert size == 1 or blue.seen_players == {BLUE}


def test_play_game_is_deterministic_with_fixed_seeds() -> None:
    first = play_game(HexGame(7), RandomPlayer(10), RandomPlayer(20))
    second = play_game(HexGame(7), RandomPlayer(10), RandomPlayer(20))
    assert first == second


def test_play_game_many_random_games() -> None:
    game = HexGame(5)
    winners = {play_game(game, RandomPlayer(s), RandomPlayer(s + 1000)).winner for s in range(100)}
    assert winners == {RED, BLUE}  # Both colours win at least once.


def test_play_game_scripted_blue_win() -> None:
    red = FixedPlayer([(0, 0), (0, 1), (2, 2)])
    blue = FixedPlayer([(1, 0), (1, 1), (1, 2)])
    result = play_game(HexGame(3), red, blue)
    assert result.winner == BLUE
    assert result.moves == ((0, 0), (1, 0), (0, 1), (1, 1), (2, 2), (1, 2))


def test_play_game_passes_time_limit_to_players() -> None:
    limits: list[float] = []

    class Spy(RandomPlayer):
        def choose_move(self, observation: Observation) -> Move:
            limits.append(observation.time_limit)
            return super().choose_move(observation)

    play_game(HexGame(3), Spy(0), Spy(1), time_limit=0.25)
    assert limits and all(t == 0.25 for t in limits)


def test_play_game_propagates_illegal_moves() -> None:
    cheater = FixedPlayer([(0, 0), (0, 0)])
    with pytest.raises(IllegalMoveError):
        play_game(HexGame(3), RandomPlayer(0), cheater)
