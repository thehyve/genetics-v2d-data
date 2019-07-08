import os

import argparse
import pandas as pd


def write_df_to_parquet(df, args, filename):
    df.to_parquet(os.path.join(args.output_dir, filename))


def merge_files(files, additional_file=False):
    file_list = list()

    if additional_file and additional_file != 'None':
        file_list.append(additional_file)

    for file in files:
        df = pd.read_parquet(file)
        file_list.append(df)

    return pd.concat(file_list, axis=0, ignore_index=True)


def parse_args():
    """ Load command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument('--studies', metavar="<parquet file(s)>", nargs='+',
                        help="Location of the studies", type=str, required=True)
    parser.add_argument('--output_dir', metavar="<str>", help="Output directory", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    merged_studies = merge_files(args.studies)
    write_df_to_parquet(merged_studies, args, 'studies.parquet')


if __name__ == '__main__':
    main()
