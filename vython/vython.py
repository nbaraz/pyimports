import runpy
import sys
import os
import argparse

def main():
    from . import importer

    sys.argv = sys.argv[1:]
    importer.install_hook()

    # curretly only support running files. entry points coming soon :)
    runpy.run_path(sys.argv[0], run_name='__main__')

if __name__ == '__main__':
    main()
