import argparse
import pandas as pd


def make_parquet(df, args):
    df.to_parquet(args.output_dir)


def make_dataframe(args):
    df = pd.read_csv(args.study, index_col=0).drop(['study_location']).transpose()

    df['study_id'] = df.index
    df.iloc[0]['ancestry_initial'] = [df.iloc[0]['ancestry_initial']]
    df.iloc[0]['ancestry_replication'] = [df.iloc[0]['ancestry_replication']]

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
    df = make_dataframe(args)
    make_parquet(df, args)


if __name__ == '__main__':
    main()
