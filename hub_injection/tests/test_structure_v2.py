import unittest
from unittest.mock import patch

from tools.analyze_structure_v2 import (clustering, components, degrees,
    degree_bin, path_without_tested_edge, projection, random_baseline, triple)


class StructuralTests(unittest.TestCase):
    def test_projection_clustering_and_directional_degree(self):
        edges = [{'source': s, 'relation': r, 'target': t} for s, r, t in
                 [('a', 'r', 'b'), ('b', 'r', 'a'), ('a', 'x', 'b'), ('b', 'r', 'c'), ('c', 'r', 'a')]]
        adj, counts = projection(['a', 'b', 'c', 'd'], edges)
        self.assertEqual(len(adj['a']), 2)
        self.assertEqual(degrees(adj, edges)['a'], {'in': 2, 'out': 2, 'total': 4})
        self.assertEqual(clustering(adj, 'a'), 1)
        self.assertEqual(clustering(adj, 'd'), 0)
        self.assertEqual(components(adj)[1]['count'], 2)
        self.assertEqual(path_without_tested_edge(adj, counts, 'a', 'b'), 1)

    def test_tested_edge_is_excluded(self):
        edges = [{'source': s, 'relation': 'r', 'target': t} for s, t in [('a', 'b'), ('b', 'c')]]
        adj, counts = projection(['a', 'b', 'c'], edges)
        self.assertIsNone(path_without_tested_edge(adj, counts, 'a', 'b'))
        edges.append({'source': 'a', 'relation': 'r', 'target': 'c'})
        adj, counts = projection(['a', 'b', 'c'], edges)
        self.assertEqual(path_without_tested_edge(adj, counts, 'a', 'b'), 2)

    def test_degree_bins(self):
        self.assertEqual([degree_bin(i) for i in [0, 1, 2, 3, 4, 7, 8]], [-1, 0, 1, 1, 2, 2, 3])

    def test_baseline_seed_constraints_and_forbidden(self):
        nodes = [{'id': q, 'entity_type': kind, 'general_type_annotation': {'eligible_for_type_swap': True}}
                 for q, kind in [('a', 'Person'), ('b', 'Person'), ('c', 'Person'), ('d', 'Person'), ('x', 'Org'), ('y', 'Org')]]
        edges = [{'source': s, 'relation': 'r', 'target': t} for s, t in [('a', 'x'), ('b', 'y'), ('c', 'y'), ('d', 'y')]]
        graph = {'nodes': nodes, 'edges': edges, 'questions': []}
        hub = [{'source': 'b', 'relation': 'r', 'target': 'x', 'injection_snapshots': ['S'],
                'injection_provenance': {'source_edge_index': 0, 'swaps': [{'position': 'source'}]}}]
        result, diagnostics = random_baseline(graph, hub, 12)
        self.assertEqual(result, random_baseline(graph, hub, 12)[0])
        self.assertNotIn(triple(result[0]), {triple(e) for e in edges})
        self.assertEqual(result[0]['target'], 'x')
        self.assertEqual(result[0]['changed_position'], 'source')
        self.assertEqual(result[0]['injection_snapshots'], ['S'])
        self.assertEqual(diagnostics['degree_bin_matched_edges'], 1)
        with patch('tools.analyze_structure_v2.qa_positive_triples', return_value={('b', 'r', 'x')}):
            for seed in range(10):
                self.assertNotEqual(random_baseline(graph, hub, seed)[0][0]['source'], 'b')
        two, _ = random_baseline(graph, hub + hub, 12)
        self.assertEqual(len({triple(e) for e in two}), 2)
        graph['nodes'][1]['general_type_annotation']['eligible_for_type_swap'] = False
        for seed in range(10):
            self.assertNotEqual(random_baseline(graph, hub, seed)[0][0]['source'], 'b')

    def test_reject_unsupported_both_position_stratum(self):
        graph = {'nodes': [], 'edges': [], 'questions': []}
        hub = [{'injection_provenance': {'swaps': [{'position': 'source'}, {'position': 'target'}]}}]
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            random_baseline(graph, hub, 0)
