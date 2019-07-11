#!/bin/bash

set -e

if [ $# -ne 3 ]; then
    echo "Calculates v2d parquet files for a study"
    echo "Usage: $0 1000Genomes_phase3/ input/ output/"
    exit 1
fi

script_d=$(cd $(dirname "$0") && pwd)
v2d_d="$(cd "$script_d/.." && pwd)"
_1000g_d="$(cd $1 && pwd)"
in_d="$(cd $2 && pwd)"
mkdir -p $3 
out_d="$(cd $3 && pwd)"

docker build "$v2d_d" --tag v2d

docker run -it --rm \
    -v "$_1000g_d":/1000Genomes_phase3/ \
    -v "$in_d":/v2d/add_study/input \
    -v "$out_d":/v2d/add_study/output \
    v2d \
    bash -c 'cd add_study && snakemake -s add_single_study.Snakefile --delete-all-output && snakemake -s add_single_study.Snakefile'
