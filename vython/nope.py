"""
A tool to manage versioned imports. Kind of sounds like 'no-pip'.
"""

import os
from os.path import join
import re
import shutil
import argparse
import errno
import warnings
import pkg_resources

import pip
import pytoml

try:
  from pathlib import Path
except ImportError:
  from pathlib2 import Path

# TODO: make package
from . import importer

TEMPDIR = 'nope_temp'


class PackageError(Exception):
    pass


class UnsatisfiedRequirement(PackageError):

    def __init__(self, requirements_dict):
        self.unsatisfied_requirements = requirements_dict
        super(UnsatisfiedRequirement, self).__init__(requirements_dict)


class Repo:

    def __init__(self, path):
        self.path = path

    def install(self, package_name, version):
        """Install the given package+version to the global repo"""

        if os.path.exists(TEMPDIR):
            shutil.rmtree(TEMPDIR)

        result = pip.main(['install', '-t', TEMPDIR, '{package_name}=={version}'.format(**locals())])
        if result != 0:
            exit(result)

        downloaded = os.listdir(TEMPDIR)
        versioned = _parse_pip_installed_dirlist(downloaded)

        for pkg_info, pkg, version in versioned:
            _transform_installation(self.path, pkg, version, pkg_info)

    def lock_add(self, lockfile, package_name, version, force=False):
        """Add a packege to a lockfile"""

        with open(lockfile, 'r') as f:
            lock_dict = pytoml.load(f)

        for name, ver in self._find_dependencies(package_name, version):
            _add_package_to_dict(lock_dict['packages'], name, ver, force)

        with open(lockfile, 'w') as f:
            pytoml.dump(lock_dict, f)

        print(lock_dict)

    def _get_package_requirements(self, package_name, version):
        path_item = os.path.join(self.path, package_name, version)
        distribution, = pkg_resources.find_on_path(None, path_item)
        return distribution.requires()

    def _satisfy_requirement(self, requirement):
        versions_path = os.path.join(self.path, requirement.name)
        # TODO: Alphabetical order might not actually be pip compliant :)
        versions = sorted(os.listdir(versions_path), reverse=True)
        found = False
        failed_requirements = {}

        for v in versions:
            if v in requirement:
                try:
                    for dep in self._find_dependencies(requirement.name, v):
                        yield dep
                except UnsatisfiedRequirement as e:
                    failed_requirements[(requirement.name, v)] = e.unsatisfied_requirements
                else:
                    found = True
                    break

        # TODO: Exception path is untested
        if not found:
            raise UnsatisfiedRequirement(failed_requirements)

    def _find_dependencies(self, package_name, version):
        requirements = self._get_package_requirements(package_name, version)
        for req in requirements:
            for pinned_package in self._satisfy_requirement(req):
                yield pinned_package

        yield package_name, version

    def install_lock(self, lockfile):
        with open(lockfile, 'r') as f:
            lock_dict = pytoml.load(f)

        for name, version in lock_dict['packages'].items():
            self.install(name, version)


def _parse_pip_installed_dirlist(dirlist):
    def _get_pkg_info(st):
        # TODO: use pkg_resources
        return re.match(r'^((.+?)-(.+).dist-info)$', st).groups()

    versioned, packages = _split_iter_by_function(dirlist, _get_pkg_info)
    assert set(packages) == set(p[1] for p in versioned)

    return versioned


def _add_package_to_dict(package_dict, package_name, version, force):
    assert version != None
    if not force and package_name in package_dict:
        toml_version = package_dict[package_name]
        if toml_version == version:
            warnings.warn(
                'Package `{package_name}` already exists with the same version ({version})'.format(**locals()))
        else:
            raise PackageError(
                'Package `{package_name}` already exists with a different version ({version})'.format(**locals()))

    package_dict[package_name] = version


def _split_iter_by_function(strings, fun):
    matched = []
    didnt = []

    for st in strings:
        try:
            matched.append(fun(st))
        except:
            didnt.append(st)

    return matched, didnt

def _try_rename(src, dst):
    try:
        os.rename(src, dst)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            pass

def _transform_installation(repo, package, version, pkg_info):
    Path.mkdir(Path(repo, package, version), parents=True, exist_ok=True)

    version_path = join(repo, package, version)

    _try_rename(join(TEMPDIR, package), join(version_path, package))
    _try_rename(join(TEMPDIR, pkg_info), join(version_path, pkg_info))


def main():
    # TODOS - I'm organizing them in the source because using the github issue tracker is too much
    # work for this small a project
    # TODO: Support installing + creating a lockfile from a requirements.txt file
    # TODO: Create a lockfile for each installed dependency in the folder in which it is installed.
    #   This will make running entry points / `python -m` possible from vython.
    # TODO: Support fuzzy version specifivation when installing

    repo = Repo(importer.REPO)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    def _run_install(args):
        repo.install(args.name, args.version)

    install_parser = subparsers.add_parser('install')
    install_parser.add_argument('name')
    install_parser.add_argument('version')
    install_parser.set_defaults(func=_run_install)

    def _run_lock_add(args):
        repo.lock_add(args.lockfile, args.name, args.version)

    lock_add_parser = subparsers.add_parser('lockadd')
    lock_add_parser.add_argument('lockfile')
    lock_add_parser.add_argument('name')
    lock_add_parser.add_argument('version')
    lock_add_parser.set_defaults(func=_run_lock_add)

    def _run_install_lock(args):
        repo.install_lock(args.lockfile)

    install_lock_parser = subparsers.add_parser('install_lock')
    install_lock_parser.add_argument('lockfile')
    install_lock_parser.set_defaults(func=_run_install_lock)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)


if __name__ == '__main__':
    main()
