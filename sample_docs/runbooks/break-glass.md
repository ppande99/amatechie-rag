---
groups: sre
---
# Break-glass IAM role rotation

The break-glass role is used only during incidents when SSO is unavailable.

Rotate its credentials every 90 days. Store the new secret in the vault, update the on-call
runbook, and record the rotation in the change log.

After every use, rotate immediately and file a post-incident review.
