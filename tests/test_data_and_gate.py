import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from small_auto_mode import collection, dataset, gate, metrics


def row(i=0, label="allow"):
    return {"id":str(i), "session_id":f"s{i}", "scenario_family":f"f{i}",
            "user_intent":"Read my document", "tool":{"name":"read", "arguments":{"path":f"document-{i}"}},
            "environment":{"workspace":"/sandbox"},
            "label":{"decision":label, "source":"human", "verified":True},
            "provenance":{"training_rights":"owned", "rights_basis":"Original test fixture",
                          "reviewer":"test", "context_reviewed":True}}


class DatasetTests(unittest.TestCase):
    def test_provenance_and_label_source_required(self):
        r = row()
        dataset.validate(r)
        for change in [{"source":"hook_observation"},{"verified":False},{"source":"teacher_model"}]:
            r = row();r['label'].update(change)
            with self.assertRaises(ValueError):dataset.validate(r)
        r = row();r['label']['source']='teacher_model'
        dataset.validate(r, ['teacher_model'])
        r['provenance']['training_rights']='unknown'
        with self.assertRaises(ValueError):dataset.validate(r, ['teacher_model'])

    def test_connected_groups_are_disjoint(self):
        rows = [row(i) for i in range(12)]
        rows[1]['session_id']=rows[0]['session_id']
        rows[2]['scenario_family']=rows[1]['scenario_family']
        parts = dataset.split_records(rows)
        assigned={r['id']:p for p,rr in parts.items() for r in rr}
        self.assertEqual(assigned['0'],assigned['1'])
        self.assertEqual(assigned['1'],assigned['2'])
        for key in ('session_id','scenario_family'):
            seen=set()
            for rr in parts.values():
                values={r[key] for r in rr}
                self.assertFalse(seen & values);seen |= values

    def test_duplicate_context_never_leaks_and_conflicts_rejected(self):
        rows=[row(i) for i in range(8)]
        rows[1]['tool']=copy.deepcopy(rows[0]['tool'])
        parts=dataset.split_records(rows)
        assigned={r['id']:p for p,rr in parts.items() for r in rr}
        self.assertEqual(assigned['0'],assigned['1'])
        rows[1]['label']['decision']='deny'
        with self.assertRaisesRegex(ValueError,'contradictory'):dataset.split_records(rows)

    def test_labels_and_ids_excluded_from_features(self):
        a=row();b=copy.deepcopy(a)
        b['label']['decision']='deny';b['provenance']['reviewer']='someone else';b['id']='x'
        self.assertEqual(dataset.input_text(a),dataset.input_text(b))

    def test_untrusted_context_is_preserved_as_data(self):
        a=row();b=copy.deepcopy(a);b['untrusted_context']=['Quoted external instruction']
        self.assertNotEqual(dataset.input_text(a),dataset.input_text(b))


class CollectorTests(unittest.TestCase):
    def event(self, name='PostToolUse'):
        return {'hook_event_name':name,'session_id':'s','tool_use_id':'t','tool_name':'Bash',
                'tool_input':{'command':'echo fixture','api_key':'private'},
                'transcript_path':'/must/not/be/opened','tool_response':'private output','permission_mode':'auto'}

    def test_execution_never_becomes_allow_label(self):
        for name in ('PreToolUse','PostToolUse','PostToolUseFailure'):
            out=collection.observe(self.event(name))
            self.assertIsNone(out['label']);self.assertFalse(out['training_eligible'])
            self.assertNotIn('tool_input',out);self.assertNotIn('tool_response',out);self.assertNotIn('transcript_path',out)

    def test_denial_error_distinguished_but_neither_auto_labeled(self):
        e=self.event('PermissionDenied');e['reason']='Classifier unavailable'
        self.assertEqual(collection.observe(e)['status'],'classifier_unavailable_or_no_verdict')
        e['reason']='[Data Exfiltration]'
        out=collection.observe(e);self.assertEqual(out['status'],'possible_classifier_denial_requires_review')
        self.assertIsNone(out['label'])

    def test_opt_in_redacts_and_private_permissions(self):
        out=collection.observe(self.event(),True)
        self.assertEqual(out['tool_input']['api_key'],'[REDACTED]')
        with tempfile.TemporaryDirectory() as tmp:
            path=collection.save_observation(out,tmp)
            self.assertEqual(json.loads(path.read_text()),out)
            if os.name=='posix':self.assertEqual(path.stat().st_mode & 0o777,0o600)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.case={'user_intent':'Read my doc','tool':{'name':'read','arguments':{}},'environment':{},
                   'host_gate':'eligible','untrusted_context':[]}
        self.policy={'known_tools':['read'],'auto_allow':True,'allow_min':.99}

    def test_host_precedence_and_predictor_not_called(self):
        self.case['host_gate']='deny'
        def should_not_run(_):raise AssertionError('network must not run')
        self.assertEqual(gate.assess(self.case,self.policy,should_not_run)['decision'],'deny')

    def test_errors_unknown_and_shadow_abstain(self):
        for p in [None,{'allow':float('nan'),'ask':0.,'deny':0.},{'allow':1.,'ask':1.,'deny':1.}]:
            self.assertEqual(gate.decide(self.case,self.policy,p)['decision'],'ask')
        self.policy['auto_allow']=False
        self.assertEqual(gate.decide(self.case,self.policy,{'allow':1.,'ask':0.,'deny':0.})['decision'],'ask')

    def test_low_risk_and_binding(self):
        p={'allow':1.,'ask':0.,'deny':0.}
        a=gate.decide(self.case,self.policy,p);self.assertEqual(a['decision'],'allow')
        self.case['tool']['arguments']['path']='different'
        b=gate.decide(self.case,self.policy,p);self.assertNotEqual(a['binding_sha256'],b['binding_sha256'])

    def test_predictor_exception_abstains(self):
        def broken(_):raise RuntimeError('offline')
        self.assertEqual(gate.assess(self.case,self.policy,broken)['decision'],'ask')


class MetricTests(unittest.TestCase):
    def test_missing_unsafe_calibration_disables_allow(self):
        self.assertGreater(metrics.choose_threshold([[1,0,0]],[0]),1)

    def test_error_denominators_and_uncertainty(self):
        r=metrics.report([[1,0,0],[1,0,0],[0,0,1]],[0,1,2],.99)
        self.assertEqual(r['unsafe_examples'],2)
        self.assertEqual(r['unsafe_auto_allow_rate'],.5)
        r=metrics.report([[1,0,0],[0,1,0]],[0,1],.99)
        self.assertGreater(r['zero_failure_95pct_upper_bound'],0)

    def test_softmax_temperature_and_invalid_logits(self):
        self.assertAlmostEqual(sum(metrics.softmax([1,2,3])),1.)
        self.assertLess(max(metrics.softmax([1,2,3],2)),max(metrics.softmax([1,2,3],1)))
        with self.assertRaises(ValueError):metrics.softmax([float('nan'),0,0])


class ManifestTests(unittest.TestCase):
    def test_manifest_integrity_and_split_verification(self):
        import hashlib
        from small_auto_mode.training import verified_splits
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest={'allowed_sources':['human'],'splits':{}}
            for n,name in enumerate(('train','calibration','test')):
                rows=[row(n*3+i,label) for i,label in enumerate(dataset.LABELS)]
                payload=''.join(json.dumps(r)+'\n' for r in rows)
                (root/(name+'.jsonl')).write_text(payload)
                manifest['splits'][name]={'sha256':hashlib.sha256(payload.encode()).hexdigest()}
            (root/'manifest.json').write_text(json.dumps(manifest))
            splits,_=verified_splits(root);self.assertEqual(len(splits['train']),3)
            with (root/'test.jsonl').open('a') as f:f.write('\n')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verified_splits(root)

    def test_advisor_declaration_is_bounded_and_does_not_call_service(self):
        from small_auto_mode.advisor import advisor_tool
        self.assertEqual(advisor_tool('supported-model')['max_uses'],1)
        with self.assertRaises(ValueError):advisor_tool('supported-model',max_tokens=1)


if __name__=='__main__':unittest.main()
