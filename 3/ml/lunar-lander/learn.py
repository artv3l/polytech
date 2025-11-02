import argparse
import sys
from pathlib import Path

from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import VecVideoRecorder
from stable_baselines3.common.env_util import make_vec_env

import common

videos_path = "./video"

model_policy = "MlpPolicy"
eval_freq = 1_000
video_every_steps = 10_000
video_length = 1_000


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    parser.add_argument("algorithm")
    parser.add_argument("total_timesteps_k")
    parser.add_argument("--log_path", default=None)
    return parser

def make_env(**kwargs):
    return make_vec_env("LunarLander-v3", **kwargs)

def get_model(model_path: Path, algorithm: str, log_path: Path):
    algo = common.select_algorithm(algorithm)
    if algo is None:
        print("Invalid algorithm")
        return None
    
    env = make_env(n_envs=4)
    if model_path.is_file():
        print("Load existing model")
        model = common.load_model(model_path, algorithm)
        model.env = env
        model.tensorboard_log = str(log_path)
    else:
        print("Create new model")
        model = algo(model_policy, env, tensorboard_log=str(log_path))
    
    return model

if __name__ == "__main__":
    args = get_parser().parse_args(sys.argv[1:])

    total_timesteps = int(args.total_timesteps_k) * 1_000

    model = get_model(Path(args.model_path), args.algorithm, args.log_path)

    eval_env = make_env(n_envs=1)

    eval_video_env = VecVideoRecorder(
        eval_env,
        video_folder=videos_path,
        record_video_trigger=lambda step: step % video_every_steps == 0,
        video_length=video_length,
        name_prefix=args.algorithm
    )

    eval_callback = EvalCallback(
        eval_video_env,
        log_path=args.log_path,
        eval_freq=eval_freq,
        deterministic=True,
        render=False,
    )

    model.learn(total_timesteps=total_timesteps, callback=eval_callback)
    model.save(args.model_path)
