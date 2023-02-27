from pathlib import Path

import pytest

from poetry_check_existing_plugin.plugin import PoetryProjectExt

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize("project_dir, version, name", [
    (DATA_DIR / "v1", "0.1.0", "poetry-check-existing-plugin"),
    (DATA_DIR / "v2", "2.0.1", "version-two-project-name"),
])
def test_read_project(project_dir, version, name) -> None:
    """Test that read_project_version() returns the correct version."""
    poetry_project = PoetryProjectExt.from_dir(project_dir)
    assert poetry_project.name == name
    assert poetry_project.version == version


@pytest.mark.parametrize("project_dir, repository, url", [
    (DATA_DIR / "v1", None, "https://upload.pypi.org/pypi/poetry-check-existing-plugin/json"),
    (DATA_DIR / "v2", None, "https://upload.pypi.org/pypi/version-two-project-name/json"),
    (DATA_DIR / "v2", "pypi-artifactory",
     "https://artifactory.example.com/artifactory/api/pypi/pypi-artifactory/version-two-project-name/json"),
])
def test_get_url(project_dir, repository, url) -> None:
    """Test that read_project_version() returns the correct version."""
    poetry_project = PoetryProjectExt.from_dir(project_dir)
    project_repo, project_url = poetry_project.get_url(repository)
    assert project_repo == repository if repository else "pypi"
    assert project_url == url
