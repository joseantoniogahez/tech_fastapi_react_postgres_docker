from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from scripts import bootstrap_new_app as bootstrap

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_SCRIPT = REPOSITORY_ROOT / "scripts" / "bootstrap_new_app.py"
SOURCE_REPOSITORY = "https://github.com/example/foundation"
PRISTINE_TEMPLATES = {
    Path("AGENTS.md"): "# Fixture agent guide\n",
    Path("README.md"): (
        "# FastAPI + React + PostgreSQL Docker Template\n"
        "Full-stack template application with JWT authentication and RBAC.\n"
        "`compose.test.yaml` sets `name: tech-tests`\n"
        "`compose.prod.yaml` sets `name: tech-prod`\n"
        "## Use This As a New Project Starter\n\n"
        "Legacy bootstrap commands.\n\n"
        "## Run Full Stack (Docker)\n"
    ),
    Path("backend/README.md"): (
        "`JWT_ISSUER=fastapi-template`\n"
        "`JWT_AUDIENCE=fastapi-template-api`\n"
        "`DB_HOST=system_db`, `DB_NAME=main_db`\n"
        'DB_NAME = "main_db"\n'
        'DB_NAME="main_db"\n'
    ),
    Path(".env_examples"): (
        "API_HOST=system_api\n"
        "JWT_ISSUER=fastapi-template\n"
        "JWT_AUDIENCE=fastapi-template-api\n"
        "DB_HOST=system_db\n"
        "DB_NAME=main_db\n"
        "UI_HOST=frontend\n"
    ),
    Path("compose.yaml"): (
        "name: tech-dev\n"
        "services:\n"
        "  api:\n"
        "    environment:\n"
        "      JWT_ISSUER: ${JWT_ISSUER:-fastapi-template}\n"
        "      JWT_AUDIENCE: ${JWT_AUDIENCE:-fastapi-template-api}\n"
    ),
    Path("compose.test.yaml"): "name: tech-tests\nservices: {}\n",
    Path("compose.prod.yaml"): "name: tech-prod\nservices: {}\n",
    Path("backend/app/core/config/settings.py"): (
        'JWT_ISSUER: str = "fastapi-template"\nJWT_AUDIENCE: str = "fastapi-template-api"\n'
    ),
    Path("frontend/index.html"): "<title>Portal de Acceso</title>\n",
    Path("frontend/src/shared/i18n/ui-text.ts"): (
        "export const UI_TEXT = {\n"
        '  "auth.login.footer.backToLanding": "Inicio",\n'
        '  "landing.badge.portal": "Portal",\n'
        '  "landing.loading.title": "Cargando...",\n'
        '  "landing.subtitle": "Acceso",\n'
        '  "landing.title": "Portal",\n'
        "};\n"
    ),
    Path("frontend/package.json"): '{\n  "name": "frontend",\n  "private": true\n}\n',
    Path("frontend/package-lock.json"): (
        '{\n  "name": "frontend",\n  "lockfileVersion": 3,\n'
        '  "packages": {\n    "": {\n      "name": "frontend"\n    }\n  }\n}\n'
    ),
}
TEMPLATE_PATHS = tuple(PRISTINE_TEMPLATES)
EXPECTED_BOOTSTRAP_PATHS = (set(TEMPLATE_PATHS) - {Path("AGENTS.md")}) | {
    bootstrap.PROVENANCE_RELATIVE_PATH
}


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP_SCRIPT), "--root", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _fixture(root: Path) -> tuple[Path, str]:
    for relative_path, contents in PRISTINE_TEMPLATES.items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="\n") as fixture_file:
            fixture_file.write(contents)
    (root / "docs" / "ai").mkdir(parents=True, exist_ok=True)

    _git(root, "init", "--initial-branch=main")
    _git(root, "config", "user.name", "Bootstrap Contract")
    _git(root, "config", "user.email", "bootstrap@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "pristine fixture")
    return root, _git(root, "rev-parse", "HEAD")


def _digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


def _bootstrap_residue(root: Path) -> list[Path]:
    return sorted(root.rglob(".bootstrap-*"))


def _make_fixture_files_writable(root: Path) -> None:
    if os.name != "nt":
        return
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(stat.S_IREAD | stat.S_IWRITE)


def _identity_args(revision: str) -> tuple[str, ...]:
    return (
        "--source-repository",
        SOURCE_REPOSITORY,
        "--source-revision",
        revision,
        "--app-name",
        "Example Portal",
        "--description",
        "A temporary bootstrap contract fixture.",
    )


def test_bootstrap_preview_on_pristine_fixture_succeeds_without_writes(tmp_path: Path) -> None:
    root, revision = _fixture(tmp_path / "preview")
    before = _digest(root)

    result = _run(root, *_identity_args(revision))

    assert result.returncode == 0, result.stderr
    assert "bootstrap mode: dry-run" in result.stdout
    assert f"template commit: {revision}" in result.stdout
    assert "docs/ai/template_provenance.json" in result.stdout
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


def test_bootstrap_accepts_an_existing_reviewed_tag(tmp_path: Path) -> None:
    root, revision = _fixture(tmp_path / "reviewed-tag")
    _git(root, "tag", "reviewed-v1")
    before = _digest(root)

    result = _run(root, *_identity_args("reviewed-v1"))

    assert result.returncode == 0, result.stderr
    assert "bootstrap mode: dry-run" in result.stdout
    assert f"template commit: {revision}" in result.stdout
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize("revision", ["main", "HEAD"])
def test_bootstrap_rejects_mutable_or_symbolic_revisions_before_writes(
    tmp_path: Path,
    revision: str,
) -> None:
    root, _ = _fixture(tmp_path / revision.lower())
    before = _digest(root)

    result = _run(root, *_identity_args(revision))

    assert result.returncode == 2
    assert "branches and symbolic revisions are not accepted" in result.stderr
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


def test_bootstrap_mismatched_critical_token_fails_before_writes(tmp_path: Path) -> None:
    root, _ = _fixture(tmp_path / "mismatch")
    readme = root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace("# FastAPI", "# Changed"), encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "incompatible fixture")
    revision = _git(root, "rev-parse", "HEAD")
    before = _digest(root)

    result = _run(root, *_identity_args(revision), "--write")

    assert result.returncode == 2
    assert "Expected text not found" in result.stderr
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


def test_bootstrap_write_is_consistent_and_second_write_is_rejected(tmp_path: Path) -> None:
    root, revision = _fixture(tmp_path / "write")

    first = _run(root, *_identity_args(revision), "--write")

    assert first.returncode == 0, first.stderr
    provenance_path = root / bootstrap.PROVENANCE_RELATIVE_PATH
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert provenance["schema_version"] == bootstrap.PROVENANCE_SCHEMA_VERSION
    assert provenance["template_contract_version"] == bootstrap.TEMPLATE_CONTRACT_VERSION
    assert provenance["template_repository"] == SOURCE_REPOSITORY
    assert provenance["requested_revision"] == revision
    assert provenance["template_commit"] == revision
    assert len(provenance["template_tree"]) == 40
    assert provenance["bootstrapped_at_utc"].endswith("Z")
    assert provenance["application"] == {
        "name": "Example Portal",
        "slug": "example-portal",
        "frontend_package_name": "example-portal-frontend",
        "compose_projects": ["example-portal-dev", "example-portal-tests", "example-portal-prod"],
        "jwt_issuer": "example-portal",
        "jwt_audience": "example-portal-api",
    }
    assert provenance["notice"].endswith("is not the pristine template.")

    root_readme = (root / "README.md").read_text(encoding="utf-8")
    assert root_readme.startswith("# Example Portal")
    assert "## Template Origin" in root_readme
    assert "## Use This As a New Project Starter" not in root_readme
    compose = (root / "compose.yaml").read_text(encoding="utf-8")
    assert "name: example-portal-dev" in compose
    assert "${JWT_ISSUER:-example-portal}" in compose
    assert "${JWT_AUDIENCE:-example-portal-api}" in compose
    assert "name: example-portal-tests" in (root / "compose.test.yaml").read_text(encoding="utf-8")
    assert "name: example-portal-prod" in (root / "compose.prod.yaml").read_text(encoding="utf-8")
    env_examples = (root / ".env_examples").read_text(encoding="utf-8")
    assert "API_HOST=example_portal_api" in env_examples
    assert "DB_HOST=example_portal_db" in env_examples
    assert "DB_NAME=example_portal_main" in env_examples
    assert "UI_HOST=example_portal_frontend" in env_examples
    assert "JWT_ISSUER=example-portal" in env_examples
    assert "JWT_AUDIENCE=example-portal-api" in env_examples
    backend_readme = (root / "backend" / "README.md").read_text(encoding="utf-8")
    assert "`JWT_ISSUER=example-portal`" in backend_readme
    assert "`JWT_AUDIENCE=example-portal-api`" in backend_readme
    assert "`DB_HOST=example_portal_db`, `DB_NAME=example_portal_main`" in backend_readme
    settings = (root / "backend" / "app" / "core" / "config" / "settings.py").read_text(encoding="utf-8")
    assert 'JWT_ISSUER: str = "example-portal"' in settings
    assert 'JWT_AUDIENCE: str = "example-portal-api"' in settings
    assert json.loads((root / "frontend/package.json").read_text(encoding="utf-8"))["name"] == (
        "example-portal-frontend"
    )
    package_lock = json.loads((root / "frontend/package-lock.json").read_text(encoding="utf-8"))
    assert package_lock["name"] == "example-portal-frontend"
    assert package_lock["packages"][""]["name"] == "example-portal-frontend"
    assert "<title>Example Portal</title>" in (root / "frontend/index.html").read_text(encoding="utf-8")
    ui_text = (root / "frontend" / "src" / "shared" / "i18n" / "ui-text.ts").read_text(encoding="utf-8")
    assert '"auth.login.footer.backToLanding": "Regresa a Example Portal"' in ui_text
    assert '"landing.badge.portal": "Example Portal"' in ui_text
    assert '"landing.loading.title": "Cargando Example Portal..."' in ui_text
    assert '"landing.subtitle": "Signin to access Example Portal."' in ui_text
    assert '"landing.title": "Example Portal"' in ui_text

    changed_paths = {
        Path(path)
        for path in (
            _git(root, "diff", "--name-only").splitlines()
            + _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
        )
    }
    assert changed_paths == EXPECTED_BOOTSTRAP_PATHS
    for relative_path in EXPECTED_BOOTSTRAP_PATHS:
        assert b"\r\n" not in (root / relative_path).read_bytes()

    before_second = _digest(root)
    second = _run(root, *_identity_args(revision), "--write")
    assert second.returncode == 2
    assert "Bootstrap provenance already exists" in second.stderr
    assert _digest(root) == before_second


def test_bootstrap_escapes_visible_text_and_preserves_explicit_jwt_identifiers(tmp_path: Path) -> None:
    root, revision = _fixture(tmp_path / "escaped-text")
    document_title = 'Foundation <Portal> & "Admin"'
    landing_title = 'Use C:\\Portal "Admin"'
    jwt_issuer = "https://Issuer.Example/App"
    jwt_audience = "URN:Example:API"

    result = _run(
        root,
        *_identity_args(revision),
        "--document-title",
        document_title,
        "--landing-title",
        landing_title,
        "--jwt-issuer",
        jwt_issuer,
        "--jwt-audience",
        jwt_audience,
        "--write",
    )

    assert result.returncode == 0, result.stderr
    assert "<title>Foundation &lt;Portal&gt; &amp; &quot;Admin&quot;</title>" in (
        root / "frontend" / "index.html"
    ).read_text(encoding="utf-8")
    ui_text = (root / "frontend" / "src" / "shared" / "i18n" / "ui-text.ts").read_text(encoding="utf-8")
    assert f'"landing.title": {json.dumps(landing_title, ensure_ascii=False)}' in ui_text
    env_examples = (root / ".env_examples").read_text(encoding="utf-8")
    assert f"JWT_ISSUER={jwt_issuer}" in env_examples
    assert f"JWT_AUDIENCE={jwt_audience}" in env_examples


def test_bootstrap_rejects_control_characters_before_writes(tmp_path: Path) -> None:
    root, revision = _fixture(tmp_path / "control-character")
    before = _digest(root)

    result = _run(root, *_identity_args(revision), "--landing-title", "invalid\nvalue", "--write")

    assert result.returncode == 2
    assert "single line without control characters" in result.stderr
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("extra_args", "diagnostic"),
    [
        (("--slug", "a" * 49), "slug must use lowercase"),
        (("--jwt-issuer", "${unsafe}"), "safe case-preserving identifier"),
        (("--document-title", "a" * 201), "at most 200 characters"),
    ],
)
def test_bootstrap_rejects_unsafe_or_oversized_identity_values_before_writes(
    tmp_path: Path,
    extra_args: tuple[str, str],
    diagnostic: str,
) -> None:
    root, revision = _fixture(tmp_path / hashlib.sha256(repr(extra_args).encode()).hexdigest()[:8])
    before = _digest(root)

    result = _run(root, *_identity_args(revision), *extra_args, "--write")

    assert result.returncode == 2
    assert diagnostic in result.stderr
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize("invalid_lock", ["not-json", '{"name": "frontend", "packages": {}}'])
def test_bootstrap_rejects_an_incompatible_package_lock_before_writes(
    tmp_path: Path,
    invalid_lock: str,
) -> None:
    root, _ = _fixture(tmp_path / hashlib.sha256(invalid_lock.encode()).hexdigest()[:8])
    lock_path = root / "frontend" / "package-lock.json"
    lock_path.write_text(invalid_lock + "\n", encoding="utf-8")
    _git(root, "add", "frontend/package-lock.json")
    _git(root, "commit", "-m", "incompatible lock")
    revision = _git(root, "rev-parse", "HEAD")
    before = _digest(root)

    result = _run(root, *_identity_args(revision), "--write")

    assert result.returncode == 2
    assert "Expected" in result.stderr
    assert "package-lock.json" in result.stderr
    assert _digest(root) == before
    assert _git(root, "status", "--porcelain") == ""


def test_current_template_snapshot_exposes_the_exact_bootstrap_surface() -> None:
    if (REPOSITORY_ROOT / bootstrap.PROVENANCE_RELATIVE_PATH).exists():
        pytest.skip("Exact bootstrap-surface validation applies only to the pristine template snapshot.")

    parser = bootstrap.build_parser()
    args = parser.parse_args(
        [
            "--source-repository",
            SOURCE_REPOSITORY,
            "--source-revision",
            "1" * 40,
            "--app-name",
            "Compatibility Fixture",
        ]
    )
    config = bootstrap.build_config(args)
    source = bootstrap.SourceSnapshot(SOURCE_REPOSITORY, "1" * 40, "1" * 40, "2" * 40)

    changes = bootstrap.collect_changes(REPOSITORY_ROOT, config, source)

    assert {change.path.relative_to(REPOSITORY_ROOT) for change in changes} == EXPECTED_BOOTSTRAP_PATHS
    root_readme = next(change.after for change in changes if change.path == REPOSITORY_ROOT / "README.md")
    assert "## Template Origin" in root_readme
    assert "## Use This As a New Project Starter" not in root_readme


def test_bootstrap_rejects_revision_mismatch_and_dirty_checkout(tmp_path: Path) -> None:
    root, revision = _fixture(tmp_path / "preflight")
    (root / "review-marker.txt").write_text("newer snapshot\n", encoding="utf-8")
    _git(root, "add", "review-marker.txt")
    _git(root, "commit", "-m", "newer fixture snapshot")
    current_revision = _git(root, "rev-parse", "HEAD")
    before_mismatch = _digest(root)

    mismatch = _run(root, *_identity_args(revision))
    assert mismatch.returncode == 2
    assert f"Source revision resolves to {revision}, but checkout HEAD is {current_revision}" in mismatch.stderr
    assert _digest(root) == before_mismatch
    assert _git(root, "status", "--porcelain") == ""

    (root / "README.md").write_text("dirty\n", encoding="utf-8")
    dirty = _run(root, *_identity_args(current_revision))
    assert dirty.returncode == 2
    assert "clean compatible checkout" in dirty.stderr


def test_bootstrap_atomic_write_restores_a_late_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "atomic"
    root.mkdir()
    first = root / "first.txt"
    second = root / "second.txt"
    created = root / "created.txt"
    first.write_text("first-before\n", encoding="utf-8")
    second.write_text("second-before\n", encoding="utf-8")
    changes = [
        bootstrap.FileChange(first, "first-before\n", "first-after\n"),
        bootstrap.FileChange(second, "second-before\n", "second-after\n"),
        bootstrap.FileChange(created, None, "created-after\n"),
    ]
    original_link = bootstrap.os.link

    def fail_created_install(source: Path, target: Path) -> None:
        if Path(target) == created:
            raise OSError("synthetic late failure")
        original_link(source, target)

    monkeypatch.setattr(bootstrap.os, "link", fail_created_install)

    with pytest.raises(bootstrap.BootstrapError, match="previous files restored"):
        bootstrap.apply_changes(changes, root.resolve())

    assert first.read_text(encoding="utf-8") == "first-before\n"
    assert second.read_text(encoding="utf-8") == "second-before\n"
    assert not created.exists()
    assert _bootstrap_residue(root) == []


def test_bootstrap_replacement_preserves_target_mode(tmp_path: Path) -> None:
    root = tmp_path / "mode-preservation"
    root.mkdir()
    target = root / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    target.chmod(0o640)
    expected_mode = stat.S_IMODE(target.stat().st_mode)

    bootstrap.apply_changes(
        [bootstrap.FileChange(target, "before\n", "after\n")],
        root.resolve(),
    )

    assert target.read_text(encoding="utf-8") == "after\n"
    assert stat.S_IMODE(target.stat().st_mode) == expected_mode
    assert _bootstrap_residue(root) == []


def test_bootstrap_install_source_is_adjacent_to_a_nested_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "adjacent-install-source"
    root.mkdir()
    target = root / "nested" / "deeper" / "created.txt"
    observed_links: list[tuple[Path, Path]] = []
    original_link = bootstrap.os.link

    def observe_exclusive_install(source: Path, destination: Path) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        observed_links.append((source_path, destination_path))
        original_link(source, destination)

    monkeypatch.setattr(bootstrap.os, "link", observe_exclusive_install)

    bootstrap.apply_changes(
        [bootstrap.FileChange(target, None, "created\n")],
        root.resolve(),
    )

    assert len(observed_links) == 1
    install_source, destination = observed_links[0]
    assert destination == target
    assert install_source.parent == target.parent
    assert install_source.name.startswith(".bootstrap-install-")
    assert target.read_text(encoding="utf-8") == "created\n"
    if os.name == "nt":
        acl = subprocess.run(
            ["icacls", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert acl.returncode == 0, acl.stderr
        assert "(I)" in acl.stdout
    assert _bootstrap_residue(root) == []


def test_bootstrap_reports_and_retains_an_install_source_that_cleanup_cannot_remove(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "install-source-cleanup-failure"
    root.mkdir()
    target = root / "nested" / "created.txt"
    original_unlink = Path.unlink

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("synthetic fsync failure")

    def fail_install_source_unlink(
        path: Path,
        missing_ok: bool = False,
    ) -> None:
        if path.name.startswith(".bootstrap-install-"):
            raise OSError("synthetic install-source cleanup failure")
        original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(bootstrap.os, "fsync", fail_fsync)
    monkeypatch.setattr(Path, "unlink", fail_install_source_unlink)

    with pytest.raises(bootstrap.BootstrapError, match="rollback was incomplete"):
        bootstrap.apply_changes(
            [bootstrap.FileChange(target, None, "created\n")],
            root.resolve(),
        )

    assert not target.exists()
    residue = _bootstrap_residue(root)
    install_sources = [path for path in residue if path.name.startswith(".bootstrap-install-")]
    transactions = [path for path in residue if path.parent == root]
    assert len(install_sources) == 1
    assert install_sources[0].parent == target.parent
    assert install_sources[0].read_text(encoding="utf-8") == "created\n"
    assert len(transactions) == 1
    assert (transactions[0] / "stage" / "nested" / "created.txt").read_text(encoding="utf-8") == (
        "created\n"
    )

    _make_fixture_files_writable(root)
    original_unlink(install_sources[0])
    shutil.rmtree(transactions[0])
    assert _bootstrap_residue(root) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX umask semantics")
def test_bootstrap_new_target_mode_honors_the_process_umask(tmp_path: Path) -> None:
    root = tmp_path / "new-target-umask"
    root.mkdir()
    target = root / "created.txt"
    previous_umask = os.umask(0o027)
    try:
        bootstrap.apply_changes(
            [bootstrap.FileChange(target, None, "created\n")],
            root.resolve(),
        )
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    assert _bootstrap_residue(root) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows readonly replacement semantics")
def test_bootstrap_replaces_a_readonly_target_and_preserves_its_mode(tmp_path: Path) -> None:
    root = tmp_path / "readonly-replacement"
    root.mkdir()
    target = root / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    target.chmod(stat.S_IREAD)
    expected_mode = stat.S_IMODE(target.stat().st_mode)

    try:
        bootstrap.apply_changes(
            [bootstrap.FileChange(target, "before\n", "after\n")],
            root.resolve(),
        )

        assert target.read_text(encoding="utf-8") == "after\n"
        assert stat.S_IMODE(target.stat().st_mode) == expected_mode
        assert _bootstrap_residue(root) == []
    finally:
        _make_fixture_files_writable(root)


@pytest.mark.skipif(os.name != "nt", reason="Windows readonly rollback semantics")
def test_bootstrap_restores_a_readonly_target_after_a_late_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "readonly-rollback"
    root.mkdir()
    readonly = root / "readonly.txt"
    trigger = root / "trigger.txt"
    readonly.write_text("before\n", encoding="utf-8")
    readonly.chmod(stat.S_IREAD)
    expected_mode = stat.S_IMODE(readonly.stat().st_mode)
    original_link = bootstrap.os.link

    def fail_late_install(source: Path, destination: Path) -> None:
        if Path(destination) == trigger:
            raise OSError("synthetic late failure")
        original_link(source, destination)

    monkeypatch.setattr(bootstrap.os, "link", fail_late_install)

    try:
        with pytest.raises(bootstrap.BootstrapError, match="previous files restored"):
            bootstrap.apply_changes(
                [
                    bootstrap.FileChange(readonly, "before\n", "after\n"),
                    bootstrap.FileChange(trigger, None, "trigger\n"),
                ],
                root.resolve(),
            )

        assert readonly.read_text(encoding="utf-8") == "before\n"
        assert stat.S_IMODE(readonly.stat().st_mode) == expected_mode
        assert not trigger.exists()
        assert _bootstrap_residue(root) == []
    finally:
        _make_fixture_files_writable(root)


def test_bootstrap_atomic_write_rejects_targets_changed_after_preflight(tmp_path: Path) -> None:
    root = tmp_path / "changed"
    root.mkdir()
    existing = root / "existing.txt"
    created = root / "created.txt"
    existing.write_text("before\n", encoding="utf-8")
    existing_change = bootstrap.FileChange(existing, "before\n", "after\n")
    created_change = bootstrap.FileChange(created, None, "created\n")

    existing.write_text("concurrent\n", encoding="utf-8")
    with pytest.raises(bootstrap.BootstrapError, match="changed after preflight"):
        bootstrap.apply_changes([existing_change], root.resolve())
    assert existing.read_text(encoding="utf-8") == "concurrent\n"

    created.write_text("concurrent\n", encoding="utf-8")
    with pytest.raises(bootstrap.BootstrapError, match="appeared after preflight"):
        bootstrap.apply_changes([created_change], root.resolve())
    assert created.read_text(encoding="utf-8") == "concurrent\n"
    assert _bootstrap_residue(root) == []


def test_bootstrap_revalidates_each_target_immediately_before_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "commit-race"
    root.mkdir()
    first = root / "first.txt"
    second = root / "second.txt"
    first.write_text("first-before\n", encoding="utf-8")
    second.write_text("second-before\n", encoding="utf-8")
    changes = [
        bootstrap.FileChange(first, "first-before\n", "first-after\n"),
        bootstrap.FileChange(second, "second-before\n", "second-after\n"),
    ]
    original_link = bootstrap.os.link

    def change_second_after_first_install(source: Path, target: Path) -> None:
        original_link(source, target)
        if Path(target) == first:
            second.write_text("concurrent\n", encoding="utf-8")

    monkeypatch.setattr(bootstrap.os, "link", change_second_after_first_install)

    with pytest.raises(bootstrap.BootstrapError, match="changed after preflight"):
        bootstrap.apply_changes(changes, root.resolve())

    assert first.read_text(encoding="utf-8") == "first-before\n"
    assert second.read_text(encoding="utf-8") == "concurrent\n"
    assert _bootstrap_residue(root) == []


def test_bootstrap_never_overwrites_a_new_target_created_during_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "new-target-race"
    root.mkdir()
    created = root / "created.txt"
    change = bootstrap.FileChange(created, None, "bootstrap\n")
    original_link = bootstrap.os.link

    def create_target_before_exclusive_install(source: Path, target: Path) -> None:
        Path(target).write_text("concurrent\n", encoding="utf-8")
        original_link(source, target)

    monkeypatch.setattr(bootstrap.os, "link", create_target_before_exclusive_install)

    with pytest.raises(bootstrap.BootstrapError, match="previous files restored"):
        bootstrap.apply_changes([change], root.resolve())

    assert created.read_text(encoding="utf-8") == "concurrent\n"
    assert _bootstrap_residue(root) == []


def test_bootstrap_preserves_a_concurrent_target_and_retains_its_original_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "rollback-collision"
    root.mkdir()
    target = root / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    change = bootstrap.FileChange(target, "before\n", "after\n")
    original_link = bootstrap.os.link
    collision_created = False

    def create_target_after_backup(source: Path, destination: Path) -> None:
        nonlocal collision_created
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            destination_path == target
            and source_path.name.startswith(".bootstrap-install-")
            and not collision_created
        ):
            collision_created = True
            target.write_text("concurrent\n", encoding="utf-8")
        original_link(source, destination)

    monkeypatch.setattr(bootstrap.os, "link", create_target_after_backup)

    with pytest.raises(bootstrap.BootstrapError, match="rollback was incomplete"):
        bootstrap.apply_changes([change], root.resolve())

    assert target.read_text(encoding="utf-8") == "concurrent\n"
    retained = _bootstrap_residue(root)
    assert len(retained) == 1
    backup = retained[0] / "backup" / "target.txt"
    assert backup.read_text(encoding="utf-8") == "before\n"


def test_bootstrap_detects_a_metadata_only_race_before_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "mode-race-before-backup"
    root.mkdir()
    target = root / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    target.chmod(stat.S_IREAD | stat.S_IWRITE if os.name == "nt" else 0o640)
    raced_mode: int | None = None
    original_replace = bootstrap.os.replace
    race_injected = False

    def change_mode_at_backup(source: Path, destination: Path) -> None:
        nonlocal race_injected, raced_mode
        if Path(source) == target and "backup" in Path(destination).parts and not race_injected:
            race_injected = True
            target.chmod(stat.S_IREAD if os.name == "nt" else 0o600)
            raced_mode = stat.S_IMODE(target.stat().st_mode)
        original_replace(source, destination)

    monkeypatch.setattr(bootstrap.os, "replace", change_mode_at_backup)

    try:
        with pytest.raises(bootstrap.BootstrapError, match="changed during commit"):
            bootstrap.apply_changes(
                [bootstrap.FileChange(target, "before\n", "after\n")],
                root.resolve(),
            )

        assert raced_mode is not None
        assert target.read_text(encoding="utf-8") == "before\n"
        assert stat.S_IMODE(target.stat().st_mode) == raced_mode
        assert _bootstrap_residue(root) == []
    finally:
        _make_fixture_files_writable(root)


def test_bootstrap_detects_a_metadata_only_race_before_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "mode-race-before-rollback"
    root.mkdir()
    target = root / "target.txt"
    trigger = root / "trigger.txt"
    target.write_text("before\n", encoding="utf-8")
    target.chmod(stat.S_IREAD | stat.S_IWRITE if os.name == "nt" else 0o640)
    original_mode = stat.S_IMODE(target.stat().st_mode)
    raced_mode: int | None = None
    original_link = bootstrap.os.link

    def fail_after_changing_installed_mode(source: Path, destination: Path) -> None:
        nonlocal raced_mode
        if Path(destination) == trigger:
            target.chmod(stat.S_IREAD if os.name == "nt" else 0o600)
            raced_mode = stat.S_IMODE(target.stat().st_mode)
            raise OSError("synthetic late failure after metadata race")
        original_link(source, destination)

    monkeypatch.setattr(bootstrap.os, "link", fail_after_changing_installed_mode)

    try:
        with pytest.raises(bootstrap.BootstrapError, match="rollback was incomplete"):
            bootstrap.apply_changes(
                [
                    bootstrap.FileChange(target, "before\n", "after\n"),
                    bootstrap.FileChange(trigger, None, "trigger\n"),
                ],
                root.resolve(),
            )

        assert raced_mode is not None
        assert target.read_text(encoding="utf-8") == "after\n"
        assert stat.S_IMODE(target.stat().st_mode) == raced_mode
        retained = _bootstrap_residue(root)
        assert len(retained) == 1
        backup = retained[0] / "backup" / "target.txt"
        assert backup.read_text(encoding="utf-8") == "before\n"
        assert stat.S_IMODE(backup.stat().st_mode) == original_mode
    finally:
        _make_fixture_files_writable(root)


def test_bootstrap_retains_backups_and_continues_after_a_restore_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "restore-failure"
    root.mkdir()
    first = root / "first.txt"
    second = root / "second.txt"
    trigger = root / "trigger.txt"
    first.write_text("first-before\n", encoding="utf-8")
    second.write_text("second-before\n", encoding="utf-8")
    changes = [
        bootstrap.FileChange(first, "first-before\n", "first-after\n"),
        bootstrap.FileChange(second, "second-before\n", "second-after\n"),
        bootstrap.FileChange(trigger, None, "trigger\n"),
    ]
    original_link = bootstrap.os.link

    def fail_late_install_and_second_restore(source: Path, target: Path) -> None:
        source_path = Path(source)
        target_path = Path(target)
        if target_path == trigger:
            raise OSError("synthetic install failure")
        if "backup" in source_path.parts and target_path == second:
            raise OSError("synthetic restore failure")
        original_link(source, target)

    monkeypatch.setattr(bootstrap.os, "link", fail_late_install_and_second_restore)

    with pytest.raises(bootstrap.BootstrapError, match="recovery data was retained"):
        bootstrap.apply_changes(changes, root.resolve())

    assert first.read_text(encoding="utf-8") == "first-before\n"
    assert not second.exists()
    assert not trigger.exists()
    retained = _bootstrap_residue(root)
    assert len(retained) == 1
    second_backup = retained[0] / "backup" / "second.txt"
    assert second_backup.read_text(encoding="utf-8") == "second-before\n"
    assert not (retained[0] / "backup" / "first.txt").exists()

    original_link(second_backup, second)
    second_backup.unlink()
    shutil.rmtree(retained[0])
    assert second.read_text(encoding="utf-8") == "second-before\n"


def test_bootstrap_restores_the_batch_after_keyboard_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "interrupt"
    root.mkdir()
    first = root / "first.txt"
    second = root / "second.txt"
    first.write_text("first-before\n", encoding="utf-8")
    second.write_text("second-before\n", encoding="utf-8")
    changes = [
        bootstrap.FileChange(first, "first-before\n", "first-after\n"),
        bootstrap.FileChange(second, "second-before\n", "second-after\n"),
    ]
    original_link = bootstrap.os.link

    def interrupt_second_install(source: Path, target: Path) -> None:
        original_link(source, target)
        if Path(target) == second and Path(source).name.startswith(".bootstrap-install-"):
            raise KeyboardInterrupt

    monkeypatch.setattr(bootstrap.os, "link", interrupt_second_install)

    with pytest.raises(bootstrap.BootstrapError, match="previous files restored"):
        bootstrap.apply_changes(changes, root.resolve())

    assert first.read_text(encoding="utf-8") == "first-before\n"
    assert second.read_text(encoding="utf-8") == "second-before\n"
    assert _bootstrap_residue(root) == []
