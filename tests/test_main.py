from pathlib import Path

import pytest
from pyartifactory.models.artifact import (
    ArtifactListFolderResponse,
    ArtifactListResponse,
)

from poetry_check_existing_plugin.artifactory import ArtifactoryClient
from poetry_check_existing_plugin.plugin import PoetryProjectExt

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def artifactory_client():
    art = ArtifactoryClient(
        "https://artifactory.example.com/artifactory", "user", "password"
    )
    return art


@pytest.mark.parametrize(
    "project_dir, version, name",
    [
        (DATA_DIR / "v1", "0.1.0", "poetry-check-existing-plugin"),
        (DATA_DIR / "v2", "2.0.1", "version-two-project-name"),
    ],
)
def test_read_project(project_dir, version, name) -> None:
    """Test that read_project_version() returns the correct version."""
    poetry_project = PoetryProjectExt.from_dir(project_dir)
    assert poetry_project.name == name
    assert poetry_project.version == version


@pytest.mark.parametrize(
    "project_dir, repository, url",
    [
        (
            DATA_DIR / "v1",
            None,
            "https://pypi.org/pypi/poetry-check-existing-plugin/json",
        ),
        (
            DATA_DIR / "v2",
            None,
            "https://pypi.org/pypi/version-two-project-name/json",
        ),
        (
            DATA_DIR / "v2",
            "pypi-artifactory",
            "https://artifactory.example.com/artifactory/api/pypi/pypi-artifactory/version-two-project-name/json",
        ),
    ],
)
def test_get_url(project_dir, repository, url) -> None:
    """Test that read_project_version() returns the correct version."""
    poetry_project = PoetryProjectExt.from_dir(project_dir)
    project_repo, project_url = poetry_project.get_url(repository)
    assert project_repo == repository if repository else "pypi"
    assert project_url == url


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://artifactory.example.com/artifactory",
            "https://artifactory.example.com/artifactory",
        ),
        (
            "https://artifactory.example.com/artifactory/api/pypy/pypi-local/package",
            "https://artifactory.example.com/artifactory",
        ),
        (
            "https://artifactory.example.com/",
            "https://artifactory.example.com/artifactory",
        ),
    ],
)
def test_artifactory_url(url, expected):
    assert ArtifactoryClient.get_base_url(url) == expected


def test_artifactory_releases(artifactory_client, mocker):
    repo = "pypi-local"
    package = "my-package"
    artifactory_client.artifacts.list = mocker.Mock(
        return_value=ArtifactListResponse(
            uri=f"https://artifactory.example.com/artifactory/api/storage/{repo}/{package}",
            created="2023-02-08T15:00:00.000+0000",
            files=[
                ArtifactListFolderResponse(
                    uri="/0.1.0",
                    size=-1,
                    folder=True,
                    lastModified="2023-02-08T15:00:00.000+0000",
                ),
                ArtifactListFolderResponse(
                    uri="/0.1.1",
                    size=-1,
                    folder=True,
                    lastModified="2023-02-08T15:00:00.000+0000",
                ),
                ArtifactListFolderResponse(
                    uri="/0.1.2",
                    size=-1,
                    folder=True,
                    lastModified="2023-02-08T15:00:00.000+0000",
                ),
                ArtifactListFolderResponse(
                    uri="/2.0.1",
                    size=-1,
                    folder=True,
                    lastModified="2023-02-08T15:00:00.000+0000",
                ),
            ],
        )
    )

    res = artifactory_client.get_releases(
        "pypi-artifactory", "version-two-project-name"
    )
    assert res == ["0.1.0", "0.1.1", "0.1.2", "2.0.1"]

    artifactory_client.artifacts.list.assert_called_once_with(
        "pypi-artifactory/version-two-project-name", recursive=False, list_folders=True
    )
