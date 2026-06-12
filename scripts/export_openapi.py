"""Export OpenAPI specs."""

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import click
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_tags() -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--sort=v:refname"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )
    return [t for t in result.stdout.strip().split("\n") if t]


def detect_api_versions(worktree_path: Path) -> list[str]:
    """Return API version names by finding v*.py files in app/routers/."""
    routers_dir = worktree_path / "app" / "routers"
    return sorted(f.stem for f in routers_dir.glob("v*.py"))


def generate_openapi_spec(worktree_path: Path) -> dict:
    """Import the FastAPI app from a worktree and return its OpenAPI schema."""
    script = (
        "import json, sys; "
        f"sys.path.insert(0, r'{worktree_path}'); "
        "from app.main import app; "
        "print(json.dumps(app.openapi()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def load_spec(file_path: Path) -> dict | None:
    """Return the parsed YAML spec, or ``None`` if the file does not exist."""
    if not file_path.exists():
        return None
    with open(file_path) as f:
        return yaml.safe_load(f)


def write_spec(output_file: Path, spec: dict) -> None:
    with open(output_file, "w") as f:
        yaml.dump(
            spec,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def comparable_spec(spec: dict) -> dict:
    """Strip ``info.version`` so a version-only bump isn't treated as a spec change."""
    copy = deepcopy(spec)
    copy["info"].pop("version", None)
    return copy


def spec_filename(tag: str, api_version: str) -> str:
    return f"health-monitor-backend_{tag}_api_{api_version}.yaml"


def find_previous_spec(
    output_path: Path, api_version: str, current_tag: str, tags: list[str]
) -> dict | None:
    """Return the most recent existing spec for ``api_version`` before the tag."""
    idx = tags.index(current_tag)
    for earlier_tag in reversed(tags[:idx]):
        previous = load_spec(output_path / spec_filename(earlier_tag, api_version))
        if previous is not None:
            return previous
    return None


@click.command()
@click.option(
    "--output-dir",
    default=str(PROJECT_ROOT / "api_docs"),
    show_default=True,
    help="Directory to write spec files into.",
)
def main(output_dir: str) -> None:
    """Generate OpenAPI YAML specs for all tagged application versions."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    tags = get_tags()
    if not tags:
        click.echo("No git tags found.", err=True)
        sys.exit(1)

    for tag in tags:
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir) / tag.replace(".", "_")

            click.echo(f"Processing tag {tag} ...")
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(worktree_path), tag],
                check=True,
                capture_output=True,
                cwd=PROJECT_ROOT,
            )

            try:
                api_versions = detect_api_versions(worktree_path)
                spec = generate_openapi_spec(worktree_path)
                comparable = comparable_spec(spec)

                for api_version in api_versions:
                    output_file = output_path / spec_filename(tag, api_version)

                    previous = find_previous_spec(output_path, api_version, tag, tags)
                    if previous is not None and comparable_spec(previous) == comparable:
                        click.echo(
                            f"  Skipped {api_version}: unchanged from previous version"
                        )
                        continue

                    existing = load_spec(output_file)
                    if existing is not None and comparable_spec(existing) == comparable:
                        click.echo(f"  Up-to-date: {output_file}")
                        continue

                    write_spec(output_file, spec)
                    click.echo(f"  Written: {output_file}")
            finally:
                subprocess.run(
                    ["git", "worktree", "remove", str(worktree_path), "--force"],
                    capture_output=True,
                    cwd=PROJECT_ROOT,
                )


if __name__ == "__main__":
    main()
