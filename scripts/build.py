import subprocess
from pathlib import Path

import click
from python_on_whales import DockerClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTAINERFILE = PROJECT_ROOT / "Containerfile"


def _client() -> DockerClient:
    return DockerClient(client_call=["podman"])


def build_image(tag: str, containerfile: Path, context: Path) -> str:
    """Build the image locally. Never pushes."""
    _client().legacy_build(
        context_path=context,
        file=containerfile,
        tags=tag,
        quiet=True,
    )
    return tag


def push_image(tag: str, tls_verify: bool = True) -> None:
    """Push a built image. Caller must `podman login` to the registry first.

    `tls_verify=False` is intended for tests against a local plain-HTTP registry.
    """
    if tls_verify:
        _client().push(tag)
        return
    subprocess.run(
        ["podman", "push", "--tls-verify=false", tag],
        check=True,
    )


@click.command()
@click.option(
    "--tag",
    "-t",
    "tags",
    multiple=True,
    default=("health-monitor-backend:latest",),
    show_default=True,
    help="Image tag(s) to apply. Repeat for multiple tags.",
)
@click.option(
    "--containerfile",
    "-f",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    default=DEFAULT_CONTAINERFILE,
    show_default=True,
    help="Path to the Containerfile.",
)
@click.option(
    "--context",
    "-c",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=PROJECT_ROOT,
    show_default=True,
    help="Build context directory.",
)
@click.option(
    "--push/--no-push",
    default=False,
    show_default=True,
    help="Push the image after building. Requires prior `podman login`.",
)
def main(tags: tuple[str, ...], containerfile: Path, context: Path, push: bool) -> None:
    """Build the health-monitor-backend container image with Podman."""
    for tag in tags:
        click.echo(f"Building {tag} from {containerfile} (context: {context})")
        build_image(tag=tag, containerfile=containerfile, context=context)
        click.echo(f"Built {tag}")

    if push:
        for tag in tags:
            click.echo(f"Pushing {tag}")
            push_image(tag)
            click.echo(f"Pushed {tag}")


if __name__ == "__main__":
    main()
