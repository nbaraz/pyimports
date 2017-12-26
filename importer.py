import sys
import os
import pytoml

if sys.version_info.major == 3:
    import importer3 as importer
else:
    import importer2 as importer

REPO = importer.REPO


def install_hook(lockfile_dir='.'):
    """
    Install the versioned import hook
    """
    importer._install_hook_init()

    stripped_script_name, ext = os.path.splitext(os.path.basename(sys.argv[0]))
    if not ext or ext.lower() == '.py':
        script_name = stripped_script_name
    else:
        script_name = sys.argv[0]

    lock_name = script_name + '-lock.toml'

    with open(os.path.join(lockfile_dir, lock_name)) as lock_file:
        lock_dict = pytoml.load(lock_file)

    for package_name, version in lock_dict['packages'].items():
        if not importer._install_package_in_path(package_name, version):
            raise RuntimeError('Could not find all versioned packages', (package_name, version))

    importer._install_hook_finalize()
