"""Obtain a bearer token from Keycloak for local manual testing."""

import sys
import time

import click
import httpx


@click.command()
@click.option(
    "--keycloak-url",
    default="http://localhost:8080",
    show_default=True,
    help="Base URL of the Keycloak server.",
)
@click.option(
    "--realm",
    default="health-monitor",
    show_default=True,
    help="Keycloak realm name.",
)
@click.option(
    "--client-id",
    default="health-monitor-swagger",
    show_default=True,
    help="OAuth2 client ID configured in the realm.",
)
@click.option(
    "--username",
    default="tester",
    show_default=True,
    help="Username of the realm user to authenticate as.",
)
@click.option(
    "--password",
    default="tester",
    show_default=True,
    help="Password of the realm user.",
)
@click.option(
    "--wait/--no-wait",
    default=True,
    show_default=True,
    help="Wait up to 60s for Keycloak to become reachable.",
)
def main(
    keycloak_url: str,
    realm: str,
    client_id: str,
    username: str,
    password: str,
    wait: bool,
) -> None:
    """Print a JWT access token using Keycloak's direct access grant flow.

    Pipe the output to your clipboard (e.g. `... | pbcopy` on macOS) and paste
    it into the Swagger UI Authorize dialog at http://localhost:8000/docs.
    """
    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"

    if wait:
        _wait_for_keycloak(keycloak_url, realm)

    try:
        resp = httpx.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": client_id,
                "username": username,
                "password": password,
            },
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        click.echo(f"Failed to reach Keycloak at {token_url}: {exc}", err=True)
        sys.exit(1)

    if resp.status_code != 200:
        click.echo(
            f"Token request failed: HTTP {resp.status_code}\n{resp.text}",
            err=True,
        )
        sys.exit(1)

    click.echo(resp.json()["access_token"])


def _wait_for_keycloak(keycloak_url: str, realm: str, timeout: float = 60.0) -> None:
    discovery_url = f"{keycloak_url}/realms/{realm}/.well-known/openid-configuration"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(discovery_url, timeout=2.0)
            if resp.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2.0)
    click.echo(
        f"Keycloak not reachable at {discovery_url} after {timeout:.0f}s.",
        err=True,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
