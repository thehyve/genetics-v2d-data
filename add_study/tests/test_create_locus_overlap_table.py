import unittest
import numpy as np

from add_study.scripts.create_locus_overlap_table import *


class TestLocusOverlap(unittest.TestCase):
    df_tl = pd.read_csv('data/test_tl.csv', header=0)
    df_ld = pd.read_csv('data/test_ld.csv', header=0)
    create_var_index(df_tl)
    create_var_index(df_ld, True)

    def test_create_var_index(self):
        self.assertTrue(np.any(self.df_tl.columns.values == 'var_index'))
        self.assertFalse(np.any(self.df_tl.columns.values == 'tag_var_index'))
        self.assertTrue(np.any(self.df_ld.columns.values == 'var_index'))
        self.assertTrue(np.any(self.df_ld.columns.values == 'tag_var_index'))

    def test_filter_ld(self):
        filtered_ld = filter_ld(df_ld=self.df_ld, df_tl=self.df_tl)
        self.assertTrue(np.all(filtered_ld['overall_r2'] > 0.7))
        self.assertFalse(np.any(
            filtered_ld['var_index'] == set(self.df_tl['var_index']).difference(set(self.df_ld['tag_var_index']))
        ))

    def test_calculate_overlap(self):
        overlap_df = calculate_overlap(self.df_ld)
        a=1


if __name__ == '__main__':
    unittest.main()
