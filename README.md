Variant-disease tables
======================

This repositroy contains scripts to produce variant-to-disease (V2D) association tables for Open Targets Genetics.

### Contents

- [Usage](#usage)
- Tables produced by workflow
  1. [Top loci associations table](#top-loci-table)
  2. [Study information table](#study-table)
  3. [Finemapping (credible set) results table](#finemapping-table)
  4. [LD table](#ld-table)
  5. [Locus overlap table](#locus-overlap-table)

### Usage

```
# Install dependencies into isolated environment
conda env create -n v2d_data --file environment.yaml

# Activate environment
source activate v2d_data

# Alter configuration file
nano config.yaml

# Authenticate google cloud storage
gcloud auth application-default login

# Execute workflow (locally)
version_date=`date +%y%m%d`
cores=3
snakemake -s 1_make_tables.Snakefile --config version=$version_date --cores $cores
snakemake -s 2_calculate_LD_table.Snakefile --config version=$version_date --cores $cores
snakemake -s 3_make_overlap_table.Snakefile --config version=$version_date --cores $cores

# Dry-run gsutil rsync to copy from staging to live
gsutil -m rsync -rn gs://genetics-portal-staging/v2d/180904 gs://genetics-portal-data/v2d
```

### Tables

#### Top loci table

List of loci associated with disease. Currently this data comes from two sources: (i) [GWAS Catalog](https://www.ebi.ac.uk/gwas/docs/file-downloads), (ii) [Neale *et al.* UK Biobank summary statistics (version 1)](http://www.nealelab.is/uk-biobank).

##### Top loci columns
- `study_id`: unique identifier for study
- `variant_id_b37`: chrom_pos_ref_alt (build 37) identifier for variant. RSID to variant ID mapping is non-unique, therefore multiple IDs may exist separated by ';'
- `rsid`: RSID for each corresponding variant ID, separated by ';'
- `pval_mantissa`: the p-value coefficient when written in scientfic notation
- `pval_exponent`: the p-value exponent (base 10)

##### Top loci methods


1. Download [all associations](ftp://ftp.ebi.ac.uk/pub/databases/gwas/releases/latest)
2. Map rsIDs and chr:pos fields to variant_ids (GRCh37)
  - This is complicated by the fact that:
    - some GWAScat loci have mulitple rsid assignments
    - some rows don't have rsids, will use chrom:pos (GRCh37 assumed) instead
    - rsIDs/chrom:pos can map to multiple variant ids (e.g. rs773154059)
  - Steps:
    - Load GWAS Catalog data and explode multiSNPs into separate rows
    - Load HRC site list + Ensembl VCF and split multiallelic sites into multiple rows
    - For each assoc in gwascat, extract rsID from SNP_ID_CURRENT or SNPS
    - Variants are first joined to HRC sitelist VCF, then unmerged rows are joined to the Ensembl VCF. Join on:
      1. Where RSID starts with "rs", join to VCF on rsid
      2. Where RSID starts with "chr", split into chrom and pos then join to VCF on these fields
    - Make variant IDs in the format chr_pos_ref_alt
    - Use "risk allele" from GWAS Catalog to see if it is concordant with alt and ref. Keep those that are concordant or ambiguous (missing), remove those that are not concordant.
    - Collapse loci with multiple variant IDs into one row per locus
  - Notes:
    - Two associations don't have the same number of SNPs in SNPS, CHR_ID and
      CHR_POS. These have been dropped as they are ambiguous.
    - I am assuming that variants with id e.g. chr21:43693789 are from build GRCh37.
    - Associations that do not have an rsID or chr:pos will be dropped
    - Associations that do not have a match in the Ensembl VCF will be dropped.
3. Create standard format containing all required columns
  Steps:
    - Remove rows with no mapped `variant_id_b37`
    - Extract p-value mantissa and exponenet
    - GWAS Catalog sometimes enocodes subphenotypes as a sting under the "p-value (text)". Where there are multiple p-values when grouped by (study, variant), keep only the lowest p-value.
4. Append UKB top loci from the finemapping conditional analysis
  Steps:
    - Download finemapping results from GCS (`gs://uk_biobank_analysis/em21/neale_summary_statistics_20170915/finemapping/results/neale_ukb_uk10kref_180502.crediblesets.long.varids.tsv.gz`)
    - Select rows where `locus_index_varid == varid` as these will be the top loci
    - Make study_id from trait name (prepend "NEALEUKB_")
    - Set any p-values that == 0 to minimum float
    - Remove any rows where nominal p-value is > 1e-5
    - Extract pvalue mantissa and exponent.

###### Top loci notes
- GWAS Catalog RSIDs are mapped to variant IDs using (i) HRC sitelist VCF, (ii) Ensembl VCF. Therefore, if the variant is not in either of these it will be dropped from the top loci table.
- There can be multiple P-values for each (study, variant). This occurs where different subphenotypes (`P-VALUE (TEXT)`) are reported (e.g. different sexs, subpopulations). Occasionally there are multiple P-values for the same subphenotye also For the time being I will drop these.
- We have decided not to extract effect sizes/OR and SE. This this can't be done in a consistent way across studies, because:
  - Both alleles are not reported so the direction of the effect
    cannot be inferred unambiguously
  - The 95% CI column str in poorly formatted making it very difficult to parse
  - Many do not report effects

#### Study table

Information about each study found in the top loci table.

##### Study table columns
  - `study_id`: unique identifier for study
  - `pmid`: pubmed ID (GWAS Catalog studies only)
  - `pub_date`: publication date
  - `pub_journal`: publication journal
  - `pub_title`: publication title
  - `pub_author`: publication author
  - `trait_reported`: trait reported in publication
  - `trait_mapped`: ontology trait label
  - `trait_efos`: EFO short_form
  - `ancestry_initial`: ancestry of initial GWAS sample, separated by ';'
  - `ancestry_replication`: ancestry of replication GWAS sample, separated by ';'
  - `n_initial`: GWAS initial sample size
  - `n_replication`: GWAS replication sample size
  - `n_cases`: number of cases. Warning: there is currently no easy way to get this information from GWAS Catalog, therefore it is set to null

Merges to top loci table using `study_id`.

##### Study table methods

###### GWAS Catalog studies
Steps:
1. Get [GWAS Catalog study and ancestry information](https://www.ebi.ac.uk/gwas/docs/file-downloads).
2. Combined ancestry information into a single field.
3. Make trait_code hash using 16 characters from `hasher.hexdigest()[0:16]`
4. Remove rows with no sample size information (see note below)

Notes:
  - There are 18 studies where sample size == 0 because ancestry in API is null. Annalisa has recommended these studies be removed, as they are old curations that are not consistent with the rest of the catalog.

###### Neale UKB studies
Steps
  - Get and merge self-reported and ICD10 manual EFO curations
  - Map EFOs to mapped_trait
  - Load Neale et al manifest
  - Merge EFOs with manifest
  - Extract required columns
  - Create trait code using field code from Neale et al.
  - Add trait categories field, acquired from [Oxford BIG server](http://big.stats.ox.ac.uk/)

Todo:
  - Fix field `S72	EFO_000855` in EFO curation (short_form not recognised)

#### Finemapping table

Credible set analysis results used to link index variants to tag variants. Full finemapping methods can be seen here: https://github.com/opentargets/finemapping

##### Finemapping table columns
  - `study_id`: unique identifier for study
  - `index_variantid_b37`: unique variant identifier for index variant, chrom_pos_ref_alt (build 37)
  - `tag_variantid_b37`: unique variant identifier for tagging variant, chrom_pos_ref_alt (build 37)
  - `log10_ABF`: log10 of the approximate Bayes factor for this tagging variant
  - `posterior_prob`: posterior probability of causality for this tagging variant compared to other variants at this locus

Table is pre-filtered to contain only 95% credible set variants. Merges to top loci table using `study_id` and `index_variantid_b37`.

##### Finemapping table methods

Steps
  - Downlaod from from GCS
  - Make study ID frrom the field code
  - Filter to only keep those in 95% credible sets
  - Put into a standardised format (above)

#### LD table

Table of LD values linking index varaints to tag variants.

##### LD table columns
  - `study_id`: unique identifier for study
  - `index_variantid_b37`: unique variant identifier for index variant, chrom_pos_ref_alt (build 37)
  - `tag_variantid_b37`: unique variant identifier for tagging variant, chrom_pos_ref_alt (build 37)
  - `overall_r2`: overall R<sup>2</sup> averaged of superpopulations
  - `AFR_1000G_prop`: proportion of sample from AFR superpopulation
  - `AMR_1000G_prop`: proportion of sample from AMR superpopulation
  - `EAS_1000G_prop`: proportion of sample from EAS superpopulation
  - `EUR_1000G_prop`: proportion of sample from EUR superpopulation
  - `SAS_1000G_prop`: proportion of sample from SAS superpopulation

Table is pre-filtered to only contain R<sup>2</sup> > 0.7.

##### LD table methods

LD calculated for each (study_id, index_variant) pair using 1000 Genomes p3.

Methods:
  1. GWAS Catalog populations mapped to 1000 Genomes super populations
    - Manually curated. Suppl fig 6 from here https://arxiv.org/pdf/1805.03233.pdf is useful.
    - Curations in `configs/gwascat_superpopulation_lut.curated.tsv`
  2. Output list of index variants with super population proportions for each study (`ld_analysis_input.tsv.gz`). This file is used as the LD analysis input manifest.
  3. Prepare 1000 Genomes haplotypes. Script [available here](https://github.com/opentargets/genetics-backend/tree/master/reference_data/1000Genomes_phase3):
    1. Download
    2. Normalise to reference genome
    3. Extract samples separately for each super population
    4. Filter to remove MAF < 1% and genotypin-rate < 5%
    5. Convert to bed, bim, fam
  3. Use plink to calculate correaltion coefficients (R) for each index study in each 1000 superpopulation.
  4. Merge index variant correlation tables to input manifest
  4. Fisher-Z transform R coefficients.
  5. For each study take weighted average across populations weighting by sample size.
  6. Inverse-Fisher-Z transform to get R values
  7. Take R-squared and filter rows for overall R2 < 0.7.

Notes:
  - Studies with missing or NR ancestries will be assumed to be European

#### Locus overlap table

Table containing metrics on the degree of (tag variant) overlap between index variants with 5Mb of each other.

##### Locus overlap table columns
  - `study_id_A`: locusA unique identifier for study
  - `index_variantid_b37_A`: locusA unique variant identifier, chrom_pos_ref_alt (build 37)
  - `study_id_B`: locusB unique identifier for study
  - `index_variantid_b37_B`: locusB unique variant identifier, chrom_pos_ref_alt (build 37)
  - `set_type`: one of 'finemapping', 'ld' or 'combined' (see below)
  - `distinct_A`: number of tag variants distinct to locusA
  - `overlap_AB`: number of tag variants overlapping locusA and locusB
  - `distinct_B`: number of tag variants distinct to locusB

Only loci with >=1 overlapping tag variants are stored.

##### Locus overlap methods

Table showing the number of overlapping tag variants for each (study_id, index_variant) found within 5Mb of each other. This calculated using: (i) only finemapping sets, (ii) only LD sets, (iii) a combination of finemapping and LD, prefering finemapping over LD where available. The 'combined' set is used for the Genetics Portal.
