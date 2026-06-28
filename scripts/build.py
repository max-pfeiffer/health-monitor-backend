from pathlib import Path

import click
from python_on_whales import DockerClient
from python_on_whales.utils import run as pow_run

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTAINERFILE = PROJECT_ROOT / "Containerfile"
DEFAULT_PLATFORMS = ("linux/amd64", "linux/arm64")


def _client() -> DockerClient:
    return DockerClient(client_call=["podman"])


def build_image(
    tag: str,
    containerfile: Path,
    context: Path,
    platforms: tuple[str, ...] = DEFAULT_PLATFORMS,
) -> str:
    """Build the image locally. Never pushes.

    A single platform produces a normal image tagged ``tag``. Multiple
    platforms produce a multi-arch manifest list named ``tag`` (one image per
    architecture, all referenced by the manifest).
    """
    client = _client()
    if len(platforms) > 1:
        # podman keeps each architecture under a manifest list. python-on-whales'
        # build helpers don't expose --manifest, so build the command directly
        # (same client, lower-level entry point).
        pow_run(
            client.docker_cmd
            + [
                "build",
                "--platform",
                ",".join(platforms),
                "--manifest",
                tag,
                "--file",
                str(containerfile),
                str(context),
            ]
        )
    else:
        client.legacy_build(
            context_path=context,
            file=containerfile,
            tags=tag,
            pull=False,
            quiet=True,
        )
    return tag


def push_image(tag: str, multi_arch: bool = False) -> None:
    """Push a built image. Caller must `podman login` to the registry first.

    For a multi-arch build, push the whole manifest list (every architecture).
    """
    client = _client()
    if multi_arch:
        # `podman manifest push --all` uploads the manifest list together with
        # the per-architecture images it references.
        pow_run(
            client.docker_cmd + ["manifest", "push", "--all", tag, f"docker://{tag}"]
        )
    else:
        client.push(tag)


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
    "--platform",
    "-p",
    "platforms",
    multiple=True,
    default=DEFAULT_PLATFORMS,
    show_default=True,
    help=(
        "Target platform(s). Repeat for multiple. Multiple platforms build a "
        "multi-arch manifest list. A single platform builds a runnable image."
    ),
)
@click.option(
    "--push/--no-push",
    default=False,
    show_default=True,
    help="Push the image after building. Requires prior `podman login`.",
)
def main(
    tags: tuple[str, ...],
    containerfile: Path,
    context: Path,
    platforms: tuple[str, ...],
    push: bool,
) -> None:
    """Build the health-monitor-backend container image with Podman."""
    multi_arch = len(platforms) > 1
    for tag in tags:
        click.echo(
            f"Building {tag} from {containerfile} "
            f"(context: {context}, platforms: {', '.join(platforms)})"
        )
        build_image(
            tag=tag,
            containerfile=containerfile,
            context=context,
            platforms=platforms,
        )
        click.echo(f"Built {tag}")

    if push:
        for tag in tags:
            click.echo(f"Pushing {tag}")
            push_image(tag, multi_arch=multi_arch)
            click.echo(f"Pushed {tag}")


if __name__ == "__main__":
    main()
