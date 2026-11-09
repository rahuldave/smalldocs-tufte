"""Test authored contracts and emitted consumer parity with no third-party color math."""

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "src/foundations.json").read_text())


def contrast(a: str, b: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [
            x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
            for x in channels
        ]
        return sum(a * b for a, b in zip(linear, [0.2126, 0.7152, 0.0722]))

    values = sorted([luminance(a), luminance(b)])
    return (values[1] + 0.05) / (values[0] + 0.05)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_opaque_pairs_and_roles(mode: str) -> None:
    data = DATA["modes"][mode]
    sw, roles = data["swatches"], data["roles"]
    assert all(re.fullmatch(r"#[0-9a-fA-F]{6}", value) for value in sw.values())
    assert all(ref in sw for ref in roles.values())
    color = lambda role: sw[roles[role]]
    for role in ["ink", "muted", "accent-text", "link-hover", "code-ink"]:
        for background in ["paper", "panel", "code"]:
            assert contrast(color(role), color(background)) >= 5
    for role in ["focus", "control-boundary"]:
        for background in ["paper", "panel", "code"]:
            assert contrast(color(role), color(background)) >= 3
    for ink, fill in [
        ("button-ink", "primary-fill"),
        ("primary-hover-ink", "primary-hover-fill"),
        ("selected-ink", "selected-fill"),
        ("optional-highlight-ink", "optional-highlight-fill"),
    ]:
        assert contrast(color(ink), color(fill)) >= 4.5
    for state in data["states"].values():
        assert contrast(state["ink"], state["fill"]) >= 5
        assert contrast(state["boundary"], state["fill"]) >= 3
    assert (
        color("accent-text")[1:3]
        == color("accent-text")[3:5]
        == color("accent-text")[5:7]
    )


def test_build_is_reproducible_and_parity_is_exact() -> None:
    extension = ROOT / "_extensions/tufte"
    names = [
        "foundations.json",
        "tufte.css",
        "tufte-dark.css",
        "tufte.scss",
        "tufte-dark.scss",
    ]
    before = {name: (extension / name).read_bytes() for name in names}
    subprocess.run(["sh", "scripts/build.sh"], cwd=ROOT, check=True)
    assert before == {name: (extension / name).read_bytes() for name in names}
    assert before["foundations.json"] == (ROOT / "src/foundations.json").read_bytes()
    for mode, standalone, sass in [
        ("light", "tufte.css", "tufte.scss"),
        ("dark", "tufte-dark.css", "tufte-dark.scss"),
    ]:
        for role, ref in DATA["modes"][mode]["roles"].items():
            token = f"--tf-{role}: {DATA['modes'][mode]['swatches'][ref]};"
            assert token in before[standalone].decode()
            assert token in before[sass].decode()
    assert "Bootstrap v5" not in before["tufte.scss"].decode()
    assert "Bootstrap v5" not in before["tufte-dark.scss"].decode()


def test_reading_scale_and_unboxed_defaults() -> None:
    reading = DATA["typography"]["profiles"]["reading"]
    assert {
        k: reading[k] for k in ["body", "ui", "metadata", "title", "display"]
    } == dict(body=20, ui=16, metadata=14, title=36, display=48)
    assert DATA["shape"] == dict(radius=0, restingShadow="none", grouping="unboxed")
    assert DATA["spacing"]["profiles"]["reading"]["panel"] == 0
    assert DATA["typography"]["fonts"]["body"].startswith("et-book")


def test_profile_mutation_drives_both_renderers(tmp_path, monkeypatch) -> None:
    """Prove scale/profile edits flow through emitted vars and Quarto defaults."""
    import copy
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "tufte_foundations", ROOT / "scripts/foundations.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = copy.deepcopy(DATA)
    data["typography"]["profiles"]["reading"]["body"] = 24
    data["typography"]["lineHeights"]["reading"] = 1.5
    data["spacing"]["profiles"]["reading"]["group"] = 64
    (tmp_path / "src").mkdir()
    (tmp_path / "_extensions/tufte").mkdir(parents=True)
    (tmp_path / "src/foundations.json").write_text(json.dumps(data))
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["foundations.py", str(tmp_path / "generated")])
    module.main()
    profiles = (tmp_path / "generated/profiles.css").read_text()
    assert "--tf-size-body: 1.5rem;" in profiles
    assert "--tf-type-24: 1.5rem;" in profiles
    assert "--tf-line-reading: 1.5;" in profiles
    assert "--tf-gap-group: 4rem;" in profiles
    for mode in ["light", "dark"]:
        defaults = (tmp_path / f"generated/defaults-{mode}.scss").read_text()
        assert "$font-size-base: 1.5rem !default;" in defaults
        assert "$line-height-base: 1.5 !default;" in defaults
    common = (ROOT / "src/common.css").read_text()
    assert "font-size: var(--tf-size-body)" in common
    assert "line-height: var(--tf-line-reading)" in common
    assert "margin-top: var(--tf-gap-group)" in common


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_semantic_actions_use_safe_existing_pairs(mode: str) -> None:
    """Normal and reversed active/hover pairs reuse approved opaque state colors."""
    data = DATA["modes"][mode]
    role = lambda key: data["swatches"][data["roles"][key]]
    for state, triple in data["states"].items():
        assert contrast(triple["ink"], triple["fill"]) >= 5
        # Reversing this pair supplies the same reserve on hover and active.
        assert contrast(triple["fill"], triple["ink"]) >= 5
        for surface in ["paper", "panel", "code"]:
            assert contrast(triple["ink"], role(surface)) >= 5
        assert contrast(triple["boundary"], role("paper")) >= 3
    assert contrast(role("secondary-action"), role("panel")) >= 5
    assert contrast(role("disabled-ink"), role("disabled-fill")) >= 5


def test_semantic_action_variants_publish_to_both_consumers() -> None:
    """Every filled/outline action and its active/disabled fixture is emitted."""
    common = (ROOT / "src/common.css").read_text()
    fixture = (ROOT / "tests/fixtures/components.qmd").read_text()
    for variant in ["success", "warning", "danger", "info"]:
        assert f"--tf-action-fill: var(--tf-{variant}-fill)" in common
        for prefix in ["", "outline-"]:
            for behavior in ["base", "active", "disabled", "disabled-active"]:
                assert f'id="state-{prefix}{variant}-{behavior}"' in fixture
    assert "--tf-action-boundary: var(--tf-control-boundary)" in common
    assert "html .btn-outline-secondary" in common
    assert "--bs-btn-active-bg: var(--tf-action-ink)" in common
    assert "--bs-btn-disabled-bg: var(--tf-disabled-fill)" in common
    for file in ["tufte.css", "tufte-dark.css", "tufte.scss"]:
        assert common in (ROOT / "_extensions/tufte" / file).read_text()


def test_code_profile_covers_renderer_descendants_without_overwriting_syntax() -> None:
    """Keep code line wrappers at the declared size without flattening token hues."""
    common = (ROOT / "src/common.css").read_text()
    assert "html body #quarto-content main.content pre code span" in common
    assert "font-size: var(--tf-size-code);" in common
    assert "line-height: var(--tf-line-code);" in common
    assert (
        "html body #quarto-content main.content pre code > span[id] { color: var(--tf-code-ink); }"
        in common
    )
    assert "pre code span { color:" not in common
    assert "main.content div.sourceCode { padding: var(--tf-gap-panel); }" in common
    assert DATA["typography"]["profiles"]["reading"]["code"] == 16
    assert DATA["typography"]["lineHeights"]["code"] == 1.5
    assert DATA["spacing"]["profiles"]["reading"]["panel"] == 0
