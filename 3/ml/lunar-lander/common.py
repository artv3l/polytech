from pathlib import Path

from stable_baselines3 import PPO, A2C

def select_algorithm(algorithm: str):
    if algorithm == "PPO":
        return PPO
    elif algorithm == "A2C":
        return A2C
    else:
        return None
    
def load_model(model_path: Path, algorithm: str):
    algo = select_algorithm(algorithm)
    if algo is not None:
        return algo.load(str(model_path))
    else:
        return None
    