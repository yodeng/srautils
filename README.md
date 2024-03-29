# srautils

[![PyPI version](https://img.shields.io/pypi/v/srautils.svg?logo=pypi&logoColor=FFE873)](https://pypi.python.org/pypi/srautils)

srautils is a program used for download and dump NCBI SRA archive raw fastq data. It provides a fast and easy way to fetch sra data and convert sra file into fastq/fasta sequence data for our scientific research.

### 1. Requirement

+ Linux64
+ python >=3.8
+ [sratoolkit](https://github.com/ncbi/sra-tools/wiki/02.-Installing-SRA-Toolkit)

### 2. Install

The latest release can be installed with

> pypi:

```shell
pip3 install srautils -U
```

The development version can be installed with (for recommend)

```shell
pip3 install git+https://github.com/yodeng/srautils.git
```

### 3. Usage

srautils include `srautils fetch` and `srautils dump` sub-commands. 

```
$ srautils -h 
usage: srautils [-h] [-v] command ...

fast utils for fetch and dump SRA archive raw fastq data

positional arguments:
  command
    fetch        fetch raw sra data by SRA accession id
    dump         dump sra into fastq/fasta sequence file

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
```

#### 3.1 srautils fetch

The `fetch` command is used for download SRA file by only giving an accession SRA id, it's a rapid and interruptable download accelerator.

All original SRA files are obtained directly from AWS Cloud with `UNSIGNED` access. This tools split the whole download into many pieces and record the progress of each chunk in a `*.ht` binary file, this can significantly speed up the download. Auto resume can be running by loading the progress file if any interruption. Command help as follows:

```
$ srautils fetch -h 
usage: srautils fetch [-h] -i <str> [-o <str>] [-n <int>] [-s <str>]

optional arguments:
  -h, --help            show this help message and exit
  -i <str>, --id <str>  input sra-id, SRR/ERR/DRR allowed, required
  -o <str>, --outdir <str>
                        output sra directory, current dir by default
  -n <int>, --num <int>
                        the max number of concurrency, default: auto
  -s <str>, --max-speed <str>
                        specify maximum speed per second, case-insensitive unit support (K[b], M[b]...), no-limited by default
```

| options        | descriptions                                                 |
| -------------- | ------------------------------------------------------------ |
| -h/--help      | show this help message and exit                              |
| -i/--id        | input valid accession SRA id                                 |
| -o/--outdir    | output directory                                             |
| -n/--num       | the max number of concurrency, auto detect by sra file size  |
| -s/--max-speed | maximum speed per second, case-insensitive unit support (K[b], M[b]...), no-limited by default |

![fetch](https://user-images.githubusercontent.com/18365846/201565539-4df7ee9e-0a44-4786-8a90-1fd2e78d4ab5.png)

#### 3.2 srautils dump

The `dump` command is a parallel `fastq-dump` wrapper which used for dump SRA file and get the raw `fastq/fasta` sequence data as output. 

NCBI `fastq-dump` is very slow,  even if you have high machine resources (network, IO, CPU). This tool speeds up the process by dividing the work into multiple jobs and runing all chunked jobs parallelly in localhost or sge cluster (default) environment. After chunk jobs finished, all resuslts will be concatenated together. The command usage below here:

```
$ srautils dump -h 
usage: srautils dump [-h] -i <file> [-p <int>] [-l <file>] [--local] [-o <dir>] [--no-gzip] [--fasta] [-q [<str> ...]]

optional arguments:
  -h, --help            show this help message and exit
  -i <file>, --input <file>
                        input sra file, required
  -p <int>, --processes <int>
                        number of dumps processors, 10 by default
  -l <file>, --log <file>
                        append srautils log info to file, stdout by default
  --local               run sra-dumps in localhost instead of sge

output arguments:
  -o <dir>, --outdir <dir>
                        output directory, current dir by default
  --no-gzip             do not compress output
  --fasta               output fasta only

sge arguments:
  -q [<str> ...], --queue [<str> ...]
                        sge queue, multi-queue can be sepreated by whitespace, all.q by default
```

| options      | descriptions                                                 |
| ------------ | ------------------------------------------------------------ |
| -h/--help    | show this help message and exit                              |
| -i/--input   | input sra file                                               |
| -p/--process | divide chunks number, 10 by default                          |
| -l/--log     | process logging file, stdout by default                      |
| --local      | running all chunked jobs in localhost instead of sge cluster |
| -o/--output  | output directory                                             |
| --no-gzip    | do not gzip output, gzip output by default                   |
| --fasta      | output fasta instead of fastq                                |
| -q/--queue   | running all chunked jobs in sge queue if set,  `all.q` by default |

![dump](https://user-images.githubusercontent.com/18365846/201566132-b3d8e0d3-426e-44f5-b9d6-6db58020dbff.png)

### 4. License

`srautils` is distributed under the [MIT License](https://github.com/yodeng/srautils/blob/master/LICENSE).

### 5. Reference

+ [NIH NCBI Sequence Read Archive (SRA) on AWS](https://registry.opendata.aws/ncbi-sra/)
+ [ncbi/sra-tools](https://github.com/ncbi/sra-tools)
