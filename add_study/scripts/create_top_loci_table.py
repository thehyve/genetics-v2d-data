import itertools
import os

import argparse
import numpy as np
import pandas as pd

# key: pandas datatype, value: column name
TYPES = {
    'str': ['study_id', 'chrom', 'ref', 'alt', 'directions'],
    'int64': ['pos', 'pval_exponent'],
    'float64': [
        'beta', 'beta_ci_lower', 'beta_ci_upper', 'odds_ratio',
        'oddsr_ci_lower', 'oddsr_ci_upper', 'pval_mantissa'
    ]
}


def make_var_file(df, args):
    """
    Function for creating the variant list with all genomic variants required for the pipeline
    :param df: Pandas Dataframe, containing all the lead variants
    :param args: argparse arguments containing the output directory
    :return:
    """
    output_dir = os.path.dirname(args.output_dir)
    output_file = os.path.join(output_dir, 'variant_list.txt')
    df['var_id'] = df['chrom'].str.cat([df['pos'], df['ref'], df['alt']], sep=":")
    df.to_csv(output_file, columns=['var_id'], header=False, index=False)


def make_parquet(df, args):
    """
    Created the parquet file with the pandas to parquet fuction
    :param df: input dataframe
    :param args: argparse arguments containing the output dir
    :return: None
    """
    df.to_parquet(args.output_dir)


def set_types(df):
    """
    Set the types for necessary for the parquet output
    :param df: input dataframe
    :return: dataframe with the given data types obtained from the TYPES variable
    """
    for dtype in TYPES.keys():
        df[TYPES[dtype]] = df[TYPES[dtype]].astype(dtype=dtype)
    return df


def transform_pval_column(pval, values):
    """
    Create the mantissa and exponent row of the top loci table
    :param pval: float, pvalue
    :param values: Pandas Series with all the variant information
    :return: None
    """
    exponent = np.floor(np.log10(pval))
    mantissa = pval/10**exponent
    values['pval_mantissa'] = mantissa
    values['pval_exponent'] = exponent


def transform_variant_name(variant, values):
    """
    Create separate columns of the index variant
    :param variant: index variant
    :param values: Pandas Series with all the variant information
    :return:
    """
    values['chrom'], values['pos'], values['ref'], values['alt'] = variant.split(':')


def extract_variants(meta_df, study_df, output_df):
    """
    Function for creating the output dataframe of all the input variants
    :param meta_df: Pandas Dataframe, containing all the study meta info
    :param study_df: Pandas Dataframe, containing all the variants
    :param output_df: Pandas Dataframe, output dataframe
    :return: None, filled output dataframe
    """
    columns = list(itertools.chain(*TYPES.values()))
    for index, variant in study_df.iterrows():
        values = {column: None for column in columns}
        values['study_id'] = meta_df.columns[0]
        values['beta'] = variant['beta']
        transform_variant_name(variant['variant'], values)
        transform_pval_column(variant['pval'], values)

        output_df.loc[index] = values


def open_study(args):
    """
    Opens the study and variant file
    :param args: Argparse arguments, containing the locations of the files
    :return: Pandas Dataframes that are created from the files
    """
    meta_df = pd.read_csv(args.study, index_col='study_id', header=0)
    df = pd.read_csv(meta_df.loc['study_location'][0], sep='\t', header=0)
    df = df[df['pval'] < args.min_p_val]
    return meta_df, df


def make_output_dataframe():
    """
    Creates empty output top loci dataframe
    :return: Pandas Dataframe, output dataframe
    """
    df = pd.DataFrame(columns=list(itertools.chain(*TYPES.values())))
    return df


def parse_args():
    """
    Load the command line arguments
    :return: args, argparse line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', metavar="<str>", help="Location of the study file", type=str, required=True)
    parser.add_argument('--min_p_val', metavar="<float>", help="Minimum p-value (default: 1e-5)",
                        type=float, required=False, default=0.00001)
    parser.add_argument('--output_dir', metavar="<str>", help="Output directory", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    output_df = make_output_dataframe()
    meta_df, study_df = open_study(args)
    extract_variants(meta_df, study_df, output_df)
    output_df = set_types(output_df)
    make_parquet(output_df, args)
    make_var_file(output_df, args)


if __name__ == '__main__':
    main()
