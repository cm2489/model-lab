import unittest

from evals import metrics

GOLD = [
    {"id": "a", "label": "Health"},
    {"id": "b", "label": "Health"},
    {"id": "c", "label": "Taxation"},
    {"id": "d", "label": "Energy"},
]


class Classification(unittest.TestCase):
    def setUp(self):
        preds = [
            {"id": "a", "pred": "Health"},
            {"id": "b", "pred": "Taxation"},
            {"id": "c", "pred": "Taxation", "gold": "Health"},  # a wrong gold here must be ignored
            # "d" has no prediction at all
        ]
        self.c = metrics.classification(metrics.join(GOLD, preds))

    def test_accuracy_counts_invalid_as_wrong(self):
        self.assertEqual(self.c["n"], 4)
        self.assertEqual(self.c["correct"], 2)
        self.assertEqual(self.c["accuracy"], 0.5)

    def test_missing_prediction_is_invalid(self):
        self.assertEqual(self.c["invalid"], 1)
        self.assertEqual(self.c["invalid_rate"], 0.25)

    def test_per_label(self):
        pl = self.c["per_label"]
        self.assertEqual(pl["Health"], {"precision": 1.0, "recall": 0.5, "f1": 0.6667, "support": 2})
        self.assertEqual(pl["Taxation"]["precision"], 0.5)
        self.assertEqual(pl["Taxation"]["recall"], 1.0)
        self.assertEqual(pl["Energy"]["recall"], 0.0)

    def test_macro_f1(self):
        # Health 0.6667, Taxation 0.6667, Energy 0.0
        self.assertAlmostEqual(self.c["macro_f1"], round((0.6667 + 0.6667 + 0) / 3, 4), places=4)

    def test_confusions(self):
        pairs = {(x["gold"], x["pred"]) for x in self.c["top_confusions"]}
        self.assertEqual(pairs, {("Health", "Taxation"), ("Energy", metrics.INVALID)})


class Speed(unittest.TestCase):
    def test_percentiles(self):
        self.assertEqual(metrics.percentile([1, 2, 3, 4, 5], 50), 3)
        self.assertAlmostEqual(metrics.percentile([1, 2, 3, 4, 5], 90), 4.6)
        self.assertIsNone(metrics.percentile([], 50))

    def test_speed_block(self):
        s = metrics.speed([{"latency_s": 1.0, "gen_tps": 100}, {"latency_s": 3.0, "gen_tps": 200}])
        self.assertEqual(s["latency_p50_s"], 2.0)
        self.assertEqual(s["tokens_per_second"], 150.0)


class Cost(unittest.TestCase):
    ROWS = [{"input_tokens": 300, "output_tokens": 10}, {"input_tokens": 300, "output_tokens": 30}]

    def test_priced(self):
        # per bill: 300 in x $4/M + 20 out x $20/M = 0.0012 + 0.0004 = $0.0016 -> $1.60 per 1,000
        c = metrics.cost(self.ROWS, 4.0, 20.0, local=False)
        self.assertEqual(c["cost_per_1k_usd"], 1.6)

    def test_local_is_zero_and_says_so(self):
        c = metrics.cost(self.ROWS, None, None, local=True)
        self.assertEqual(c["cost_per_1k_usd"], 0.0)
        self.assertIn("local", c["cost_note"])

    def test_api_without_prices_is_unknown(self):
        c = metrics.cost(self.ROWS, None, None, local=False)
        self.assertIsNone(c["cost_per_1k_usd"])


if __name__ == "__main__":
    unittest.main()
