import sys
import os
import pytoml

REPO = 'repo2'
versioned_path = [REPO]


def _install_package_in_path(package_name, version):
    for path in versioned_path:
        package_path = os.path.join(path, package_name, version, package_name)

        if os.path.exists(package_path):
            sys.path.append(os.path.join(path, package_name, version))
            return True

    return False


def _find_install_libs_dir():
    import abc
    return os.path.dirname(abc.__file__)


def _install_hook_init():
    install_libs_dir = _find_install_libs_dir()
    sys.path = [p for p in sys.path if p.startswith(install_libs_dir)]

def _install_hook_finalize():
    pass
