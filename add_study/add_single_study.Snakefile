import pandas as pd

# Load configuration
configfile: 'config.yaml'

hap1000G_pops = ['EUR', 'EAS', 'AMR', 'AFR', 'SAS']
hap1000G_chroms = list(range(1, 23)) + ['X']

study_df = pd.read_csv(config['study_file'], header=0)


rule all:
    input:
        expand('{output_dir}/{study_id}/study.csv', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/study.parquet', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/toploci.parquet', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/ld_analysis_input.tsv.gz', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/ld/', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/ld/top_loci_variants.ld.gz', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/ld/study_weighted.ld.gz', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/{study_id}/ld.parquet', study_id=study_df.study_id, output_dir=config['output_dir']),
        expand('{output_dir}/parquet_files/', output_dir=config['output_dir'])


rule get_studies:
    input:
        config['study_file']
    output:
        expand('{output_dir}/{study_id}/study.csv', study_id=study_df.study_id, output_dir=config['output_dir'])
    run:
        for index, study in study_df.iterrows():
            study.to_csv(output[index])


rule make_study_table:
    input:
        '{output_dir}/{study_id}/study.csv'
    output:
        '{output_dir}/{study_id}/study.parquet'
    shell:
        'python scripts/create_study_table.py '
        '--study {input} '
        '--output_dir {output} '


rule make_top_loci_table:
    input:
        '{output_dir}/{study_id}/study.csv'
    output:
        '{output_dir}/{study_id}/toploci.parquet',
    params:
        p_val = config['min_p_val']
    shell:
        'python scripts/create_top_loci_table.py '
        '--study {input} '
        '--output_dir {output} '
        '--min_p_val {params.p_val}'


rule make_ld_input_queries:
    input:
        loci = '{output_dir}/{study_id}/toploci.parquet',
        study = '{output_dir}/{study_id}/study.parquet',
        pop_map = config['gwascat_2_superpop']
    output:
        '{output_dir}/{study_id}/ld_analysis_input.tsv.gz',
    shell:
        'python ../scripts/create_ld_input_table.py '
        '--in_loci {input.loci} '
        '--in_study {input.study} '
        '--in_popmap {input.pop_map} '
        '--outf {output}'


rule calculate_r_using_plink:
    input:
        '{output_dir}/{study_id}/toploci.parquet',
    output:
        directory('{output_dir}/{study_id}/ld/')
    params:
        bfile_pref = config['1000_genomes_plink_data'],
        pops = hap1000G_pops,
        ld_window = config['ld_window'],
        min_r2 = config['min_r2'],
        cores = config['cores'],
        varfile = '{output_dir}/{study_id}/variant_list.txt',
    shell:
        'python ../scripts/calc_ld_1000G.v2.py '
        '--varfile {params.varfile} '
        '--bfile {params.bfile_pref} '
        '--pops {params.pops} '
        '--ld_window {params.ld_window} '
        '--min_r2 {params.min_r2} '
        '--max_cores {params.cores} '
        '--outdir {output} '
        '--delete_temp '


rule concat_ld_scores:
    input:
        '{output_dir}/{study_id}/ld/'
    output:
        '{output_dir}/{study_id}/ld/top_loci_variants.ld.gz'
    params:
        in_pattern = '{output_dir}/{study_id}/ld/\*.ld.tsv.gz'
    shell:
        'python ../scripts/merge_ld_outputs.py '
        '--inpattern {params.in_pattern} '
        '--output {output}'


rule calc_study_specific_weighted_r2:
    input:
        ld = '{output_dir}/{study_id}/ld/top_loci_variants.ld.gz',
        manifest = '{output_dir}/{study_id}/ld_analysis_input.tsv.gz'
    output:
        '{output_dir}/{study_id}/ld/study_weighted.ld.gz'
    shell:
        'python ../scripts/calc_study_weighted_ld.py '
        '--in_ld {input.ld} '
        '--in_manifest {input.manifest} '
        '--out {output}'


rule weight_studies_to_final:
    input:
        ld = '{output_dir}/{study_id}/ld/study_weighted.ld.gz',
        manifest = '{output_dir}/{study_id}/ld_analysis_input.tsv.gz'
    output:
        '{output_dir}/{study_id}/ld.parquet'
    params:
        min_r2=config['min_r2']
    shell:
        'python ../scripts/format_ld_table.py '
        '--inf {input.ld} '
        '--in_manifest {input.manifest} '
        '--outf {output} '
        '--min_r2 {params.min_r2}'


rule calculate_overlaps:
    input:
        top_loci=expand('{output_dir}/{study_id}/toploci.parquet', study_id=study_df.study_id, output_dir=config['output_dir']),
        linkage_disequilibrium=expand('{output_dir}/{study_id}/ld.parquet', study_id=study_df.study_id, output_dir=config['output_dir']),
        study=expand('{output_dir}/{study_id}/study.parquet', study_id=study_df.study_id, output_dir=config['output_dir'])
    output:
        directory('{output_dir}/parquet_files/')
    params:
        top_loci_existing=config['top_loci_parquet_file'],
        linkage_disequilibrium_existing=config['linkage_disequilibrium_parquet_file']
    run:
        shell(
        'python scripts/create_locus_overlap_table.py '
        '--top_loci {input.top_loci} '
        '--linkage_disequilibrium {input.linkage_disequilibrium} '
        '--top_loci_existing {params.top_loci_existing} '
        '--linkage_disequilibrium_existing {params.linkage_disequilibrium_existing} '
        '--output_dir {output}'
    )
        shell(
        'python scripts/merge_studies.py '
        '--studies {input.study} '
        '--output_dir {output}'
    )