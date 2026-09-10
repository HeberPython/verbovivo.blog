# Hostinger scheduler - NOT DEPLOYED

Prepared on 2026-09-10. User confirmed no existing Hostinger cron jobs.
The browser control connection is unavailable. Do not claim activation.

This CLI-only dispatcher preserves the Python editorial workflow. It does not
implement another publisher. Place it OUTSIDE public_html in a private directory;
keep scheduler-config.json and scheduler.lock in that directory with restrictive
permissions. Do not store tokens in this repository, screenshots, logs, artifacts,
cron command lines or public URLs.

Required credential: dedicated fine-grained GitHub PAT, resource owner HeberPython,
only verbovivo.blog selected, repository Actions read/write, automatic Metadata read.
Actions permission is repository-wide, not restricted to this one workflow. A
compromised token can manage Actions in this repository. Record its expiration and
arrange renewal. Never reuse the broad GitHub CLI OAuth credential.

Private configuration keys: github_token (secret), enabled (boolean, false until
validated). Run --check to test read access without publishing; this does NOT prove
write permission. No credential or private config is bundled here.

Activation checklist:

1. Confirm private absolute server directory, PHP CLI and cURL availability.
2. Back up workflow configuration and inventory published articles and lessons.
3. Install the dispatcher and private configuration through an authenticated,
   encrypted channel; verify access restrictions and PHP syntax.
4. Test --check and a controlled workflow dispatch, with a content backup first.
5. Preserve the shared editorial workflow concurrency group. Remove ONLY the
   GitHub schedule trigger when switching to Hostinger; keep manual dispatch.
6. Configure Hostinger cron every 15 minutes, all hours/days; the script enforces
   07:00-22:59 America/Sao_Paulo independently of the panel timezone.
7. Verify at least two consecutive scheduled dispatches and real mailbox scan
   timestamps, then compare the publication inventory. Do not equate API acceptance
   with a successful scan or SMTP acceptance with inbox delivery.
8. Record rollback instructions: disable new cron, restore original GitHub schedule.

Hostinger controls dispatch timing, but GitHub runner queues and long executions
can still delay scans. This is not a hard real-time 15-minute guarantee. A running
or queued workflow is not duplicated. No loops, self-dispatch chains or idle runners.

Source: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
