# Установка зависимостей

Чтобы под Windows установился модуль `gymnasium[box2d]` нужно установить swig. Также нужно установить зависимости для Python.

```
choco install swig
pip install -r requirements.txt
```

# Обучение модели

```
python learn.py <Model filname> <Algorithm: PPO or A2C> <total_timesteps_k (in thousands)> --log_path logs
python learn.py ppo_2.zip PPO 300 --log_path logs
```

Во время обучения можно посмотреть графики. Для этого нужно запустить TensorBoard.

```
python -m tensorboard.main --logdir logs
```

# Использование модели

Demo-пример загружает указанную модель и запускает визуализацию.

```
python demo.py <Model filname> <Algorithm: PPO or A2C>
python demo.py ppo_2.zip PPO
```

Есть сервис, который можно упаковать в Docker контейнер. И клиент, который покажет визуализацию и будет использовать модель внутри сервиса.

```
docker run --name ml-service -p 8080:8080  ml-service
python client.py
```

Или без использования контейнера.

```
python service.py
python client.py
```

# Сборка контейнера

```
docker build -t ml-service .
```
