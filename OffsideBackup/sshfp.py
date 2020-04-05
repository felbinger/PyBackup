#!/usr/bin/env python
import hashlib
import dns.resolver
import dns.flags

from paramiko.client import MissingHostKeyPolicy
from paramiko.common import DEBUG

class DnssecPolicy(MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        sshfp_expect = hashlib.sha1(key.asbytes()).hexdigest()
        ans = dns.resolver.query(hostname, 'SSHFP')
        if not ans.response.flags & dns.flags.DO:
            raise AssertionError('Answer is not DNSSEC signed')
        for answer in ans.response.answer:
            for item in answer.items:
                if sshfp_expect in item.to_text():
                    client._log(DEBUG, 'Found %s in SSHFP for host %s' %
                                (key.get_name(), hostname))
                    return
        raise AssertionError('SSHFP not published in DNS')