For Windows:

```
choco install swig
pip install gymnasium[box2d]
```

TensorBoard:

```
python -m tensorboard.main --logdir logs
```

Examples:

```
python learn.py ppo_2.zip PPO 300 --log_path logs
python predict.py ppo_2.zip PPO
```
