import itertools
import os

import argparse
import pandas as pd

# key: pandas datatype, value: column name
TYPES = {
    'str': ['A_chrom', 'B_chrom', 'A_ref', 'A_alt', 'A_study_id',
            'B_ref', 'B_alt', 'B_study_id'
            ],
    'int64': [
        'A_pos', 'B_pos', 'AB_overlap',
        'A_distinct', 'B_distinct'
    ]
}


def write_df_to_parquet(df, args, filename):
    """
    Created the parquet file with the pandas to parquet fuction
    :param df: input dataframe
    :param args: argparse arguments containing the output dir
    :param filename: name of the output parquet file
    :return: None
    """
    df.to_parquet(os.path.join(args.output_dir, filename))


def set_types(df):
    """
    Set the types for necessary for the parquet output
    :param df: input dataframe
    :return: dataframe with the given data types obtained from the TYPES variable
    """
    for dtype in TYPES.keys():
        df[TYPES[dtype]] = df[TYPES[dtype]].astype(dtype=dtype)
    return df


def write_overlap_row(var1, var2, tag1, tag2):
    """
    Function for creating a locus overlap row
    :param var1: Pandas Series, genetic variant
    :param var2: Pandas Series, genetic variant 2 in range of variant 1
    :param tag1: Pandas Dataframe, all tagged variants of var 1
    :param tag2: Pandas Dataframe, all tagged variants of var 2
    :return: Pandas series containing all locus overlap column values
    """
    row = pd.Series(index=list(itertools.chain(*TYPES.values())))
    row['A_chrom'], row['A_pos'], row['A_ref'], row['A_alt'], row['A_study_id'] = var1[
        ['lead_chrom', 'lead_pos', 'lead_ref', 'lead_alt', 'study_id']]
    row['B_chrom'], row['B_pos'], row['B_ref'], row['B_alt'], row['B_study_id'] = var2[
        ['lead_chrom', 'lead_pos', 'lead_ref', 'lead_alt', 'study_id']]
    row['AB_overlap'] = len(set(tag1).intersection(set(tag2)))
    row['A_distinct'] = len(set(tag1).difference(set(tag2)))
    row['B_distinct'] = len(set(tag2).difference(set(tag1)))
    return row


def calculate_overlap(df_ld, args):
    """
    Calculating the overlapping lead and tag variants and overlapping tag variants
    :param df_ld: Pandas Dataframe, linkage disequilibrium dataframe
    :param args: argsparse arguments, required for the overlap range
    :return: overlap_df: Pandas Dataframe, output of all overlapping loci
    """
    overlap_df = pd.DataFrame(columns=list(itertools.chain(*TYPES.values())))

    for index, variant in df_ld.iterrows():
        chromosome, pos = variant[['lead_chrom', 'lead_pos']].values
        tagged_variants = df_ld[df_ld['var_index'] == variant['var_index']]['tag_var_index']
        # Calculating all the lead variants within the range
        in_range = df_ld[
            (df_ld['lead_chrom'] == chromosome) &
            (pos - args.overlap_range < df_ld['lead_pos']) &
            (pos + args.overlap_range > df_ld['lead_pos'])
            ]
        if not in_range.empty:
            for overlap_index, overlap_variant in in_range.iterrows():
                overlap_tagged_variants = df_ld[df_ld['var_index'] == overlap_variant['var_index']]['tag_var_index']
                overlap_df = overlap_df.append(write_overlap_row(
                    variant, overlap_variant, tagged_variants, overlap_tagged_variants), ignore_index=True)

    return overlap_df


def filter_ld(df_ld, df_tl, args):
    """
    Filtering the linkage disequilibrium variants not having the right requirements
    :param df_ld: Pandas Dataframe, linkage disequilibrium values
    :param df_tl: Pandas Dataframe, Top Loci values
    :param args: Argparse arguments, needed for the minimum r2 value
    :return: Pandas Dataframe, filtered linkage disequilibrium dataframe
    """
    intersecting_vars = pd.Series(list(set(df_tl['var_index']).intersection(set(df_ld['tag_var_index']))))
    df_ld = df_ld[df_ld['tag_var_index'].isin(intersecting_vars)]
    df_ld = df_ld[df_ld['overall_r2'] > args.min_r2]
    return df_ld


def create_var_index(df, ld=False):
    """
    Creation of the variant index column joining the chrom, pos, ref and alt.
    :param df: Pandas Dataframe,
    :param ld: Boolean, boolean whether the dataframe contains ld data
    :return:
    """
    if ld:
        df['tag_var_index'] = df['tag_chrom'].map(str) + '_' + df['tag_pos'].map(str) \
                              + '_' + df['tag_ref'] + '_' + df['tag_alt']
        df['var_index'] = df['lead_chrom'].map(str) + '_' + df['lead_pos'].map(str) \
                          + '_' + df['lead_ref'] + '_' + df['lead_alt']
    else:
        df['var_index'] = df['chrom'].map(str) + '_' + df['pos'].map(str) + '_' + df['ref'] + '_' + df['alt']


def merge_files(files, additional_file=False):
    """
    Merge files into a single dataframe
    :param files: All files of the same format required for merging
    :param additional_file: Possibility of adding an extra file to be merged
    :return: Pandas Datamframe, dataframe with all merged files
    """
    file_list = list()

    if additional_file or additional_file != 'None':
        file_list.append(additional_file)

    for file in files:
        df = pd.read_parquet(file)
        file_list.append(df)

    return pd.concat(file_list, axis=0, ignore_index=True)


def load_dataframes(args):
    """
    Function for loading the Pandas Dataframes from the argparse arguments
    :param args: argparse arguments containing the location of the files
    :return: Pandas Dataframes, the merged loaded files
    """
    df_tl = merge_files(args.top_loci, args.top_loci_existing)
    df_ld = merge_files(args.linkage_disequilibrium, args.linkage_disequilibrium_existing)

    # Write merged dfs to parquet file
    write_df_to_parquet(df_tl, args, 'toploci.parquet')
    write_df_to_parquet(df_ld, args, 'ld.parquet')

    return df_tl, df_ld


def parse_args():
    """
    Load the command line arguments
    :return: args, argparse line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--top_loci', metavar="<parquet file(s)>", nargs='+',
                        help="Location of top loci file(s)", type=str, required=True)
    parser.add_argument('--linkage_disequilibrium', metavar="<parquet file(s)>", nargs='+',
                        help="Location of newly creating top loci parquet file(s)", type=str, required=True)
    parser.add_argument('--top_loci_existing', metavar="<parquet file", default=False,
                        help="Location of an existing top loci file", type=str, required=False)
    parser.add_argument('--linkage_disequilibrium_existing', metavar="<parquet file>", default=False,
                        help="Location of an existing linkage disequilibrium file",
                        type=str, required=False)
    parser.add_argument('--overlap_range', metavar="<int>", default=5000000,
                        help="Range for calculating overlap between lead variants",
                        type=int, required=False)
    parser.add_argument('--min_r2', metavar="<float>", default=0.7,
                        help="Minimum r2 for filtering LD tagged variants",
                        type=float, required=False)
    parser.add_argument('--output_dir', metavar="<str>", help="Output directory", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    df_tl, df_ld = load_dataframes(args)
    create_var_index(df_tl)
    create_var_index(df_ld, True)
    df_ld = filter_ld(df_ld, df_tl, args)
    output_df = calculate_overlap(df_ld, args)
    output_df = set_types(output_df)
    write_df_to_parquet(output_df, args, 'loci_overlap.parquet')


if __name__ == '__main__':
    main()
