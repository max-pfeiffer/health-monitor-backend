"""Export OpenAPI specs."""

import json
import subprocess
import sys
import tempfile
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

                for api_version in api_versions:
                    filename = f"openapi_app{tag}_api_{api_version}.yaml"
                    output_file = output_path / filename

                    with open(output_file, "w") as f:
                        yaml.dump(
                            spec,
                            f,
                            default_flow_style=False,
                            allow_unicode=True,
                            sort_keys=False,
                        )

                    click.echo(f"  Written: {output_file}")
            finally:
                subprocess.run(
                    ["git", "worktree", "remove", str(worktree_path), "--force"],
                    capture_output=True,
                    cwd=PROJECT_ROOT,
                )


if __name__ == "__main__":
    main()
