Loading a single GWAS study 
===========================

Here a pipeline is presented focused on creating the input parquet files required for the data loading [pipeline](https://github.com/opentargets/genetics-pipe/). Before execution, the config.yaml has to be configured and a study file must be created.

The pipeline depends on the same environment described on the main [page](https://github.com/opentargets/genetics-v2d-data)

For calculating the linkage disequilibrium parquet file, the 1000genomes files must be created following some [specific](https://github.com/opentargets/genetics-backend/tree/master/reference_data/1000Genomes_phase3) actions.  

Run
---

You can run the pipeline with docker as below:

```bash
./add_study.sh /path-to/plink_format_b38/ input/ output/
```

`input/` directory has to have `gwas_studies.csv` file in the conventional format.

config.yaml
-----------
The config file requires only a few parameters to be set. 
It consists out of the following parameters.

```yaml
cores: 8

# IO directories
study_file: 'input/gwas_studies.csv' # Location of the study file
output_dir: 'output' # Output directory of the pipeline 
1000_genomes_plink_data: '/path/to/plink_format_b38/POPULATION/POPULATION.CHROM.1000Gp3.20130502' # directory of the 1000genomes data
gwascat_2_superpop: '../configs/gwascat_superpopulation_lut.curated.v2.tsv'

# LD parameters
ld_window: 500
min_r2: 0.7
```

Study file
----------
The study file consists out of predefined columns describing both some meta information about the study and the directory of the GWAS study. 
The file is formatted in a csv format and can contain 1 or multiple studies. 

The following columns are required in the study file:
* study_id: unique identifier for study
* pmid: pubmed ID
* pub_date: publication date
* pub_journal: publication journal
* pub_title: publication title
* pub_author: publication author
* trait_reported: trait reported in publication
* trait_efos: EFO short_form
* ancestry_initial: ancestry of initial GWAS sample, separated by ';'
* ancestry_replication: ancestry of replication GWAS sample, separated by ';'
* n_initial: GWAS initial sample size
* n_replication: GWAS replication sample size
* n_cases: number of cases
* trait_category: Category of the trait
* num_assoc_loci: total number of associated loci for this study in the top loci table
* has_sumstats: (boolean: True/False) if the study contains summary statistics data
* study_location: Location of the study file containing GWAS variant info

Example study_file.csv 
```csv
study_id,pmid,pub_date,pub_journal,pub_title,pub_author,trait_reported,trait_efos,ancestry_initial,ancestry_replication,n_initial,n_replication,n_cases,trait_category,num_assoc_loci,has_sumstats,study_location
study1,pmid,11-11-11,nature,test_title,author_name,disease,efo01,100,200,300,400,600,dis,1200,false,input/test_grch38.tsv
study2,pmid,11-11-11,nature,test_title,author_name,disease,efo01,100,200,300,400,600,dis,1200,false,input/test_grch38.tsv
```

Executing the pipeline
----------------------
Once everything has been set, the pipeline can executed with the following command:
```bash
$ snakemake -s add_single_study.Snakefile
```
