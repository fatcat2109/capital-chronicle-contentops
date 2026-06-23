from pathlib import Path
from live_contentops import operator_browser_lab as lab


def test_sensitive_paths_are_gitignored():
    text = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in [".env", ".env.local", "operator-browser-profiles/", ".browser-profiles/", ".oauth-token-cache/", ".oauth-callback-cache/", "*.client_secret.json", "client_secret*.json", "*oauth*token*.json", "*credential*cache*.json", "*.local.secret", "*.local.secrets.json"]:
        assert pattern in text


def test_default_profile_root_outside_repo():
    assert not lab.is_path_inside(lab.get_default_profile_root(), Path.cwd())


def test_repo_local_profile_policy_marks_sensitive(tmp_path: Path):
    profile = tmp_path / "operator-browser-profiles" / "contentops-social-main"
    policy = lab.validate_profile_policy(profile, tmp_path)
    assert policy["profile_inside_repo"] is True
    assert policy["profile_root_class"] == "repo_local_sensitive_override_requires_gitignore"
    assert policy["profile_path_persistable_in_git"] is False
