# TLS certificate renewal

Certificates are issued by ACM and renew automatically 60 days before expiry. If renewal fails,
check that the DNS validation record still exists in Route 53. Manual renewal is never needed for
ACM certificates attached to load balancers. Imported certificates must be replaced by hand.
