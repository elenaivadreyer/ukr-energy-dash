"""
This file tests the contents of the Ukraine Energy Dashboard package.
"""

import ukr_energy_dash


def test_project_name() -> None:
    assert ukr_energy_dash.NAME == "ukr_energy_dash"


def test_project_version() -> None:
    assert hasattr(ukr_energy_dash, '__version__')
    assert ukr_energy_dash.__version__ == "0.1.0"
