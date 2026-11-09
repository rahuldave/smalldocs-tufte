"""Render local foundations into both standalone and Quarto build inputs."""

import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent


def rgb(value: str) -> str:
    return ", ".join(str(int(value[i : i + 2], 16)) for i in (1, 3, 5))


def mode_css(mode: dict, selector: str, name: str) -> str:
    """Use explicit roles; original decorative anchors never become boundaries."""
    sw, roles = mode["swatches"], mode["roles"]
    colors = {key: sw[value] for key, value in roles.items()}
    props = {f"--tf-{key}": value for key, value in colors.items()}
    mapping = {
        "body-bg": "paper",
        "body-color": "ink",
        "heading-color": "ink",
        "emphasis-color": "ink",
        "secondary-color": "muted",
        "tertiary-color": "muted",
        "secondary-bg": "panel",
        "tertiary-bg": "code",
        "border-color": "control-boundary",
        "border-color-translucent": "control-boundary",
        "link-color": "accent-text",
        "link-hover-color": "link-hover",
        "code-color": "code-ink",
        "primary": "primary-fill",
        "highlight-bg": "optional-highlight-fill",
        "highlight-color": "optional-highlight-ink",
        "primary-bg-subtle": "selected-fill",
        "primary-text-emphasis": "selected-ink",
        "primary-border-subtle": "control-boundary",
        "focus-ring-color": "focus",
    }
    for token, role in mapping.items():
        props[f"--bs-{token}"] = colors[role]
        if token in [
            "body-bg",
            "body-color",
            "emphasis-color",
            "secondary-color",
            "secondary-bg",
            "tertiary-bg",
            "link-color",
            "link-hover-color",
            "primary",
        ]:
            props[f"--bs-{token}-rgb"] = rgb(colors[role])
    for state, values in mode["states"].items():
        for token in ["fill", "ink", "boundary"]:
            props[f"--tf-{state}-{token}"] = values[token]
    for kind, shape in {
        "check": '<path d="m3 8 3 3 7-7" fill="none" stroke="'
        + colors["selected-ink"]
        + '" stroke-width="2"/>',
        "radio": '<circle cx="8" cy="8" r="4" fill="' + colors["selected-ink"] + '"/>',
    }.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
            + shape
            + "</svg>"
        )
        props[f"--tf-{kind}-image"] = (
            'url("data:image/svg+xml,' + quote(svg, safe="") + '")'
        )
    props.update(
        {"--sd-inline-code": colors["code-ink"], "--sd-code-bg": colors["code"]}
    )
    return (
        selector
        + " {\n  color-scheme: "
        + name
        + ";\n"
        + "".join(f"  {k}: {v};\n" for k, v in props.items())
        + "}\n"
    )


def defaults(mode: dict, data: dict) -> str:
    """Quarto Sass gets the exact same opaque colors as standalone CSS."""
    c = {k: mode["swatches"][v] for k, v in mode["roles"].items()}
    values = {
        "body-bg": c["paper"],
        "body-color": c["ink"],
        "primary": c["primary-fill"],
        "link-color": c["accent-text"],
        "link-hover-color": c["link-hover"],
        "border-color": c["control-boundary"],
        "font-family-sans-serif": data["typography"]["fonts"]["body"],
        "font-family-monospace": data["typography"]["fonts"]["code"],
        "font-size-root": "100%",
        "grid-body-width": "640px",
        "grid-margin-width": "220px",
        "font-size-base": f'{data["typography"]["profiles"]["reading"]["body"] / 16:g}rem',
        "line-height-base": str(data["typography"]["lineHeights"]["reading"]),
        "headings-font-weight": "400",
        "border-radius": "0",
        "border-radius-sm": "0",
        "border-radius-lg": "0",
        "navbar-bg": c["paper"],
        "navbar-fg": c["muted"],
        "navbar-hl": c["ink"],
        "footer-bg": c["paper"],
        "footer-fg": c["muted"],
        "sidebar-bg": c["paper"],
        "code-color": c["code-ink"],
        "code-bg": c["code"],
        "toc-color": c["ink"],
        "callout-border-width": "2px",
    }
    for kind, state in {
        "note": "info",
        "tip": "success",
        "warning": "warning",
        "important": "danger",
        "caution": "danger",
    }.items():
        values["callout-color-" + kind] = mode["states"][state]["ink"]
    return "/*-- scss:defaults --*/\n" + "".join(
        f"${k}: {v} !default;\n" for k, v in values.items()
    )


def main() -> None:
    data = json.loads((ROOT / "src/foundations.json").read_text())
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    for name, mode in data["modes"].items():
        selector = (
            ":root, [data-bs-theme=light]"
            if name == "light"
            else ":root, [data-bs-theme=light], [data-bs-theme=dark]"
        )
        (target / f"{name}.css").write_text(mode_css(mode, selector, name))
        (target / f"defaults-{name}.scss").write_text(defaults(mode, data))
    (target / "dark-parts.css").write_text(
        mode_css(data["modes"]["dark"], "[data-bs-theme=dark]", "dark")
    )
    profiles = data["typography"]["profiles"]["reading"]
    tokens = {
        f"--tf-size-{key}": f"{value / 16:g}rem" for key, value in profiles.items()
    }
    tokens.update(
        {
            f"--tf-type-{value}": f"{value / 16:g}rem"
            for value in data["typography"]["scale"]
        }
    )
    tokens.update(
        {
            f"--tf-space-{value}": f"{value / 16:g}rem"
            for value in data["spacing"]["scale"]
        }
    )
    tokens.update(
        {
            f"--tf-gap-{key}": f"{value / 16:g}rem"
            for key, value in data["spacing"]["profiles"]["reading"].items()
        }
    )
    tokens.update(
        {
            f"--tf-line-{key}": str(value)
            for key, value in data["typography"]["lineHeights"].items()
        }
    )
    tokens.update(
        {
            f"--tf-font-{key}": value
            for key, value in data["typography"]["fonts"].items()
        }
    )
    (target / "profiles.css").write_text(
        ":root {\n" + "".join(f"  {k}: {v};\n" for k, v in tokens.items()) + "}\n"
    )
    # Publish the source verbatim, not a reconstructed approximation.
    (ROOT / "_extensions/tufte/foundations.json").write_bytes(
        (ROOT / "src/foundations.json").read_bytes()
    )


if __name__ == "__main__":
    main()
