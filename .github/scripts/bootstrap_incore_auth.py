"""Seed the pyincore token cache so the analyses tests can run unattended.

tests/conftest.py monkeypatches input()/getpass() for pytest, but the analyses
tests are run as standalone scripts and build their own IncoreClient, so that
hook never fires. This does the same credential exchange up front and lets
IncoreClient write its token file to ~/.incore; every later client for the same
service URL then picks the token up instead of prompting.

Reads tests/pyincore/.incorepw, the same two-line (JWT, key) credential file the
pytest workflow writes from the PYTEST_USER_TOKEN secret.
"""

import builtins
import getpass
import os
import sys

from jose import jwt

from pyincore import IncoreClient, globals as pyglobals

CREDENTIAL_FILE = os.path.join("tests", "pyincore", ".incorepw")


def main():
    with open(CREDENTIAL_FILE, "r") as f:
        cred = f.read().splitlines()
    credentials = jwt.decode(cred[0], cred[1])

    builtins.input = lambda *args, **kwargs: credentials["username"]
    getpass.getpass = lambda *args, **kwargs: credentials["password"]

    # Most analyses tests target dev; a couple use prod or the default (prod).
    for service_url in (pyglobals.INCORE_API_DEV_URL, pyglobals.INCORE_API_PROD_URL):
        print(f"Caching token for {service_url}")
        try:
            client = IncoreClient(service_url=service_url)
        except SystemExit:
            # IncoreClient.login() calls exit(0) when authentication fails, which
            # would otherwise leave this script looking like it succeeded.
            raise RuntimeError(f"authentication against {service_url} failed")
        if "Authorization" not in client.session.headers:
            raise RuntimeError(f"no token obtained for {service_url}")
        print(f"  token cached at {client.token_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 - surface the reason in the CI log
        print(f"Failed to cache IN-CORE token: {e}", file=sys.stderr)
        sys.exit(1)
