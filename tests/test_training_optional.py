import importlib.util
from pathlib import Path
import tempfile
import unittest


@unittest.skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('transformers'), 'install the train extra')
class TrainingSmokeTests(unittest.TestCase):
    def test_real_transformer_train_save_reload_and_predict(self):
        from small_auto_mode.training import smoke_run
        from small_auto_mode.local_model import LocalClassifier
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'model'
            metadata,report=smoke_run(out)
            self.assertTrue(metadata['smoke_only'])
            self.assertFalse(metadata['deployment_validated'])
            self.assertLess(metadata['parameters'],1_000_000_000)
            predictor=LocalClassifier(out)
            p=predictor({'user_intent':'read','tool':{'name':'read','arguments':{}},'environment':{}})
            self.assertEqual(set(p),{'allow','ask','deny'})
            self.assertAlmostEqual(sum(p.values()),1.)
            self.assertEqual(report['examples'],3)


if __name__=='__main__':unittest.main()
