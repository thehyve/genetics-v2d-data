#!/bin/bash

version_date=`date +%y%m%d`
cores="${CORES:-3}"
snakemake -s 1_make_tables.Snakefile --config version=$version_date --cores $cores
snakemake -s 2_calculate_LD_table.Snakefile --config version=$version_date --cores $cores
snakemake -s 3_make_overlap_table.Snakefile --config version=$version_date --cores $cores
