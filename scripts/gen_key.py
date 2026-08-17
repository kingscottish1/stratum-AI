#!/usr/bin/env python3
"""Print a fresh hex key for JWT_SECRET / ENCRYPTION_KEY."""
import secrets

if __name__ == "__main__":
    print(secrets.token_hex(32))
