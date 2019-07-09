import unittest
import numpy as np

from add_study.scripts.create_locus_overlap_table import *


class TestLocusOverlap(unittest.TestCase):
    """
    Unit test for the creation of the Locus Overlap Table
    """

    df_tl = pd.read_csv('data/test_tl.csv', header=0)
    df_ld = pd.read_csv('data/test_ld.csv', header=0)
    create_var_index(df_tl)
    create_var_index(df_ld, True)

    def test_create_var_index(self):
        """
        Test for creating the index columns
        """
        self.assertTrue(np.any(self.df_tl.columns.values == 'var_index'))
        self.assertFalse(np.any(self.df_tl.columns.values == 'tag_var_index'))
        self.assertTrue(np.any(self.df_ld.columns.values == 'var_index'))
        self.assertTrue(np.any(self.df_ld.columns.values == 'tag_var_index'))

    def test_filter_ld(self):
        """
        Test for filtering the ld tagged variants
        """
        filtered_ld = filter_ld(df_ld=self.df_ld, df_tl=self.df_tl)

        # All variants should have an overall r2 above 0.7 and must contain the the top loci table
        self.assertTrue(np.all(filtered_ld['overall_r2'] > 0.7))
        self.assertFalse(np.any(
            filtered_ld['var_index'] == set(self.df_tl['var_index']).difference(set(self.df_ld['tag_var_index']))
        ))

    def test_calculate_overlap(self):
        """
        Test whether the overlap dataframe gets created correctly
        """
        overlap_df = calculate_overlap(self.df_ld)
        self.assertFalse(overlap_df.empty)

    def test_set_types(self):
        """
        Test if all the pandas data types are set correctly following the right documented types see:
        https://github.com/opentargets/genetics-v2d-data
        """
        overlap_df = calculate_overlap(self.df_ld)
        overlap_df = set_types(overlap_df)
        dtypes = overlap_df.dtypes
        self.assertTrue(dtypes[TYPES['str']].any() == object)
        self.assertTrue(dtypes[TYPES['int64']].any() == int)


if __name__ == '__main__':
    unittest.main()
