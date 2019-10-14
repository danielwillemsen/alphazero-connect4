import numpy as np
import pyspiel
from open_spiel.python.algorithms import mcts
from connect4net import state_to_board

from alphazerobot import AlphaZeroBot, NeuralNetBot
from connect4net import Net


def play_game(game, player1, player2):
    # Returns the reward of the first player
    state = game.new_initial_state()
    while not state.is_terminal():
        if len(state.history()) % 2 == 0:
            _, action = player1.step(state)
        else:
            _, action = player2.step(state)
        state.apply_action(action)
    return state.returns()[0]


def test_zero_vs_random(policy_fn):
    game = pyspiel.load_game('connect_four')

    # Alphazero first
    zero_bot = AlphaZeroBot(game, 0, policy_fn=policy_fn, use_dirichlet=False)
    random_bot = pyspiel.make_uniform_random_bot(game, 1, np.random.randint(0, 1000))
    score1 = play_game(game, zero_bot, random_bot)

    # Random bot first
    zero_bot = AlphaZeroBot(game, 1, policy_fn=policy_fn, use_dirichlet=False)
    random_bot = pyspiel.make_uniform_random_bot(game, 0, np.random.randint(0, 1000))
    score2 = -play_game(game, random_bot, zero_bot)
    return score1, score2


def test_zero_vs_mcts(policy_fn, max_search_nodes, game_name, **kwargs):
    game = pyspiel.load_game(game_name)

    # Alphazero first
    zero_bot = AlphaZeroBot(game, 0, policy_fn=policy_fn, use_dirichlet=False, **kwargs)
    mcts_bot = mcts.MCTSBot(game, 1, 1,
                            max_search_nodes, mcts.RandomRolloutEvaluator(1))
    score1 = play_game(game, zero_bot, mcts_bot)

    # Random bot first
    zero_bot = AlphaZeroBot(game, 1, policy_fn=policy_fn, use_dirichlet=False, **kwargs)
    mcts_bot = mcts.MCTSBot(game, 0, 1,
                            max_search_nodes, mcts.RandomRolloutEvaluator(1))
    score2 = -play_game(game, mcts_bot, zero_bot)
    return score1, score2


def test_net_vs_mcts(policy_fn, max_search_nodes, game_name, **kwargs):
    game = pyspiel.load_game(game_name)

    # Alphazero first
    zero_bot = NeuralNetBot(game, 0, policy_fn)
    mcts_bot = mcts.MCTSBot(game, 1, 1,
                            max_search_nodes, mcts.RandomRolloutEvaluator(1))
    score1 = play_game(game, zero_bot, mcts_bot)

    # Random bot first
    zero_bot = NeuralNetBot(game, 1, policy_fn)
    mcts_bot = mcts.MCTSBot(game, 0, 1,
                            max_search_nodes, mcts.RandomRolloutEvaluator(1))
    score2 = -play_game(game, mcts_bot, zero_bot)
    return score1, score2


def test_net_vs_random(policy_fn, game_name, **kwargs):
    game = pyspiel.load_game(game_name)

    # Alphazero first
    zero_bot = NeuralNetBot(game, 0, policy_fn)
    random_bot = pyspiel.make_uniform_random_bot(game, 1, np.random.randint(0, 1000))
    score1 = play_game(game, zero_bot, random_bot)

    # Random bot first
    zero_bot = NeuralNetBot(game, 1, policy_fn)
    random_bot = pyspiel.make_uniform_random_bot(game, 0, np.random.randint(0, 1000))
    score2 = -play_game(game, random_bot, zero_bot)
    return score1, score2


def test_zero_vs_zero(policy_fn, max_search_nodes, game_name, policy_fn2=None, **kwargs):
    examples = []
    settings1 = dict(kwargs.get("settings1", None))
    settings2 = dict(kwargs.get("settings2", None))
    if not policy_fn2:
        policy_fn2 = policy_fn
    game = pyspiel.load_game(game_name)

    # Alphazero first
    zero1_bot = AlphaZeroBot(game, 0, policy_fn=policy_fn, use_dirichlet=True, **settings1)
    zero2_bot = AlphaZeroBot(game, 1, policy_fn=policy_fn2, use_dirichlet=True, **settings2)

    score1 = play_game(game, zero1_bot, zero2_bot)

    # Random bot first
    zero1_bot = AlphaZeroBot(game, 1, policy_fn=policy_fn, use_dirichlet=True, **settings1)
    zero2_bot = AlphaZeroBot(game, 0, policy_fn=policy_fn2, use_dirichlet=True, **settings2)
    score2 = -play_game(game, zero2_bot, zero1_bot)
    return score1, score2


def play_game_self(policy_fn, game_name, **kwargs):
    examples = []
    game = pyspiel.load_game(game_name)
    state = game.new_initial_state()
    state_shape = game.information_state_normalized_vector_shape()
    num_distinct_actions = game.num_distinct_actions()
    alphazero_bot = AlphaZeroBot(game, 0, policy_fn, self_play=True, **kwargs)
    while not state.is_terminal():
        policy, action = alphazero_bot.step(state)
        policy_dict = dict(policy)
        policy_list = []
        for i in range(num_distinct_actions):
            # Create a policy list. To be used in the net instead of a list of tuples.
            policy_list.append(policy_dict.get(i, 0.0))
        examples.append([state.information_state(), state_to_board(state, state_shape), policy_list, None])
        state.apply_action(action)
    # Get return for starting player
    reward = state.returns()[0]
    for i in range(len(examples)):
        examples[i][3] = reward
        reward *= -1
    return examples