import math
import unittest

from summarize import exact_binomial_interval


class StatisticalTests(unittest.TestCase):
    def test_exact_two_trial_intervals_match_closed_form_bounds(self):
        zero=exact_binomial_interval(0,2)
        both=exact_binomial_interval(2,2)
        self.assertEqual(zero[0],0)
        self.assertAlmostEqual(zero[1],1-math.sqrt(.025))
        self.assertAlmostEqual(both[0],math.sqrt(.025))
        self.assertEqual(both[1],1)


if __name__=='__main__':
    unittest.main()
