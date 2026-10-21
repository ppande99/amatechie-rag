---
groups: sre, platform
---
# High CPU alert on ECS services

The alert fires when average CPU stays above 85 percent for ten minutes. First check for a recent
deploy, then look at request volume. If traffic is normal, scale the service out by two tasks and
open an incident if CPU does not drop within fifteen minutes.
