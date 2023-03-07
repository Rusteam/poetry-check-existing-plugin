# Poetry check-existing plugin

[Poetry](https://python-poetry.org/docs/plugins/#using-plugins)
plugin to check if a package with the same version already exists in a pypi index.
It can be useful to avoid uploading a package with the same version twice
(in cases where pypi repository does not protect from overwriting packages). 
Also, it can be used in CI/CD to make sure that the package version has been updated.

## Usage

1. Clone the project and build the plugin:

```bash
poetry build
```
This will create a distributable package in the `dist` directory.

2. Install the plugin in a **target** project:

```bash
pip install --user path/to/dist/poetry_check_existing-0.1.0-py3-none-any.whl
```

3. Run the plugin: 
```bash
# to use with pypi.org
poetry check-existing

# to use with Artifactory deployed on-premise
poetry check-existing -r pypi-repo-name --artifactory
```

It should raise a `RuntimeError` if the package with the same version already exists.
If the package does not exist, it will print a message and exit with code 0.