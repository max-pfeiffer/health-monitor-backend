from pathlib import Path

import click
from python_on_whales import DockerClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTAINERFILE = PROJECT_ROOT / "Containerfile"


def build_image(tag: str, containerfile: Path, context: Path) -> str:
    podman = DockerClient(client_call=["podman"])
    podman.legacy_build(
        context_path=context,
        file=containerfile,
        tags=tag,
        quiet=True,
    )
    return tag


@click.command()
@click.option(
    "--tag",
    "-t",
    default="health-monitor-backend:latest",
    show_default=True,
    help="Image tag to apply to the built image.",
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
def main(tag: str, containerfile: Path, context: Path) -> None:
    """Build the health-monitor-backend container image with Podman."""
    click.echo(f"Building {tag} from {containerfile} (context: {context})")
    build_image(tag=tag, containerfile=containerfile, context=context)
    click.echo(f"Built {tag}")


if __name__ == "__main__":
    main()
