import argparse
import pandas as pd

# key: pandas datatype, value: column name
TYPES = {
    'str': ['study_id', 'pmid', 'pub_date', 'pub_journal',
            'pub_title', 'pub_author', 'trait_reported', 'trait_category'
            ],
    'int64': [
            'n_initial', 'n_replication', 'n_cases', 'num_assoc_loci'
            ],
    'bool': [
            'has_sumstats'
            ]
}


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


def make_dataframe(args):
    """
    Reads a study file from the input arguments and converts it to a dataframe
    :param args: argparse arguments pointing to the study file location
    :return: Pandas dataframe
    """
    df = pd.read_csv(args.study, index_col=0).drop(['study_location']).transpose()

    df['study_id'] = df.index

    list_columns = ['trait_efos', 'ancestry_initial', 'ancestry_replication']
    for column in list_columns:
        df[column] = df[column].apply(lambda x: x.split(';'))

    return df


def parse_args():
    """
    Load the command line arguments
    :return: args, argparse line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', metavar="<str>", help="Location of the study file", type=str, required=True)
    parser.add_argument('--output_dir', metavar="<str>", help="Output directory", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    df = make_dataframe(args)
    df = set_types(df)
    make_parquet(df, args)


if __name__ == '__main__':
    main()
