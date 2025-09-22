# Ukraine Energy Dashboard

A Plotly Dash application for visualizing and monitoring Ukraine's energy infrastructure data.

## Overview

tbd

## Features

tbd

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Run the dashboard:**
   ```bash
   python app.py
   ```

3. **Access the dashboard:**
   Open your browser and navigate to `http://localhost:8050`

## Project Structure

```
ukr_energy_dash/
├── app.py                # Main Dash application
├── assets/               # CSS, JS, and static files
│   └── data/             # Directory for input data
│   └── styles.css        # Custom styles
├── data/                 # Data loading and processing
│   ├── __init__.py
│   ├── process.py        # Data loading utilities
├── layouts/              # UI layout components
│   ├── __init__.py
│   └── layout_main.py    # Main dashboard layout
├── components/           # Reusable UI components
│   ├── __init__.py
│   └── utils.py          # Functions etc.
```

## Usage

The dashboard runs on a single configurable port (default: 8050). You can set a custom port using the `PORT` environment variable:

```bash
PORT=8080 python app.py
```

## Data Sources

Currently uses sample data for demonstration. In production, this would connect to real energy monitoring systems and databases.

## Development

1. **Install development dependencies:**
   ```bash
   pip install -e ".[test]"
   ```

2. **Run tests:**
   ```bash
   pytest tests/
   ```

3. **Code formatting:**
   ```bash
   ruff format .
   ```

## Structure

This repository is structured as a Plotly Dash application with the following organization:

* `app.py`: Main Dash application entry point
* `assets/`: Static files (CSS, JS, images) served by Dash
* `data/`: Data loading and processing modules
* `layouts/`: UI layout components and page structures
* `components/`: Reusable UI components (buttons, cards, etc.)


## Accessing Virtual Environment in Codespaces
For bash terminal users wanting to work in a virtual environment of ukr_energy_dash, enter these commands:

```
cd /workspaces/ukr_energy_dash
source .venv/bin/activate
```

## Accessing this Package on a Local Linux Server
This assumes you have internet connection and you already have cloned this repository. For both sub-cases below, start with these:
```
cd SOME_PATH/ukr_energy_dash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

### Local Mode
```
pip install . --no-cache-dir
```

### Testing/Developing Editable Mode
```
pip install -e .[test] --no-cache-dir --force-reinstall
```

## Accessing Database in Codespaces
PostgreSQL Database is set up only inside the Codespace Development Container, which is installed via apt-get. This database in Codespaces is used for these:
* `project_db`: Project-Testing with schema `dev` and in future cases `prod`.

When container is built for the first time, and to login to the database, please click on a extension logo on the left in VS Code that looks like a database, click on "Create Connection" and enter the following info:
```
host:       127.0.0.1 (or: localhost)
Port:       5432
Username:   project_user
Password:   project_pass
Database:   project_db
```
And then, click on `+ Connect`.


## Linting and Formatting
This project implements linting and formatting tools via a pre-commit hook. Most linting/formatting functionalities are covered by [Ruff](https://docs.astral.sh/ruff/). `Ruff` and other linting/formatting tools are installed in the virtual environment of `ukr_energy_dash`.

### Executing Linting Sources:
Executing as pre-commit hook:
```
pre-commit run --all-files
```
**Please note** that pre-commit hooks are only applied to staged changes.
### Executing Ruff
In order to check for linting and formatting errors in a bash terminal with automatic fixes, please use the commands below. This check also applies to unstaged changes as well as existing files, unless they were explicitly excluded from ruff checks.
```
ruff check . --fix
ruff format
```
Checking for included/excluded files and directories:
```
ruff check . -v
```

### Ruff Configuration:
For more details on Ruff’s configuration and rules, see our `pyproject.toml` file. In order to exclude specific rules in your repository, please check the [error code](https://docs.astral.sh/ruff/) you would like to exclude and add it in `pyproject.toml`
```
[tool.ruff.lint]
ignore = [
    "E722" #example
]
```
