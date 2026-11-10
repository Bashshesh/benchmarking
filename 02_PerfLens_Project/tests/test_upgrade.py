"""Public adapter/recommendation boundaries; values below are synthetic fixtures."""
import unittest
from upgrade.metrics import jmh_single_fork, permitted_jvm, recommend, dependence
from upgrade.workloads.redundant import sum_squares_mod97, oracle

class UpgradeTests(unittest.TestCase):
    def test_one_jmh_fork_is_one_sample_not_each_iteration(self):
        record=[dict(forks=1,mode='avgt',primaryMetric=dict(score=1000,scoreUnit='ns/op',rawData=[[900,1100]]))]
        result=jmh_single_fork(record)
        self.assertAlmostEqual(result['seconds'],.000001)
        self.assertEqual(result['within_fork_iterations'],[900,1100])
        record[0]['forks']=2
        record[0]['primaryMetric']['rawData']=[[900,1100],[1000,1000]]
        with self.assertRaisesRegex(ValueError,'independent'):
            jmh_single_fork(record)

    def test_unknown_or_instrumenting_configuration_is_rejected(self):
        self.assertEqual(permitted_jvm('default'),[])
        with self.assertRaises(ValueError):
            permitted_jvm('-javaagent:untrusted.jar')

    def test_recommendation_requires_correctness_confirmation_and_resource_evidence(self):
        good=dict(decision='improvement',ci95_percent=[-20,-10])
        self.assertEqual(recommend('default','tier1',good,False,1)['selected'],'default')
        self.assertEqual(recommend('default','tier1',good,True,1.2)['selected'],'default')
        self.assertEqual(recommend('default','tier1',good,True,None)['selected'],'default')
        self.assertEqual(recommend('default','tier1',good,True,.9)['selected'],'tier1')
        self.assertEqual(recommend('default','tier1',dict(decision='inconclusive',ci95_percent=[-20,5]),True,.9)['selected'],'default')

    def test_redundant_workload_has_independent_known_results(self):
        for n,value in [(1,0),(2,1),(3,5),(5,30),(97,4656),(98,4656)]:
            self.assertEqual(sum_squares_mod97(n),value)
            self.assertEqual(oracle(n),value)

    def test_drift_diagnostic_does_not_claim_independence(self):
        result=dependence([1,1,2,2])
        self.assertEqual(result['second_half_change_percent'],100)
        self.assertIsNone(dependence([1,1,1,1])['lag_one_descriptive'])
