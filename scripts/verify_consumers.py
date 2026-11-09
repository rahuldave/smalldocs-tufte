"""Build real consumers from working outputs, never the last Git commit.

Usage: python3 scripts/verify_consumers.py /tmp/tufte-foundations-qa
Then serve that folder on 8860 and inspect both renderers in each mode/width.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    destination = Path(sys.argv[1]).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "tests/fixtures/narrow.html", destination / "narrow.html")
    example = destination / "example"
    shutil.copytree(
        ROOT / "example",
        example,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("_site", "_extensions", ".quarto"),
    )
    shutil.copytree(
        ROOT / "_extensions/tufte", example / "_extensions/tufte", dirs_exist_ok=True
    )
    subprocess.run(
        [
            "uvx",
            "--from",
            "smalldocs==0.5.5",
            "smalldocs",
            "render",
            str(example),
            "--strict",
        ],
        check=True,
    )
    for renderer in ["smalldocs", "quarto"]:
        folder = destination / renderer
        folder.mkdir(exist_ok=True)
        shutil.copytree(
            ROOT / "_extensions/tufte", folder / "_extensions/tufte", dirs_exist_ok=True
        )
        shutil.copy2(ROOT / "tests/fixtures/components.qmd", folder / "index.qmd")
        common = "project:\n  type: website\nwebsite:\n  title: Tufte acceptance\n  navbar:\n    left:\n      - href: index.qmd\n        text: Components\ntoc: true\nreference-location: margin\n"
        if renderer == "smalldocs":
            (folder / "_smalldocs.yml").write_text(common + "theme: tufte\n")
            subprocess.run(
                [
                    "uvx",
                    "--from",
                    "smalldocs==0.5.5",
                    "smalldocs",
                    "render",
                    str(folder),
                    "--strict",
                ],
                check=True,
            )
        else:
            (folder / "_quarto.yml").write_text(
                common + "format:\n  tufte-html:\n    toc: true\n"
            )
            subprocess.run(["quarto", "render", str(folder)], check=True)
        page = folder / "_site/index.html"
        text = page.read_text()
        for marker in [
            "acceptance-form",
            "project-error",
            "aria-selected",
            "alert-success",
            "column-margin",
        ]:
            assert marker in text, (renderer, marker)
        assert (folder / "_extensions/tufte/foundations.json").read_bytes() == (
            ROOT / "src/foundations.json"
        ).read_bytes()
        print(
            f"{renderer}: working manifest and complete components fixture rendered to {page}"
        )


if __name__ == "__main__":
    main()
