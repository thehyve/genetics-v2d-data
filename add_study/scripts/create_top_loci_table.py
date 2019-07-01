import os

import argparse
import numpy as np
import pandas as pd

COLUMNS = [
    'study_id', 'chrom', 'pos', 'ref', 'alt',
    'directions', 'beta', 'beta_ci_lower', 'beta_ci_upper',
    'odds_ratio', 'oddsr_ci_lower', 'oddsr_ci_upper',
    'pval_mantissa', 'pval_exponent'
]


def make_var_file(df, args):
    output_dir = os.path.dirname(args.output_dir)
    output_file = os.path.join(output_dir, 'variant_list.txt')
    df['var_id'] = df['chrom'].str.cat([df['pos'], df['ref'], df['alt']], sep=":")
    df.to_csv(output_file, columns=['var_id'], header=False, index=False)


def make_parquet(df, args):
    df.to_parquet(args.output_dir)


def transform_pval_column(pval, values):
    exponent = np.floor(np.log10(pval))
    mantissa = pval/10**exponent
    values['pval_mantissa'] = mantissa
    values['pval_exponent'] = exponent


def transform_variant_name(variant, values):
    values['chrom'], values['pos'], values['ref'], values['alt'] = variant.split(':')


def extract_variants(meta_df, study_df, output_df):
    for index, variant in study_df.iterrows():
        values = {column: None for column in COLUMNS}
        values['study_id'] = meta_df.columns[0]
        values['beta'] = variant['beta']
        transform_variant_name(variant['variant'], values)
        transform_pval_column(variant['pval'], values)

        output_df.loc[index] = values


def open_study(args):
    meta_df = pd.read_csv(args.study, index_col='study_id', header=0)
    df = pd.read_csv(meta_df.loc['study_location'][0], sep='\t', header=0)
    df = df[df['pval'] < 0.0001]
    return meta_df, df


def make_output_dataframe():
    df = pd.DataFrame(columns=COLUMNS)
    return df


def parse_args():
    """ Load command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', metavar="<str>", help="Location of the study file", type=str, required=True)
    parser.add_argument('--output_dir', metavar="<str>", help="Output directory", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    output_df = make_output_dataframe()
    meta_df, study_df = open_study(args)
    extract_variants(meta_df, study_df, output_df)
    make_parquet(output_df, args)
    make_var_file(output_df, args)


if __name__ == '__main__':
    main()
