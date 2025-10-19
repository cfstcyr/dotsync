from dotsync.cli.app import app
from dotsync.utils.load_app_dotenv import load_app_dotenv


def main():
    load_app_dotenv(".env.dev", ".env", prefix="DOTSYNC_", override=True)
    app()


if __name__ == "__main__":
    main()
