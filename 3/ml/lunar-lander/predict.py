import argparse
import sys

import gymnasium as gym

import common

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    parser.add_argument("algorithm")
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args(sys.argv[1:])

    algo = common.select_algorithm(args.algorithm)
    if algo is None:
        print("Invalid algorithm")
        pass

    env = gym.make("LunarLander-v3", render_mode="human")
    
    model = common.load_model(args.model_path, args.algorithm)
    
    obs, _ = env.reset()
    done = False
    total_reward = 0

    while not done:
        action, _states = model.predict(obs)
        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        total_reward += reward

    print(f"Total reward: {total_reward:.2f}")
    env.close()
