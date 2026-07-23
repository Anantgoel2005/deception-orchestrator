# Five-minute product demo

1. Sign in to the protected Analyst Console and point out the deployment-mode badge on the dashboard.
2. Open **Demo Lab** and run the credential-to-exfiltration scenario. Explain that all addresses are reserved TEST-NET data and no external system is touched.
3. Follow the automatically opened investigation. Highlight the ordered login, command, exploit, and canary events plus their MITRE tags and risk scores.
4. Open **Alerts**, acknowledge the high-confidence alert, read the recommended action, and resolve it.
5. Open **Canaries**, generate a URL beacon, copy its callback URL, and fetch it once. Refresh Alerts to show the one-time critical callback signal.
6. Close by showing the deployment guide: hosted control planes receive dashboard traffic and canary callbacks, while decoys stay isolated to a local lab.

For portfolio screenshots, capture the dashboard after the scenario, the investigation timeline, the alert triage view, and the canary list with a tripped URL token. Do not include real public IP addresses, API keys, or passwords.
