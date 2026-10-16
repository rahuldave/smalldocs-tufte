"Check that tufte.css and tufte-dark.css are whole Bootstrap 5.3 themes, as a Bootswatch theme is. Standard library only."

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "_extensions" / "tufte"
FILES = ["tufte.css", "tufte-dark.css"]
COMPONENTS = [".btn", ".btn-primary", ".navbar", ".nav-link", ".card", ".alert", ".table", ".form-control", ".dropdown-menu", ".badge", ".container"]


def read(name: str) -> str:
    "The CSS of a file in the extension, without comments."
    return re.sub(r"/\*.*?\*/", "", (EXT / name).read_text(encoding="utf-8"), flags=re.S)


def rules(css: str) -> list[tuple[list[str], str]]:
    "Each innermost rule of the CSS: its selectors and its body."
    # A selector can follow an at-rule that ends in a semicolon, such as @charset "UTF-8";
    return [([s.strip() for s in sel.rpartition(";")[2].split(",")], body) for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]


def props(css: str, selector: str) -> dict[str, str]:
    "The custom properties that the rules for a selector define, later rules winning."
    out: dict[str, str] = {}
    for sels, body in rules(css):
        if selector in sels:
            out.update(re.findall(r"(--[\w-]+)\s*:\s*([^;]+)", body))
    return out


def spec() -> dict:
    "The keys of smalldocs.yml, read without PyYAML: the file is a few plain lines."
    out, section = {}, None
    for line in (EXT / "smalldocs.yml").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, value = line.strip().partition(":")
        value = value.strip()
        if line.startswith((" ", "\t")) and section:
            out[section][key] = value
        elif value:
            out[key], section = value, None
        else:
            out[key], section = {}, key
    return out


@pytest.mark.parametrize("name", FILES)
def test_bootstrap_banner(name):
    text = (EXT / name).read_text(encoding="utf-8")
    assert re.search(r"Bootstrap\s+v5\.3\.\d+", text[:2000]), "the file must start with Bootstrap 5.3"


@pytest.mark.parametrize("name", FILES)
def test_bootswatch_variables(name):
    lines = (ROOT / "tests" / "bootswatch-vars.txt").read_text().splitlines()
    wanted = [v.strip() for v in lines if v.strip() and not v.startswith("#")]
    have = props(read(name), ":root")
    missing = [v for v in wanted if v not in have]
    assert not missing, f"{name} does not define on :root: {', '.join(missing)}"


@pytest.mark.parametrize("name", FILES)
def test_colour_modes(name):
    css = read(name)
    dark = props(css, "[data-bs-theme=dark]")
    assert "--bs-body-bg" in dark and "--bs-body-color" in dark


@pytest.mark.parametrize("name", FILES)
@pytest.mark.parametrize("component", COMPONENTS)
def test_components(name, component):
    selectors = {s for sels, _ in rules(read(name)) for s in sels}
    assert component in selectors, f"{name} has no rule for {component}"


@pytest.mark.parametrize("name", FILES)
def test_urls_resolve(name):
    for ref in re.findall(r"""url\(\s*['"]?([^'")]+?)['"]?\s*\)""", read(name)):
        if ref.startswith(("data:", "#")):
            continue
        assert not re.match(r"^[a-z]+:|^//|^/", ref), f"{name} loads {ref} from outside the folder"
        path = (EXT / re.split(r"[?#]", ref)[0]).resolve()
        assert EXT.resolve() in path.parents and path.is_file(), f"{name}: {ref} is not a file in the folder"


def test_spec_files_exist():
    s = spec()
    assert set(s) <= {"css", "logo", "favicon"}
    assert set(s["css"]) == {"light", "dark"}
    for f in [*s["css"].values(), *(s[k] for k in ("logo", "favicon") if k in s)]:
        assert (EXT / f).is_file(), f"smalldocs.yml names {f}, which is not there"


def test_modes_differ():
    s = spec()["css"]
    light, dark = (props(read(s[m]), ":root")["--bs-body-bg"].strip() for m in ("light", "dark"))
    assert light != dark
    assert light == "#fffff8" and dark == "#151515"
