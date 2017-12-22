"""
Install an import hook that precedes the normal path based finder with one that imports based on
versions. Designed to replace `virtualenv` in most use cases.
"""

import sys
import os
import pytoml

# TODO: maybe there's a better way?
PathFinder = sys.modules['_frozen_importlib_external'].PathFinder

# TODO: make this configurable, somehow
versioned_path = ['repo']
_resolved_versioned_path = None


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


def install_hook(lockfile_dir='.'):
    """
    Install the versioned import hook
    """
    global _resolved_versioned_path

    _resolved_versioned_path = []

    stripped_script_name, ext = os.path.splitext(os.path.basename(sys.argv[0]))
    if not ext or ext.lower() == '.py':
        script_name = stripped_script_name
    else:
        script_name = sys.argv[0]

    lock_name = script_name + '-lock.toml'

    with open(os.path.join(lockfile_dir, lock_name)) as lock_file:
        lock_dict = pytoml.load(lock_file)

    for package_name, version in lock_dict['packages'].items():
        if not _install_package_in_path(package_name, version):
            raise RuntimeError('Could not find all versioned packages', (package_name, version))

    idx = sys.meta_path.index(PathFinder)
    sys.meta_path.insert(idx, VersionedPathFinder)
