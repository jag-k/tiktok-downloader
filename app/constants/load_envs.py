from pathlib import Path


def load_envs(base_path: Path, config_path: Path, print_envs: bool = False):
    env_paths = [
        base_path / ".env",
        base_path / ".env.local",
        config_path / ".env",
        config_path / ".env.local",
    ]

    for env_path in env_paths:
        if env_path and env_path.exists() and env_path.is_file():
            from dotenv import load_dotenv

            load_dotenv(env_path)
            if print_envs:
                print(f"Loaded envs from {env_path}")
            break
    else:
        if print_envs:
            print("No .env file found")
