from __future__ import annotations

import subprocess

import pytest

from scripts import release_validation


def test_release_runner_refuses_local_execution_before_launching_commands(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    def unexpected_command(*args, **kwargs):
        pytest.fail("Local release invocation must not launch commands or containers")

    monkeypatch.setattr(release_validation.subprocess, "run", unexpected_command)
    with pytest.raises(RuntimeError, match="Hosted release runner required"):
        release_validation.main()


def test_release_runner_rejects_docker_drift_before_creating_services(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("RELEASE_SOURCE_REPOSITORY", "https://github.com/example/template")
    monkeypatch.setattr(release_validation.platform, "system", lambda: "Linux")
    monkeypatch.setattr(release_validation.platform, "python_version", lambda: "3.14.6")

    def observed_version(*args):
        assert args[:2] == ("docker", "version")
        return "29.7.2/29.7.2"

    monkeypatch.setattr(release_validation, "run", observed_version)
    with pytest.raises(RuntimeError, match="Docker matrix drift"):
        release_validation.main()


def test_failed_command_redacts_generated_credentials_from_diagnostics(monkeypatch, capsys) -> None:
    fixture_secret = "synthetic-release-redaction-probe"  # pragma: allowlist secret
    monkeypatch.setattr(release_validation, "SECRET_VALUES", [fixture_secret])
    monkeypatch.setattr(
        release_validation.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, f"failed {fixture_secret}"),
    )
    with pytest.raises(RuntimeError, match="failed") as failure:
        release_validation.run("probe")
    output = capsys.readouterr().out
    assert fixture_secret not in output
    assert fixture_secret not in str(failure.value)
    assert "[redacted]" in output


def test_source_repository_defaults_to_current_hosted_repository(monkeypatch) -> None:
    monkeypatch.delenv("RELEASE_SOURCE_REPOSITORY", raising=False)
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.example.test/")
    monkeypatch.setenv("GITHUB_REPOSITORY", "team/template")
    assert release_validation.resolve_source_repository() == "https://github.example.test/team/template"


def test_source_repository_override_takes_precedence(monkeypatch) -> None:
    monkeypatch.setenv("RELEASE_SOURCE_REPOSITORY", "https://github.com/team/default")
    assert release_validation.resolve_source_repository("https://example.test/team/template/") == (
        "https://example.test/team/template"
    )


@pytest.mark.parametrize("source", [
    "git@github.com:team/template.git",
    "https://user:password@example.test/repo",  # pragma: allowlist secret
    "https://example.test/repo?token=private", "https://example.test/repo#branch", "file:///tmp/repo",
])
def test_source_repository_rejects_credentials_and_non_http_urls(source) -> None:
    with pytest.raises(RuntimeError, match="credential-free HTTP"):
        release_validation.resolve_source_repository(source)


def test_source_repository_requires_an_explicit_or_hosted_origin(monkeypatch) -> None:
    monkeypatch.delenv("RELEASE_SOURCE_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    with pytest.raises(RuntimeError, match="Source repository URL"):
        release_validation.resolve_source_repository()


def test_derived_application_runs_services_without_attempting_second_bootstrap(monkeypatch, tmp_path) -> None:
    provenance = tmp_path / "docs/ai/template_provenance.json"
    provenance.parent.mkdir(parents=True)
    provenance.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(release_validation, "ROOT", tmp_path)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(release_validation.platform, "system", lambda: "Linux")
    monkeypatch.setattr(release_validation.platform, "python_version", lambda: "3.14.6")
    gates = []
    monkeypatch.setattr(release_validation, "npm_policy", lambda root: gates.append("npm"))
    monkeypatch.setattr(release_validation, "service_gate", lambda root, python: gates.append("services"))
    monkeypatch.setattr(release_validation, "image_gate", lambda root: gates.append("images"))

    def command(*args):
        if args[:2] == ("docker", "version"):
            return "29.6.2/29.6.2"
        if args[:2] == ("docker", "compose"):
            return "5.3.1"
        if args == ("git", "status", "--porcelain"):
            return ""
        if args[:2] == ("git", "rev-parse"):
            return "a" * 40
        pytest.fail(f"Unexpected command: {args}")

    def unexpected_fixture(*args, **kwargs):
        pytest.fail("An existing application must not create a second bootstrap fixture")

    monkeypatch.setattr(release_validation, "run", command)
    monkeypatch.setattr(release_validation.tempfile, "mkdtemp", unexpected_fixture)
    release_validation.main("https://github.com/example/application")
    assert gates == ["npm", "services", "images"]
