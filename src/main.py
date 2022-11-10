#!/usr/bin/env python3
# coding:utf-8

from functools import partial

from .src import *
from .utils import hutils


def sra_init(args):
    if args.command == "fetch":
        return partial(hutils.autoreloader, sraDownload(args).run)
    elif args.command == "dump":
        return partial(sraDumps(args).run)


def main():
    args = sraArgs()
    sra_app = sra_init(args)
    sra_app()


if __name__ == "__main__":
    main()
