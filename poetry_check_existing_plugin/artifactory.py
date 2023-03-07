from urllib.parse import urlparse

from pyartifactory import Artifactory


class ArtifactoryClient(Artifactory):
    """Artifactory client with a method to return release versions.

    Attributes:

    """

    def __init__(self, url: str, username: str, password: str, **kwargs):
        url = self.get_base_url(url)
        super().__init__(url, auth=(username, password), **kwargs)

    @staticmethod
    def get_base_url(url: str) -> str:
        """Return the base url of an artifactory instance.

        Args:
            url (str): The url of the artifactory instance.

        Returns:
            str: The base url of the artifactory instance.
        """
        parsed = urlparse(url)
        new = parsed._replace(path="/artifactory")
        return new.geturl().rstrip("/")

    def get_releases(self, repository_name: str, package_name: str) -> list[str]:
        """List versions uploaded to an artifactory repository.

        Args:
            repository_name: pypi repository name
            package_name: pypi package name

        Returns:
            list[str]: List of versions uploaded to the artifactory repository.
        """
        resp = self.artifacts.list(
            f"{repository_name}/{package_name}", recursive=False, list_folders=True
        )
        return [item.uri.lstrip("/") for item in resp.files]
