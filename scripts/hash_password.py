from __future__ import annotations

import argparse
import getpass

from app.password_auth import hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a PBKDF2 password hash for SESSION_PASSWORD_HASH.",
    )
    parser.add_argument(
        "--password",
        help="Plaintext password to hash. If omitted, the script prompts securely.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    password = args.password or getpass.getpass("Password: ")
    print(hash_password(password))


if __name__ == "__main__":
    main()
