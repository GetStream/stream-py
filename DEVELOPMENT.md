# Getstream Python SDK

## Project structure:

1. `./getstream` - Core Stream SDK
2. `./protocol` - Protocol definitions for Stream SDKs
3. `./plugins` - Plugins for Core Stream SDK
4. `./examples` - Examples for Core Stream SDK
5. `./tests` - Tests for Core Stream SDK
6. `.github/workflows` - GitHub Actions workflows


## Package structure:

1. `getstream` - Core Stream SDK in `./getstream`
    - Video RTC SDK in `./getstream/video/rtc`
2. `getstream.plugins` - Plugins for Core Stream SDK in `./plugins`


```
NOTE
getstream acts as a namespace package which means all imports will be relative to the getstream package. Since getstream is a namespace package, it is required to have only one __init__.py file in the root of the package. The plugins cannot have their own __init__.py files in their respective getstream folders. When the core SDK is built and installed, you only get the core SDK getstream folder in the source distribution. When plugins are built and installed, they are merged into the core SDK namespace at getstream/plugins.
```

## Workspace

We use uv to manage the workspace. The project root is the root of the workspace. The following packages are added to the workspace:
- `getstream`

Workspace is configured in `pyproject.toml` and `uv.lock`.
In the workspace root pyproject.toml,
```toml
[tool.uv.workspace]
members = [
    "getstream",
]
```

In workspace members,
```toml
[tool.uv.sources]
getstream = { workspace = true }
```
You can also specify different sources in the sources table including local paths, git repositories, package indexes etc. Refer to the [uv documentation](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources) for more details.

To sync the workspace, run the following command:

```bash
uv sync
```

To sync the workspace with all packages and extras, run the following command:
```bash
uv sync --all-packages --all-extras --dev
```

This pull the dependencies from the workspace members.

To sync dependencies from upstream, run the following command:

```bash
uv sync --no-sources --all-packages --all-extras --dev
```
Use `--no-sources` in commands to avoid pulling dependencies from the workspace members.


Add dependencies to the workspace:

```bash
uv add numpy
```
This adds the dependency to the workspace. If you want to add a dependency to a specific package, you can do it like this:

```bash
uv add numpy --package getstream
```

`examples/*` are excluded from the workspace so as to be able to run the examples without installing the workspace.

## Build

To build the workspace, run the following command from the respective package (or use the `--package` flag to build a specific package):

```bash
uv build
```

To disable workspace build, run the following command:

```bash
uv build --no-sources
```
