"""Fail-closed deployment checks; not additional independent policy tasks."""
import copy
import unittest
from src.deployment_contract import verify_literal_snapshot


class Contract(unittest.TestCase):
    def setUp(self):
        self.task = dict(principal=dict(username='reader', clientid='reader'), filters=['site/#'])
        self.policy = [dict(kind='subscribeLiteral', topic='site/#', allow=True, priority=1),
                       dict(kind='publishClientReceive', topic='site/public/#', allow=True, priority=1)]
        self.cfg = dict(defaultACLAccess=dict(subscribe=False, publishClientReceive=False), groups=[],
                        clients=[dict(username='reader', clientid='reader', roles=[dict(rolename='reader', priority=1)])],
                        roles=[dict(rolename='reader', acls=[dict(acltype=r['kind'], **{k:r[k] for k in ['topic','allow','priority']}) for r in self.policy])])

    def test_valid(self):
        verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_extra_role(self):
        self.cfg['clients'][0]['roles'].append(dict(rolename='extra', priority=2))
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_identity_mismatch(self):
        self.cfg['clients'][0]['clientid']='other'
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_shared_input(self):
        self.task['filters']=['$share/g/site/#']
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_additional_literal_grant(self):
        self.policy.append(dict(kind='subscribeLiteral', topic='elsewhere/#', allow=True, priority=2))
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_tied_priority(self):
        self.policy.append(dict(kind='publishClientReceive', topic='site/private/#', allow=False, priority=1))
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_changed_export(self):
        self.cfg['roles'][0]['acls'][1]['allow']=False
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_permissive_default(self):
        self.cfg['defaultACLAccess']['publishClientReceive']=True
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)

    def test_group(self):
        self.cfg['groups']=[dict(groupname='extra')]
        with self.assertRaises(ValueError): verify_literal_snapshot(self.cfg, self.policy, self.task)
