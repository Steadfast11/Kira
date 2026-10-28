# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Portable app policies; important or unidentified changes never inherit a broad allowance."""
MODES=('denied','read','ask','full')
READ_ACTIONS=frozenset(('see','wait','scroll','scroll-to'))


def decide(policies,receipt,verb):
    policies=policies if isinstance(policies,dict) else {}
    receipt=receipt if isinstance(receipt,dict) else {}
    identifier=receipt.get('bundleID')
    mode=policies.get(identifier,'ask') if isinstance(identifier,str) and identifier else 'ask'
    if mode=='denied':return 'deny'
    if mode=='read':return 'allow' if verb in READ_ACTIONS else 'deny'
    if verb in READ_ACTIONS:return 'allow'
    args=receipt.get('args',[])
    if mode=='full' and (verb in ('press','drag') or verb in ('type','type-after') and (not isinstance(args,list) or any('\n' in str(value) or '\r' in str(value) for value in args))):return 'ask'
    if mode=='full' and identifier and receipt.get('risky') is False and receipt.get('secure') is False:return 'allow'
    return 'ask'
