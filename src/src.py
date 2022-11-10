#!/usr/bin/env python3
# coding:utf-8

from .utils import *

__all__ = ["sraDownload", "sraDumps", "sraArgs"]


class sraDumps(object):
    def __init__(self, args=None):
        self.args = args
        self.srafile = os.path.abspath(args.input)
        self.chunks = args.processes
        self.spot_chunks = []
        self.outdir = os.path.abspath(args.outdir)
        if not os.path.isfile(self.srafile):
            raise SraArgumentsError("No such sra file: %s" % self.args.input)
        mkdir(self.outdir)
        self.dumpdir = tempfile.TemporaryDirectory(
            dir=self.outdir, prefix="srautils_")
        self.chunkdir = os.path.join(self.dumpdir.name, "chunks")
        self.logdir = os.path.join(self.dumpdir.name, "logs")
        self.dump_scripts = os.path.join(self.dumpdir.name, "sra_dumps.sh")
        self.args.mode = "sge"
        if self.args.local:
            self.args.mode = "local"
        self.args.jobname = "sra_dump_%d" % os.getpid()
        self.args.num = self.chunks
        self.args.cpu = 1
        self.args.memory = 1
        self.args.logdir = self.logdir
        self.args.workdir = os.getcwd()
        self.args.startline = 0
        self.args.groups = 1
        self.loger = sraLog(self.args.log, "info", name=RunSge.__module__)

    def split_blocks(self):
        total = self.get_total_spot
        avg = int(total / self.chunks)
        last = 1
        for i in range(0, self.chunks):
            self.spot_chunks.append([last, last + avg-1])
            last += avg
            if i == self.chunks-1:
                self.spot_chunks[i][1] += total % self.chunks

    def _check_sra_bin(self):
        for path in [which("sra-stat"), which("fastq-dump")]:
            if not path:
                raise SraArgumentsError("sratoolkit not found in $PATH")
            if not check_cmd([path, "--version"]):
                raise SraArgumentsError("sratoolkit installation has not been configured, please run '%s --interactive'" %
                                        os.path.join(os.path.dirname(path), "vdb-config"))

    @property
    def get_total_spot(self):
        stat_exe = which("sra-stat")
        cmd = " ".join([stat_exe, '--meta', '--quick', self.srafile])
        total = 0
        with os.popen(cmd) as fi:
            for line in fi:
                total += int(line.split('|')[2].split(':')[0])
        return total

    def write_shell(self):
        mkdir(os.path.dirname(self.dump_scripts))
        dumps_exe = which("fastq-dump")
        self.chunk_res = []
        with open(self.dump_scripts, "w") as fo:
            for n, pos in enumerate(self.spot_chunks):
                out_dir = os.path.join(self.chunkdir, str(n))
                mkdir(out_dir)
                self.chunk_res.append(out_dir)
                cmdline = [dumps_exe, "--split-files", "-O",
                           out_dir, "-N", str(pos[0]), "-X", str(pos[1])]
                if not self.args.no_gzip:
                    cmdline.append("--gzip")
                if self.args.fasta:
                    cmdline.append("--fasta")
                cmdline.append(self.srafile)
                fo.write(shlex.join(cmdline)+"\n")

    def run_dumps(self):
        self.args.jobfile = self.dump_scripts
        self.args.force = True
        conf = Config()
        conf.update_dict(**self.args.__dict__)
        if os.path.isfile(self.dump_scripts):
            mkdir(self.logdir)
            srajobs = RunSge(config=conf)
            h = ParseSingal(obj=srajobs, name=self.args.jobname,
                            mode=self.args.mode, conf=conf)
            h.start()
            srajobs.run(times=0)
            if not srajobs.sumstatus():
                os.kill(os.getpid(), signal.SIGTERM)

    def mergs_res(self):
        if len(self.chunk_res):
            dumpfiles = []
            self.loger.info("merge sra dumps file")
            outfiles = sorted(os.listdir(self.chunk_res[0]))
            for outfile in outfiles:
                if (self.args.no_gzip and outfile.endswith(".gz")) or \
                        (not self.args.no_gzip and not outfile.endswith(".gz")):
                    continue
                if outfile.endswith(".gz"):
                    ext = outfile[:-3]
                else:
                    ext = outfile
                if (self.args.fasta and not ext.endswith(".fasta")) or \
                        (not self.args.fasta and not ext.endswith(".fastq")):
                    continue
                dumpfiles.append(os.path.join(self.outdir, outfile))
                with open(os.path.join(self.outdir, outfile), "wb") as fo:
                    for d in self.chunk_res:
                        chunk_file = os.path.join(d, outfile)
                        if os.path.isfile(chunk_file):
                            with open(chunk_file, "rb") as fi:
                                shutil.copyfileobj(fi, fo)
            self.loger.info("sra dumps finished: %s", ", ".join(dumpfiles))
            if os.path.isdir(self.dumpdir.name):
                self.dumpdir.cleanup()

    def run(self):
        self._check_sra_bin()
        self.split_blocks()
        self.write_shell()
        self.run_dumps()
        self.mergs_res()


class sraDownload(object):
    def __init__(self, args=None):
        self.args = args
        self.sraid = args.id.upper()
        self.threads = args.num
        self.outdir = args.outdir
        self.speed = args.max_speed

    @property
    def isSra(self):
        if self.sraid[:3] in ['SRR', 'ERR', 'DRR']:
            return True
        return False

    @property
    def url(self):
        if self.isSra:
            url = os.path.join(AWS_BUCKET, "sra", self.sraid, self.sraid)
            u = hutils.urlparse(url)
            self.bucket, self.key = u.hostname, u.path.lstrip("/")
            return url
        else:
            raise SraArgumentsError("Not a sra id: %s" % self.args.id)

    def run(self):
        if self.url:
            isOk = self._check_url()
            if not isOk:
                raise SraArgumentsError("No such sra id: %s" % self.args.id)
            mkdir(self.outdir)
            outpath = os.path.join(self.outdir, self.sraid + ".sra")
            log = hutils.loger()
            kwargs = {}
            kwargs.update(url=self.url, outfile=outpath,
                          max_speed=self.speed)
            if self.threads:
                kwargs.update(threads=min(self.threads, 300))
            hget(**kwargs)

    def _check_url(self):
        client = hutils.client('s3', config=hutils.Config(signature_version=hutils.UNSIGNED,
                                                          max_pool_connections=hutils.MAX_S3_CONNECT+1, connect_timeout=30))
        try:
            client.head_object(Bucket=self.bucket, Key=self.key)
            return True
        except:
            return False
