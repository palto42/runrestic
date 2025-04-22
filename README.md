![python version](https://img.shields.io/badge/python-3.7+-blue.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Travis (.com)](https://api.travis-ci.com/sinnwerkstatt/runrestic.svg?branch=main)
![PyPI](https://img.shields.io/pypi/v/runrestic)
[![Stackshare: runrestic](https://img.shields.io/badge/stackshare-runrestic-068DFE.svg)](https://stackshare.io/runrestic)
![PyPI - Downloads](https://img.shields.io/pypi/dm/runrestic)

# Runrestic

runrestic is a simple Python wrapper script for the
[Restic](https://restic.net/) backup software that initiates a backup,
prunes any old backups according to a retention policy, and validates backups
for consistency. The script supports specifying your settings in a declarative
configuration file rather than having to put them all on the command-line, and
handles common errors.

## Example config

```toml
repositories = [
    "/tmp/restic-repo",
    "sftp:user@host:/srv/restic-repo",
    "s3:s3.amazonaws.com/bucket_name"
    ]

[environment]
RESTIC_PASSWORD = "CHANGEME"

[backup]
sources = [
    "/home",
    "/var"
    ]

[prune]
keep-last =  3
keep-hourly =  5
```

Alternatively you can also just use JSON. For a more comprehensive example see the [example.toml](https://github.com/sinnwerkstatt/runrestic/blob/main/sample/example.toml)
or check the [schema.json](https://github.com/sinnwerkstatt/runrestic/blob/main/runrestic/runrestic/schema.json)

## Getting started

### Installing runrestic and restic

To install **runrestic**, run the following command to download and install it:

```bash
sudo pip3 install --upgrade runrestic
```

<br>
You can either manually download and install [Restic](https://restic.net/) or you can just run `runrestic` and it'll try to download it for you.

### Initializing and running

Once you have `restic` and `runrestic` ready, you should put a config file in on of the scanned locations, namely:

- /etc/runrestic.toml
- /etc/runrestic/_example_.toml
- ~/.config/runrestic/_example_.toml
- /etc/runrestic.json
- /etc/runrestic/_example_.json
- ~/.config/runrestic/_example_.json

Afterwards, run

```bash
runrestic init # to initialize all the repos in `repositories`

runrestic  # without actions will do: runrestic backup prune check
# or
runrestic [action]
```

<br>
Certain `restic` flags like `--dry-run/-n` are built into `runrestic` as well and will be passed to restic where applicable.

If, however, you need to pass along arbitrary other flags you can now add them to the end of your `runrestic` call like so:

```bash
runrestic backup -- --one-file-system
```

#### Logs for restic and hooks

The output of `restic` and the configured pre/post-hooks is added to the `runrestic` logs at the level defined in
`[execution] proc_log_level` (default: DEBUG), which can be overwritten with the CLI option `-p/--proc-log-level`.

For process log levels greater than `INFO` the output of file names is suppressed and for log levels greater than WARNING
`restic` is executed with the `--quiet` option. If the process log level is set to `DEBUG`, then restic is executed
with the `--verbose` option.

It is also possible to add `restic` progress messages to the logs by using the CLI option `--show-progress INTERVAL`
where the `INTERVAL` is the number of seconds between the progress messages.

### Restic shell

To use the options defined in `runrestic` with `restic` (e.g. for a backup restore), you can use the `shell` action:

```bash
runrestic shell
```

If you are using multiple repositories or configurations, you can select one now.

### Prometheus / Grafana metrics

[@d-matt](https://github.com/d-matt) created a nice dashboard for Grafana here: https://grafana.com/grafana/dashboards/11064/revisions

### systemd timer or cron

If you want to run runrestic automatically, say once a day, the you can
configure a job runner to invoke it periodically.

#### systemd

If you're using systemd instead of cron to run jobs, download the [sample systemd service file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/systemd/runrestic.service)
and the [sample systemd timer file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/systemd/runrestic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv runrestic.service runrestic.timer /etc/systemd/system/
sudo systemctl enable runrestic.timer
sudo systemctl start runrestic.timer
```

#### cron

If you're using cron, download the [sample cron file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/cron/runrestic).
Then, from the directory where you downloaded it:

```bash
sudo mv runrestic /etc/cron.d/runrestic
sudo chmod +x /etc/cron.d/runrestic
```

## Changelog

- v0.5.30
  - Change project setup based on [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv)
    - Uses `uv` as a replacement for `pip` and `ruff` instead of `black`.
    - `tox` to easily test multiple python versions
  - Drop support for Python 3.9 since it will be EOL end 2025.
- v0.5.29
  - Support Python 3.12
  - Updated devcontainer to Ubuntu 24.04 (noble)
- v0.5.28
  - Allow jsonschema >= 4.0
- v0.5.27
  - Fix output parsing for new restic version 0.14.0
  - Introduce failsafe output parser which supports default values
- v0.5.26
  - Add output messages from `restic` and pre/post-hook commands to runrestic logs.
  - New CLI argument `--show-progress INTERVAL` for the restic progress update interval in seconds (default None)
- v0.5.25
  - Drop support for Python 3.6, add support for Python 3.9 and 3.10, update dependencies
- v0.5.24
  - Exit the script with returncode = 1 if there was an error in any of the tasks
- v0.5.23
  - support JSON config files.
- v0.5.21

  - fix issue where "check" does not count towards overall "errors"-metric

- v**0.5**! Expect breaking changes.
  - metrics output is a bit different
  - see new `parallel` and `retry_*` options.

## Ansible

@tabic wrote an ansible role, you can find it here: https://github.com/outwire/ansible-role-restic . (I have neither checked nor tested it.)

## Development

This project is managed with [poetry](https://python-poetry.org/)

[Install it](https://github.com/python-poetry/poetry#installation) if not already present:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
# or
pip install --user poetry
```

---

# runrestic - NEW

[![Release](https://img.shields.io/github/v/release/sinnwerkstatt/runrestic)](https://img.shields.io/github/v/release/sinnwerkstatt/runrestic)
[![Build status](https://img.shields.io/github/actions/workflow/status/sinnwerkstatt/runrestic/main.yml?branch=main)](https://github.com/sinnwerkstatt/runrestic/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/sinnwerkstatt/runrestic/branch/main/graph/badge.svg)](https://codecov.io/gh/sinnwerkstatt/runrestic)
[![Commit activity](https://img.shields.io/github/commit-activity/m/sinnwerkstatt/runrestic)](https://img.shields.io/github/commit-activity/m/sinnwerkstatt/runrestic)
[![License](https://img.shields.io/github/license/sinnwerkstatt/runrestic)](https://img.shields.io/github/license/sinnwerkstatt/runrestic)

A wrapper script for Restic backup software that inits, creates, prunes and checks backups.

- **Github repository**: <https://github.com/sinnwerkstatt/runrestic/>
- **Documentation** <https://sinnwerkstatt.github.io/runrestic/>




## Getting started with your project

### 1. Create a New Repository

First, create a repository on GitHub with the same name as this project, and then run the following commands:

```bash
git init -b main
git add .
git commit -m "init commit"
git remote add origin git@github.com:sinnwerkstatt/runrestic.git
git push -u origin main
```

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```

### 4. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version

- Create an API Token on [PyPI](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting [this page](https://github.com/sinnwerkstatt/runrestic/settings/secrets/actions/new).
- Create a [new release](https://github.com/sinnwerkstatt/runrestic/releases/new) on Github.
- Create a new tag in the form `*.*.*`.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/cicd/#how-to-trigger-a-release).

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
