# Poetry check-existing plugin

[Poetry](https://python-poetry.org/docs/plugins/#using-plugins)
plugin to check if a package with the same version already exists in a pypi index.

## Usage

1. Build the plugin:

```bash
poetry build
```
This will create a distributable package in the `dist` directory.

2. Install the plugin in a target project:

```bash
pip install --user path/to/dist/poetry_check_existing-0.1.0-py3-none-any.whl
```

3. Run the plugin: 
```bash
poetry check-existing
```