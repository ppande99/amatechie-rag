---
groups: sre
---
# Database failover runbook

If the primary RDS instance is unhealthy for more than five minutes, promote the read replica.
Confirm replication lag is under 30 seconds first. Update the connection string secret, restart
the API tasks, and verify the health endpoint returns 200.

Page the database owner before promoting. After failover, create a new replica and open a ticket
to review capacity.
