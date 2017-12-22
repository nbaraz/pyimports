"""
A tool to manage versioned imports. Kind of sounds like 'no-pip'.
"""

import os
from os.path import join
import re
import argparse
import warnings
import pkg_resources

import pip
import pytoml

# TODO: make package
import importer

TEMPDIR = 'nope_temp'


class PackageError(Exception):
    pass


class UnsatisfiedRequirement(PackageError):

    def __init__(self, requirements_dict):
        self.unsatisfied_requirements = requirements_dict
        super().__init__('Unsatisfied requirements', requirements_dict)


class Repo:

    def __init__(self, path):
        self.path = path

    def install(self, package_name, version):
        """Install the given package+version to the global repo"""

        result = pip.main(['install', '-t', TEMPDIR, f'{package_name}=={version}'])
        if result != 0:
            exit(result)

        downloaded = os.listdir(TEMPDIR)

        def _get_pkg_info(st):
            # TODO: use pkg_resources
            return re.match(r'^((.+?)-(.+).dist-info)$', st).groups()

        versioned, packages = _split_iter_by_function(downloaded, _get_pkg_info)
        assert set(packages) == set(p[1] for p in versioned)

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
        distribution, = pkg_resources.find_on_path(importer.VersionedPathFinder, path_item)
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
                    yield from self._find_dependencies(requirement.name, v)
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
            yield from self._satisfy_requirement(req)

        yield package_name, version


def _add_package_to_dict(package_dict, package_name, version, force):
    assert version != None
    if not force and package_name in package_dict:
        toml_version = package_dict[package_name]
        if toml_version == version:
            warnings.warn(
                f'Package `{package_name}` already exists with the same version ({version})')
        else:
            raise PackageError(
                f'Package `{package_name}` already exists with a different version ({version})')

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
    except FileExistsError:
        pass

def _transform_installation(repo, package, version, pkg_info):
    os.makedirs(join(repo, package), exist_ok=True)

    version_path = join(repo, package, version)
    try:
        os.mkdir(version_path)
    except FileExistsError:
        if os.listdir(version_path):
            raise

    _try_rename(join(TEMPDIR, package), join(version_path, package))
    _try_rename(join(TEMPDIR, pkg_info), join(version_path, pkg_info))


def main():
    repo = Repo('repo')

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    def _run_install(args):
        repo.install(args.name, args.version)

    install_parser = subparsers.add_parser('install')
    install_parser.add_argument('name')
    install_parser.add_argument('version')
    install_parser.set_defaults(func=_run_install)

    def _run_lockadd(args):
        repo.lock_add(args.lockfile, args.name, args.version)

    lockadd_parser = subparsers.add_parser('lockadd')
    lockadd_parser.add_argument('lockfile')
    lockadd_parser.add_argument('name')
    lockadd_parser.add_argument('version')
    lockadd_parser.set_defaults(func=_run_lockadd)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)


if __name__ == '__main__':
    main()
