"""
Install an import hook that precedes the normal path based finder with one that imports based on
versions. Designed to replace `virtualenv` in most use cases.
"""

import sys
import os
import pytoml

# TODO: maybe there's a better way?
PathFinder = sys.modules['_frozen_importlib_external'].PathFinder

REPO = 'repo3'

# TODO: make this configurable, somehow
versioned_path = [REPO]
_resolved_versioned_path = []


class VersionedPathFinder(PathFinder):
    """
    Import from
    """

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        """
        Do what finding from `sys.path` does, just for versioned imports.
        """
        if path is None:
            path = _resolved_versioned_path
        return PathFinder.find_spec(fullname, path, target)


def _install_package_in_path(package_name, version):
    for path in versioned_path:
        package_path = os.path.join(path, package_name, version, package_name)

        if os.path.exists(package_path):
            _resolved_versioned_path.append(os.path.join(path, package_name, version))
            return True

    return False


def _install_hook_init():
    global _resolved_versioned_path
    _resolved_versioned_path = []


def _install_hook_finalize():
    idx = sys.meta_path.index(PathFinder)
    sys.meta_path.insert(idx, VersionedPathFinder)
