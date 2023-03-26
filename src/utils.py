#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import shlex
import signal
import shutil
import weakref
import argparse
import tempfile
import subprocess

import hget.utils as hutils

from hget import hget
from lxml import etree
from runjob import runsge
from runjob import log as sraLog
from runjob.config import Config

from ._version import __version__


class SraArgumentsError(Exception):
    pass


class TempDir(object):

    def __init__(self, suffix=None, prefix=None, dir=None, persistent=False):
        self.persistent = persistent
        self.name = tempfile.mkdtemp(suffix, prefix, dir)
        self._finalizer = weakref.finalize(
            self, self._cleanup, self.name)

    def _cleanup(self, name):
        if not self.persistent:
            shutil.rmtree(name)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, value, tb):
        self.cleanup()

    def cleanup(self):
        if self._finalizer.detach():
            shutil.rmtree(self.name)


def mkdir(path):
    os.makedirs(path, exist_ok=True)


def which(program, paths=None):
    ex = os.path.dirname(sys.executable)
    found_path = None
    fpath, fname = os.path.split(program)
    if fpath:
        program = canonicalize(program)
        if is_exe(program):
            found_path = program
    else:
        if is_exe(os.path.join(ex, program)):
            return os.path.join(ex, program)
        paths_to_search = []
        if isinstance(paths, (tuple, list)):
            paths_to_search.extend(paths)
        else:
            env_paths = os.environ.get("PATH", "").split(os.pathsep)
            paths_to_search.extend(env_paths)
        for path in paths_to_search:
            exe_file = os.path.join(canonicalize(path), program)
            if is_exe(exe_file):
                found_path = exe_file
                break
    return found_path


def is_exe(file_path):
    return (
        os.path.exists(file_path)
        and os.access(file_path, os.X_OK)
        and os.path.isfile(os.path.realpath(file_path))
    )


def check_cmd(cmd=None):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print((stdout + stderr).decode())
        return False
    return True


def canonicalize(path):
    return os.path.abspath(os.path.expanduser(path))


AWS_BUCKET = "s3://sra-pub-run-odp/"


def sraArgs():
    parser = argparse.ArgumentParser(
        description="fast utils for fetch and dump SRA archive raw fastq data", add_help=True)
    parser.add_argument("-v", '--version',
                        action='version', version="v" + __version__)
    subparsers = parser.add_subparsers(
        metavar="command", dest="command")
    fetch_args = subparsers.add_parser(
        'fetch', help='fetch raw sra data by SRA accession id')
    fetch_args.add_argument(
        '-i', "--id", help='input SRA accession id, SRR/ERR/DRR allowed, required', required=True, metavar="<str>")
    fetch_args.add_argument(
        '-o', "--outdir", help='output sra directory, current dir by default', default=os.getcwd(), metavar="<str>")
    fetch_args.add_argument(
        '-n', "--num", help='the max number of concurrency, default: auto', type=int, metavar="<int>")
    fetch_args.add_argument("-s", "--max-speed", help="specify maximum speed per second, case-insensitive unit support (K[b], M[b]...), no-limited by default",
                            metavar="<str>")
    dump_args = subparsers.add_parser(
        'dump', help='dump sra into fastq/fasta sequence file')
    dump_args.add_argument("-i", "--input", type=str, required=True,
                           help='input sra file, required', metavar="<file>")
    dump_args.add_argument("-p", "--processes", type=int, default=10,
                           help='number of dumps processors, 10 by default', metavar="<int>")
    dump_args.add_argument("-l", "--log", type=str,
                           help='append srautils log info to file, stdout by default', metavar="<file>")
    dump_args.add_argument("--local", action='store_true',
                           help="run sra-dumps in localhost instead of sge", default=False)
    output_group = dump_args.add_argument_group("output arguments")
    output_group.add_argument("-o", "--outdir", type=str, default=os.getcwd(),
                              help='output directory, current dir by default', metavar="<dir>")

    output_group.add_argument("--no-gzip", action='store_true', default=False,
                              help="do not compress output")
    output_group.add_argument("--fasta", action='store_true', default=False,
                              help="output fasta only")
    sge_group = dump_args.add_argument_group("sge arguments")
    sge_group.add_argument("-q", "--queue", type=str, default=["all.q", ],
                           help='sge queue, multi-queue can be sepreated by whitespace, all.q by default', nargs="*", metavar="<str>")
    return parser.parse_args()
