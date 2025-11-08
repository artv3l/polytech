import requests
import gymnasium as gym

c_serviceUrl = "http://localhost:8080/predict"

if __name__ == "__main__":
    env = gym.make("LunarLander-v3", render_mode="human")
    
    obs, _ = env.reset()
    done = False
    total_reward = 0

    while not done:
        payload = {"obs": obs.tolist()}
        response = requests.post(c_serviceUrl, json=payload)
        action = response.json()["action"]

        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        total_reward += reward

    print(f"Total reward: {total_reward:.2f}")
    env.close()
