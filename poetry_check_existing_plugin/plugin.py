import logging
from pathlib import Path
from urllib.parse import urljoin

import requests
from cleo.commands.command import Command
from cleo.helpers import argument, option
from poetry.factory import Factory
from poetry.plugins.application_plugin import ApplicationPlugin
from poetry.poetry import Poetry
from poetry.publishing.uploader import Uploader
from poetry.utils.authenticator import Authenticator

from poetry_check_existing_plugin.artifactory import ArtifactoryClient

logger = logging.getLogger(__name__)


def _make_request(session: requests.Session, url: str, json: bool = True) -> dict | str:
    headers = {"Accept": "application/json"} if json else None
    response = session.get(url, headers=headers)
    response.raise_for_status()
    return response.json() if json else response.content.decode()


def _get_releases(session: requests.Session, url: str) -> list[str]:
    response = _make_request(session, url)
    return list(response["releases"].keys())


class PoetryProjectExt:
    def __init__(self, poetry_project: Poetry) -> None:
        self._poetry = poetry_project
        self._uploader = Uploader(
            self._poetry, self._poetry.config.get("http-basic", {})
        )
        self._authenticator = Authenticator(self._poetry.config)

    @classmethod
    def from_dir(cls, project_dir: str):
        return cls(Factory().create_poetry(cwd=project_dir))

    @property
    def name(self) -> str:
        return self._poetry.package.name

    @property
    def version(self) -> str:
        return self._poetry.package.version.text

    def get_url(self, repository_name: str) -> str:
        if not repository_name:
            url = "https://pypi.org/pypi/"
            repository_name = "pypi"
        else:
            # Retrieving config information
            url = self._poetry.config.get(f"repositories.{repository_name}.url")
            if url is None:
                raise RuntimeError(f"Repository {repository_name} is not defined")

        # https://github.com/pypa/twine/blob/a6dd69c79f7b5abfb79022092a5d3776a499e31b/twine/repository.py#L202
        if not url.endswith("/"):
            url += "/"
        url = urljoin(url, f"{self.name}/json")
        return repository_name, url

    def check_existing(
        self,
        repository: str | None,
        username: str | None,
        password: str | None,
        cert: str | None = None,
        client_cert: str | None = None,
        artifactory: bool = False,
    ) -> None:
        repository_name, url = self.get_url(repository_name=repository)

        if not (username and password):
            # Check if we have a token first
            token = self._authenticator.get_pypi_token(repository_name)
            if token:
                logger.debug("Found an API token for %s.", repository_name)
                username = "__token__"
                password = token
            else:
                auth = self._authenticator.get_http_auth(repository_name)
                if auth:
                    logger.debug(
                        "Found authentication information for %s.", repository_name
                    )
                    username = auth.username
                    password = auth.password

        certificates = self._authenticator.get_certs_for_repository(repository_name)
        resolved_cert = cert or certificates.cert or certificates.verify
        resolved_client_cert = client_cert or certificates.client_cert

        self._uploader.auth(username, password)

        session = self._uploader.make_session()
        session.verify = (
            str(resolved_cert) if isinstance(resolved_cert, Path) else resolved_cert
        )

        if resolved_client_cert:
            session.cert = str(resolved_client_cert)

        try:
            if artifactory:
                art = ArtifactoryClient(url, username=username, password=password)
                releases = art.get_releases(repository_name, self.name)
            else:
                releases = _get_releases(session, url)

            if self.version in releases:
                raise RuntimeError(
                    f"Package version {self.version} already exists in {repository_name}"
                )
        except Exception as e:
            logger.error("Error while checking existing package version", exc_info=e)
            raise

        finally:
            session.close()

        return releases


class CheckExistingCommand(Command):
    name = "check-existing"
    description = "Checks if the package version already exists in the pypi index"
    arguments = [
        argument(
            "directory",
            "The pyproject.toml which contains package version",
            optional=True,
            default=str(Path.cwd()),
        ),
    ]
    options = [
        option("repository", "r", "The repository to use", flag=False, default=None),
        option(
            "artifactory",
            "A",
            "Whether to use pyartifactory to interact with pypi deployed in Artifactory",
            flag=True,
        ),
        option("username", "u", "The username to use", flag=False, default=None),
        option("password", "p", "The password to use", flag=False, default=None),
        option("cert", "c", "The path to a CA bundle to use", flag=False, default=None),
        option(
            "client-cert",
            "C",
            "The path to a client certificate to use",
            flag=False,
            default=None,
        ),
    ]

    def handle(self) -> int:
        self.line("<info>Checking if package version already exists...</info>")

        poetry_dir = self.argument("directory")
        poetry_project = PoetryProjectExt.from_dir(poetry_dir)
        self.line(
            f"<info>Package name: {poetry_project.name}, version: {poetry_project.version}</info>"
        )

        poetry_project.check_existing(
            repository=self.option("repository"),
            username=self.option("username"),
            password=self.option("password"),
            cert=self.option("cert"),
            client_cert=self.option("client-cert"),
            artifactory=self.option("artifactory"),
        )

        self.line(
            f"<info>{poetry_project.name}=={poetry_project.version} does not exist in the index</info>"
        )

        return 0


def factory():
    return CheckExistingCommand()


class CheckExistingPlugin(ApplicationPlugin):
    def activate(self, application):
        application.command_loader.register_factory("check-existing", factory)
