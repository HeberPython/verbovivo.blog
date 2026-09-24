# Recovery of four truncated reflections

Scope: a-boa-obra, deus-da-presenca, construtores-de-altares,
o-coracao-que-confessa. No other article or lesson may be removed.

Pre-change backup: GitHub run 36050702792, downloaded locally to
`automation/_backups/pre-four-text-recovery-20260924`.

Manual command `recover-four-texts` uses the same concurrency group as the
editorial worker. The temporary admin-authenticated PHP helper verifies the
physical catalog, creates and verifies a private backup outside public_html
(`_text_recovery_20260924`), removes only the four pages and their old approval
tokens, and updates only home/archive/feed/sitemap. Images remain byte-identical.
All unrelated files in the inventory must remain unchanged. A failed transaction
restores the affected files from that backup.

The private state retains complete originals and generated replacement drafts.
Rerunning the command reuses those drafts and skips already notified entries;
it does not regenerate images or publish. There is a small SMTP acknowledgement
window in which a repeated notification may be sent, but it uses the same draft
and review token. If text generation is blocked, originals remain in this private
queue and the workflow fails visibly. Resume the same manual command after fixing
the provider issue. This recovery queue is not the ordinary unread-email queue.

For rollback, first inventory current production and take a new backup. Restore
only the four original pages/drafts from the private backup, then reconcile
indexes with the current physical catalog. Do not blindly restore old indexes
if new articles have been published since recovery. Never expose state.json or
the backed-up draft tokens through the public site.
