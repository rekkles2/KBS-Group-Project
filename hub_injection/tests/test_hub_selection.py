import unittest
from src.compute_degrees import compute_degrees
from src.select_hubs import rank_eligible, initial_k, expand_k, selected_hubs
from tests.helpers import fixture, node, edge


class HubSelectionTests(unittest.TestCase):
    def test_multirelational_degree_self_loop(self):
        graph = {'nodes': [node('Q1','Person'), node('Q2','Person')],
                 'edges': [edge('Q1','P26','Q2'), edge('Q1','P54','Q2'), edge('Q1','P26','Q1')]}
        degrees = compute_degrees(graph)
        self.assertEqual(degrees['Q1'], {'in_degree': 1, 'out_degree': 3, 'total_degree': 4})
        self.assertEqual(degrees['Q2']['total_degree'], 2)
        self.assertEqual(sum(d['total_degree'] for d in degrees.values()), 6)

    def test_lexical_ties_per_type(self):
        graph = fixture()
        degrees = {n['id']: {'in_degree': 1,'out_degree': 1,'total_degree': 2} for n in graph['nodes']}
        self.assertEqual(rank_eligible(graph, degrees), {'Person': ['Q1','Q2','Q3'], 'SportsTeam': ['Q10','Q11']})

    def test_flags_unknown_ineligible_and_isolated_excluded(self):
        graph = fixture()
        graph['nodes'][0]['general_type_annotation']['data_quality_flags'] = ['uncertain']
        graph['nodes'][1]['general_type_annotation']['eligible_for_type_swap'] = False
        graph['nodes'][2]['entity_type'] = 'Unknown'
        graph['nodes'].append(node('Q99','Person'))
        groups = rank_eligible(graph, compute_degrees(graph))
        self.assertNotIn('Person', groups)
        self.assertNotIn('Unknown', groups)

    def test_k_formula_and_expansion(self):
        groups = {'a': list(range(1000)), 'b': list(range(3)), 'c': [1]}
        sizes = initial_k(groups)
        self.assertEqual(sizes, {'a':20, 'b':2, 'c':0})
        self.assertEqual(expand_k(groups, sizes), {'a':40,'b':3,'c':0})
        self.assertNotIn('c', selected_hubs(groups, sizes))
        with self.assertRaises(ValueError): initial_k(groups, 1)
