import os
from typing import Dict, Tuple

from dotenv import dotenv_values


ENV_PATH = ".env"


def ensure_env_file() -> None:
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write(
                "PROJECT_ENDPOINT=\nAZURE_OPENAI_ENDPOINT=\nAZURE_OPENAI_API_KEY=\nAZURE_INFERENCE_CREDENTIAL=\n"
            )


def read_env() -> Dict[str, str]:
    ensure_env_file()
    return {**dotenv_values(ENV_PATH)}  # type: ignore[return-value]


def set_env_var(key: str, value: str) -> None:
    ensure_env_file()
    lines: list[str] = []
    found = False
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                if not line.strip() or line.strip().startswith("#"):
                    lines.append(line)
                    continue
                k, sep, v = line.partition("=")
                if k == key:
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(ENV_PATH, "w") as f:
        f.writelines(lines)


def set_many(pairs: Dict[str, str]) -> None:
    for k, v in pairs.items():
        set_env_var(k, v)


def get_var(key: str, default: str = "") -> Tuple[str, bool]:
    env = read_env()
    if key in env and env[key] is not None:
        return str(env[key]), True
    return default, False
