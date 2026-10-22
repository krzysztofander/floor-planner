"""
Command-line options of the pytest regression suite (see tests/conftest.py).

Defined in the repository-root conftest.py because pytest always loads it before
parsing the command line. In tests/conftest.py, an option value that names an
existing folder (e.g. ``--scene textures``) would be taken as a test path and
the options would not be known yet.
"""


def pytest_addoption(parser):
    group = parser.getgroup('floor_planner')
    group.addoption('--update-golden', action='store_true', default=False,
                    help='write golden files instead of comparing (2D, and 3D with --golden-3d)')
    group.addoption('--golden-3d', action='store_true', default=False,
                    help='enable the 3D golden comparison (off in phase 1)')
    group.addoption('--scene', action='append', default=[],
                    help='run only scenes whose path contains this substring (repeatable)')
