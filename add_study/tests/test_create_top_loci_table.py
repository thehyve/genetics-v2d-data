import unittest
from unittest.mock import MagicMock

from add_study.scripts.create_study_table import *


class TestStudy(unittest.TestCase):
    """
      Unit test for the creation of the top loci Table
    """

    mock = MagicMock()
    mock.study = 'data/test_study.csv'
    study_df = make_dataframe(mock)

    def test_make_dataframe(self):
        """
        Test if the study dataframe could be loaded correctly
        """
        study_df = make_dataframe(self.mock)
        self.assertTrue(isinstance(study_df, pd.DataFrame))

    def test_set_types(self):
        """
        Test if all the datatypes of the study are set correctly
        """
        study_df = set_types(self.study_df)
        dtypes = study_df.dtypes
        self.assertTrue(dtypes[TYPES['bool']].any() == bool)
        self.assertTrue(dtypes[TYPES['str']].any() == object)
        self.assertTrue(dtypes[TYPES['int64']].any() == int)


if __name__ == '__main__':
    unittest.main()
