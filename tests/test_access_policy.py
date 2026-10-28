# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Application access policy: fake native receipts only, no host actions."""
import unittest
import access_policy as policy


class AccessPolicyTests(unittest.TestCase):
    def test_full_access_keeps_important_actions_and_unknown_targets_behind_approval(self):
        prefs={'com.example.notes':'full'}
        self.assertEqual(policy.decide(prefs,{'bundleID':'com.example.notes','risky':False,'secure':False},'type'),'allow')
        for field in ('risky','secure'):
            self.assertEqual(policy.decide(prefs,{'bundleID':'com.example.notes',field:True},'type'),'ask')
        self.assertEqual(policy.decide(prefs,{},'type'),'ask')

    def test_read_only_and_denied_are_restrictions(self):
        self.assertEqual(policy.decide({'a':'denied'},{'bundleID':'a'},'see'),'deny')
        self.assertEqual(policy.decide({'a':'read'},{'bundleID':'a'},'see'),'allow')
        self.assertEqual(policy.decide({'a':'read'},{'bundleID':'a'},'type'),'deny')
        self.assertEqual(policy.decide({'a':'ask'},{'bundleID':'a'},'type'),'ask')

    def test_invalid_policy_never_grants_access(self):
        self.assertEqual(policy.decide({'a':'unknown'},{'bundleID':'a'},'click'),'ask')
        self.assertEqual(policy.decide([],{'bundleID':'a'},'click'),'ask')

    def test_shell_operators_and_substitution_cannot_inherit_app_full_access(self):
        import kira
        from unittest.mock import patch
        commands=[f'{kira.ME} --hands click Foo;echo harmless',f'{kira.ME} --hands type Field "$(echo harmless)"',f'{kira.ME} --hands click Foo>output']
        def preflight(args,authorize,timeout):authorize({'args':args,'bundleID':'a','risky':False,'secure':False})
        with patch.object(kira,'pref',side_effect=lambda k,d:{'a':'full'} if k=='appAccess' else d),patch.object(kira,'hands_action',side_effect=preflight):
            for command in commands:
                with self.subTest(command=command):self.assertFalse(kira.permitted_app_command(command))

    def test_menu_execution_is_never_used_as_an_authorization_preflight(self):
        import kira
        from unittest.mock import patch
        with patch.object(kira,'hands_action') as action:
            self.assertFalse(kira.permitted_app_command(f'{kira.ME} --hands menu Notes Delete'))
            action.assert_not_called()

    def test_full_access_cannot_silently_submit_with_enter_or_multiline_typing(self):
        prefs={'a':'full'}
        for verb,args in [('press',['press','return']),('type',['type','Message','hello\n']),('type-after',['type-after','Message','hello\r']),('drag',['drag','file','folder'])]:
            with self.subTest(verb=verb):
                receipt={'bundleID':'a','risky':False,'secure':False,'args':args}
                self.assertEqual(policy.decide(prefs,receipt,verb),'ask')
