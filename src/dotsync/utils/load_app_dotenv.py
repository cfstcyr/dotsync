import os

from dotenv import dotenv_values


def load_app_dotenv(*files: str, prefix: str, override: bool = False):
    env = {}
    for file in files:
        values = dotenv_values(file)
        env.update(
            {k: v for k, v in values.items() if v is not None and k.startswith(prefix)}
        )

    if override:
        os.environ.update(env)
    else:
        for k, v in env.items():
            os.environ.setdefault(k, v)

    return env
