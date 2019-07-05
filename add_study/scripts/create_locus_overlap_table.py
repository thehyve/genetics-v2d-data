import argparse
import pandas as pd

PARQUET_COLUMNS = [
    'A_chrom', 'A_pos', 'A_ref', 'A_alt', 'A_study_id',
    'B_chrom', 'B_pos', 'B_ref', 'B_alt', 'B_study_id',
    'AB_overlap', 'A_distinct', 'B_distinct'
]


def write_df_to_parquet(df, args):
    df.to_parquet(args.output_dir)


def write_overlap_row(var1, var2, tag1, tag2):
    row = pd.Series(index=PARQUET_COLUMNS)
    row['A_chrom'], row['A_pos'], row['A_ref'], row['A_alt'], row['A_study_id'] = var1[
        ['lead_chrom', 'lead_pos', 'lead_ref', 'lead_alt', 'study_id']]
    row['B_chrom'], row['B_pos'], row['B_ref'], row['B_alt'], row['B_study_id'] = var2[
        ['lead_chrom', 'lead_pos', 'lead_ref', 'lead_alt', 'study_id']]
    row['AB_overlap'] = len(set(tag1).intersection(set(tag2)))
    row['A_distinct'] = len(set(tag1).difference(set(tag2)))
    row['B_distinct'] = len(set(tag2).difference(set(tag1)))
    return row


def calculate_overlap(df_ld):
    overlap_df = pd.DataFrame(columns=PARQUET_COLUMNS)

    for index, variant in df_ld.iterrows():
        chromosome, pos = variant[['lead_chrom', 'lead_pos']].values
        tagged_variants = df_ld[df_ld['tag_var_index'] == variant['var_index']]['tag_var_index']
        in_range = df_ld[
            (df_ld['lead_chrom'] == chromosome) &
            (pos - 5000000 < df_ld['lead_pos']) &
            (pos + 5000000 > df_ld['lead_pos'])
            ]
        if not in_range.empty:
            for overlap_index, overlap_variant in in_range.iterrows():
                overlap_tagged_variants = df_ld[df_ld['tag_var_index'] == overlap_variant['var_index']]['tag_var_index']
                overlap_df = overlap_df.append(write_overlap_row(
                    variant, overlap_variant, tagged_variants, overlap_tagged_variants), ignore_index=True)

    return overlap_df


def filter_ld(df_ld, df_tl):
    intersecting_vars = pd.Series(list(set(df_tl['var_index']).intersection(set(df_ld['tag_var_index']))))
    df_ld = df_ld[df_ld['tag_var_index'].isin(intersecting_vars)]
    df_ld = df_ld[df_ld['overall_r2'] > 0.7]
    return df_ld


def create_var_index(df, ld=False):
    if ld:
        df['tag_var_index'] = df['tag_chrom'] + '_' + df['tag_pos'].map(str) + '_' + df['tag_ref'] + '_' + df['tag_alt']
        df['var_index'] = df['lead_chrom'] + '_' + df['lead_pos'].map(str) + '_' + df['lead_ref'] + '_' + df['lead_alt']
    else:
        df['var_index'] = df['chrom'] + '_' + df['pos'] + '_' + df['ref'] + '_' + df['alt']


def merge_files(files):
    file_list = list()
    for file in files:
        df = pd.read_parquet(file)
        file_list.append(df)
    return pd.concat(file_list, axis=0, ignore_index=True)


def load_dataframes(args):
    df_tl = merge_files(args.top_loci)
    df_ld = merge_files(args.linkage_disequilibrium)
    df_lo = None
    if args.locus_overlap != 'None':
        df_lo = pd.read_parquet(args.locus_overlap)
    return df_tl, df_ld, df_lo


def parse_args():
    """ Load command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument('--top_loci', metavar="<parquet file(s)>", nargs='+',
                        help="Location of top loci file(s)", type=str, required=True)
    parser.add_argument('--linkage_disequilibrium', metavar="<parquet file(s)>", nargs='+',
                        help="Location of newly creating top loci parquet file(s)", type=str, required=True)
    parser.add_argument('--locus_overlap', metavar="<parquet file", help="Location of an existing locus overlap file",
                        type=str, required=False)
    parser.add_argument('--output_dir', metavar="<str>", help="Output directory", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    df_tl, df_ld, df_lo = load_dataframes(args)
    create_var_index(df_tl)
    create_var_index(df_ld, True)
    df_ld = filter_ld(df_ld, df_tl)
    output_df = calculate_overlap(df_ld)
    write_df_to_parquet(output_df, args)


if __name__ == '__main__':
    main()
