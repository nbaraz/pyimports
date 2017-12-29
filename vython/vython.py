import runpy
import sys
import os
import argparse


def main():
    del sys.argv[0]

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', help='module to run')
    parser.add_argument('target', help='module to run')
    parser.add_argument('args', nargs=argparse.REMAINDER)

    print(sys.argv)

    args = parser.parse_args()
    sys.argv = [args.target] + args.args

    from . import importer
    importer.install_hook()

    if args.m:
        runpy._run_module_as_main(args.target)
    else:
        runpy.run_path(args.target, run_name='__main__')


if __name__ == '__main__':
    main()
