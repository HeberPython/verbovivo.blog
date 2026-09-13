# Hostinger scheduler - PROCESSING ACTIVE

Activated on 2026-09-13 by run 34768947871, after user authorization and backup.
Hostinger cron was confirmed by the user and repeated workflow_dispatch runs.
The private configuration now uses command=all, enabled=true. The old GitHub
schedule trigger was removed; manual workflow_dispatch and concurrency remain.
Cron: */15 * * * * (script enforces 07:00-22:59 America/Sao_Paulo).
Activation passed 26 editorial tests and 8 PHP integration/security/rollback tests.
All 78 checked public files were byte-identical before and after the mode change.
Independent HTTP checks: 62 articles and 11 lessons unchanged and accessible;
home=4, archive/feed/sitemap=62, four recent article images accessible.
Two consecutive post-activation automatic processing runs passed:
- 34769524537: dispatched 2026-09-13 13:45:13 BRT; publicar checked 13:45:59,
  artigo checked 13:46:01; both processing steps succeeded, both inboxes unread=0.
- 34770258180: dispatched 2026-09-13 14:00:17 BRT; publicar checked 14:01:08,
  artigo checked 14:01:09; both processing steps succeeded, both inboxes unread=0.
Dispatch interval was 15m04s; artigo scan log interval was about 15m08s.
Manual all-mode smoke test 34769169141 also passed before these automatic runs.
Read-only audit 34769606305: home=4, archive/feed/sitemap/physical articles=62,
no orphans, both inboxes unread=0. Six existing pending-review drafts unchanged.
Final independent HTTP comparison after the second automatic run: all 73 article
and lesson pages byte-identical to the pre-change backup; recent images HTTP 200.
These empty-inbox runs validate dispatch and mailbox access, not new-message SMTP
delivery or an absolute maximum processing time for image generation.

Initially installed in audit mode on 2026-09-10 by GitHub run 34502039757.
Verified script: /home/u454442761/domains/verbovivo.blog/_verbovivo_scheduler/dispatch-editorial.php
Private directory is outside public_html. Config permissions: 0600.
Installation started in email-audit mode; activation changed ONLY command to all.
Local backup/result: automation/_backups/scheduler-install-34502039757/
Temporary bootstrap was removed; public index bytes and catalog lists unchanged.
FTPS inspection timed out. Existing FTP delivered only token-free bootstrap code;
the new credential traveled exclusively over authenticated HTTPS without redirects.
Installation authentication, private path, permissions and no-overwrite tests passed.

## Backups and rollback

- Pre-change repository: f82e5d5; local verified Git bundle:
  automation/_backups/pre-scheduler-activation-20260913.bundle
- Published content backup run: 34768477816; local copy:
  automation/_backups/pre-scheduler-activation-site-34768477816/
- Activation inventories/results: run 34768947871; local copy:
  automation/_backups/scheduler-activation-34768947871/
- Private config and dispatcher backup remains outside public_html, under
  _verbovivo_scheduler/before-mode-20260913-163612-555a6004b79f/.
  Config backup contains a secret: never download it into artifacts or the repo.
- To pause processing safely, run activate-scheduler.yml with command=email-audit.
  This uses the same authenticated atomic update and creates a fresh private backup.
- To restore the previous scheduling arrangement, switch to email-audit first,
  then restore ONLY the editorial schedule trigger and schedule step conditions
  from f82e5d5. Do not reset the repository or deploy old site files.
- Scheduler activation scripts do not modify or deploy public content. Their
  temporary authenticated PHP bootstrap is deleted immediately after the update.

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

Private configuration keys: github_token (secret), enabled (boolean), command
(email-audit for validation; all only after scheduler validation). Run --check to
test read access without publishing; this does NOT prove
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
