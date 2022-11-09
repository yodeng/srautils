#!/usr/bin/env python3
# coding:utf-8

from .src import *


def sra_init(args):
    if args.command == "fetch":
        return sraDownload(args)
    elif args.command == "dump":
        return sraDumps(args)


def main():
    args = sraArgs()
    sra_app = sra_init(args)
    sra_app.run()


if __name__ == "__main__":
    main()
