# GCP Operations Strategy — HVAC Estimator

**Owner:** Garrett (glmoss@guaranteedinsulation.com)
**Project:** `insulation-estimator`
**Service:** `hvac-estimator` (Cloud Run, us-central1)
**Branch this strategy targets:** `feature/google-cloud-sdk-only`
**Date:** 2026-04-28
**Scope:** Deploy/CI-CD and Monitoring/Alerting only. Cost, IAM-deep-dive, and DR are out of scope for this pass.

---

## 1. What changed in the last 7 days

There is one feature branch in flight and two new files. No new commits — both files are uncommitted on `feature/google-cloud-sdk-only`.

| Date (CDT) | Change | Notes |
|---|---|---|
| 2026-04-28 ~17:02 | Branch created | `feature/google-cloud-sdk-only` checked out from `feature/hvac-estimation-skill` |
| 2026-04-28 16:21 | `DEPLOY_SETUP.md` (new, 6.8 KB) | One-time GCP bootstrap runbook — APIs, buckets, secrets, IAM, build triggers |
| 2026-04-28 16:20 | `.gcloudignore` (new, 1.6 KB) | Excludes `.git/`, `venv/`, `*.pdf`, `*.md` (except README), `figma-plugin/`, secrets, build artifacts |

Reflog confirms no other activity in the 7-day window. The repo's `Dockerfile`, `cloudbuild.yaml`, `cloud_config.py`, and other GCP modules have not been modified since Feb 27 — they are the baseline this strategy assesses.

The intent of this branch is clear from the name and the new files: **make a clean, gcloud-first deploy path the primary operational surface.** The strategy below assumes that goal and builds around it.

---

## 2. Current state — what's actually wired up

### 2.1 Deploy / CI-CD

`cloudbuild.yaml` defines a six-step pipeline keyed off the `_ENVIRONMENT` substitution:

1. **run-tests** — `pip install` + `pytest tests/ -v`. The trailing `|| echo "Tests completed (some may be skipped without API keys)"` swallows non-zero exits, so tests do not gate the build.
2. **build-image** — `docker build` with three tags (`$COMMIT_SHA`, `${_ENVIRONMENT}`, `latest`) against `gcr.io/$PROJECT_ID/hvac-estimator`. Uses `--cache-from latest`.
3. **push-image** — `docker push --all-tags` to `gcr.io`.
4. **deploy-staging** — Always runs. Deploys `hvac-estimator-staging` with `--allow-unauthenticated`, 2 vCPU / 2 GiB, 0–5 instances, concurrency 10, 300 s timeout, env vars wired for Firestore + GCS + staging bucket, and Anthropic/Gemini keys mounted from Secret Manager.
5. **deploy-production** — Conditional on `_ENVIRONMENT=production`. Deploys `hvac-estimator` (no `-staging`) with `--no-allow-unauthenticated`, runtime SA `hvac-estimator-sa@…`, prod env vars, prod bucket.
6. **smoke-test** — Curls `${SERVICE_URL}/_stcore/health` on staging, fails the build on non-200.

`Dockerfile` is a clean two-stage Python 3.10-slim image: builder produces wheels, runtime installs them, drops to non-root `appuser`, exposes `$PORT`, and runs `agent_estimation_app.py` via `streamlit run`. Includes a `HEALTHCHECK` against `/_stcore/health`.

`cloud_config.py` auto-detects environment from `GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT`, picks `Firestore` cache + `GCS` storage in GCP, falls back to `FileCache` + `LocalStorage` locally, and lazily wires `google.cloud.logging` if importable.

### 2.2 Monitoring / observability

| Capability | Status | Source |
|---|---|---|
| Structured logs to Cloud Logging | **Yes** (when `is_gcp()`) | `cloud_config.py:166-175` calls `google.cloud.logging.Client().setup_logging()` |
| `google-cloud-logging` SDK | Installed | `requirements.txt:66` |
| `google-cloud-monitoring` SDK | **Commented out** | `requirements.txt:69` |
| Logger usage across modules | 136 calls across 12 modules | `utils_*.py`, `claude_*.py`, `cloud_config.py`, etc. |
| Container healthcheck | Yes | `Dockerfile` HEALTHCHECK `/_stcore/health` every 30 s |
| Build-time smoke test | Yes (staging only) | `cloudbuild.yaml` step 6 |
| Continuous uptime check | **No** | Not defined anywhere |
| Alert policies | **No** | Not defined anywhere |
| Dashboards | **No** | Not defined anywhere |
| Log-based metrics | **No** | Not defined anywhere |
| Error Reporting integration | **No** | `google-cloud-error-reporting` not in requirements |
| Custom metrics (API spend, cache hit rate) | **In-process only** | `utils_tracking.APIUsageTracker` does not export to Cloud Monitoring |
| Notification channels | **No** | Not defined anywhere |

Bottom line: logs flow to Cloud Logging once the service runs, but there is no alerting, no dashboard, and no continuous uptime check. Failures will only be noticed when someone looks.

---

## 3. Gaps that matter

The list below is filtered to things that will bite operationally, not theoretical best practices.

### Deploy / CI-CD gaps

1. **Tests don't gate the build.** Step 1's `|| echo` swallows pytest failures. A red test never blocks a deploy.
2. **`gcr.io` is on Google's deprecation path.** Container Registry is being shut down; new registries should be Artifact Registry. `DEPLOY_SETUP.md` already calls this out as a future fix.
3. **No image vulnerability scanning.** Artifact Registry can scan automatically; gcr.io can't.
4. **Staging deploy is `--allow-unauthenticated`.** Fine for now, but it means a public URL with API costs attached. At minimum it should be IAM-locked once you're past the demo phase.
5. **Production deploy has no smoke test.** Step 6 only hits staging. A bad prod deploy can sit broken until a user notices.
6. **No traffic management.** `gcloud run deploy` defaults to 100 % traffic to the new revision instantly. No `--no-traffic` + canary + promote.
7. **No rollback automation.** If smoke-test fails after deploy-staging, the build fails but the bad revision is already serving 100 %.
8. **Branch / trigger strategy is unspecified.** `DEPLOY_SETUP.md` assumes `^main$` triggers a deploy. The current working branch is `feature/google-cloud-sdk-only`. The branching model needs to be decided before the trigger is created (see §5.2).
9. **`cloud-sdk` builder image is unpinned.** Step 4 uses `gcr.io/google.com/cloudsdktool/cloud-sdk` with no tag — implicit `:latest`, non-reproducible.
10. **No notification on build failure.** Cloud Build can post to Pub/Sub → Slack/email; nothing is wired up.

### Monitoring / alerting gaps

1. **No alerts on errors.** Cloud Logging is collecting logs but nothing pages on a spike of `ERROR` lines.
2. **No alerts on 5xx rate.** Cloud Run exposes `request_count` filtered by `response_code_class=5xx`; not being watched.
3. **No alerts on latency.** P95 latency on the `/agent` request path is the user-facing SLO and is invisible.
4. **No uptime check.** A continuous external probe of the staging and prod URLs with regional fan-out is the cheapest "is the service alive" signal and isn't set up.
5. **No alert on Anthropic API spend.** `APIUsageTracker` runs in-process; spend per Cloud Run revision evaporates when the instance recycles. No Firestore/BQ aggregation, no budget alert tied to it.
6. **No alert on Cloud Run quota or billing budget.** A runaway loop or a leaked unauthenticated URL can rack up real money before anyone notices.
7. **No Error Reporting.** Stack traces are in logs but not aggregated/deduped.
8. **No log-based metric for tool failures.** The agent has 7 tools; a sudden spike of failures from one of them should be paged, not buried.
9. **No notification channel.** Even if alerts existed, there's nowhere for them to go.

---

## 4. Target state

### 4.1 Deploy / CI-CD target

```
git push origin feature/* ──► PR opened
                              └─► Cloud Build PR trigger:
                                  test + build + push to AR + deploy to PR-preview Cloud Run
                                  (auto-cleanup on PR close)

git push origin main ────────► Cloud Build main trigger:
                                  test (gating)
                                  → build + push to Artifact Registry (vuln scan on)
                                  → deploy STAGING with --no-traffic
                                  → smoke-test new revision
                                  → promote to 100 % traffic
                                  → notify Slack/email on success or failure

manual approval ─────────────► Cloud Build prod trigger (or `gcloud builds submit` w/ _ENVIRONMENT=production):
                                  re-uses image from staging build by digest
                                  → deploy PROD with --no-traffic
                                  → smoke-test
                                  → 10% canary for 5 min
                                  → 100% if error rate < threshold
                                  → rollback automatically otherwise
```

Concrete asks:

- **Migrate `gcr.io/$PROJECT_ID/hvac-estimator` → `us-central1-docker.pkg.dev/$PROJECT_ID/hvac-estimator/hvac-estimator`.** Pre-create the AR repo with `--repository-format=docker`. Enable on-push vulnerability scanning.
- **Make tests gate the build.** Drop the `|| echo` in step 1.
- **Pin the cloud-sdk image** to a specific tag (e.g. `gcr.io/google.com/cloudsdktool/cloud-sdk:466.0.0-slim`).
- **Add `--no-traffic` to the staging deploy**, then promote with `gcloud run services update-traffic --to-revisions=NEW=100` after smoke-test passes.
- **Smoke-test prod after prod deploy.** Same pattern, against the prod URL.
- **Add a Pub/Sub-based build notification** (`gcloud pubsub topics create cloud-builds` is automatic) and route to a Slack webhook or email via Cloud Function. Two lines of YAML in `cloudbuild.yaml` are not needed — the Pub/Sub topic is auto-published; only the consumer needs to be built.
- **Decide branching model.** Recommended: `main` is deployable, all work happens on `feature/*` branches, PR triggers run preview deploys, merge-to-main triggers staging, manual gcloud invocation triggers prod. See §5.2 for the migration path from the current `feature/google-cloud-sdk-only` branch.

### 4.2 Monitoring / alerting target

The minimum viable alerting set for a Cloud Run + Streamlit + Anthropic stack:

| Signal | Threshold | Notification | Why |
|---|---|---|---|
| Uptime check on staging URL | Failed > 2 of 3 regions for 5 min | Email | Cheapest "is it alive" probe |
| Uptime check on prod URL | Failed > 2 of 3 regions for 5 min | Email + SMS | Customer-facing |
| Cloud Run 5xx rate | > 5 % of requests over 5 min, prod | Email + SMS | User experience |
| Cloud Run P95 request latency | > 30 s over 10 min, prod | Email | Streamlit + agent calls are slow but not pathological |
| `severity>=ERROR` log count | > 20 in 5 min, prod | Email | Catches stack-trace spikes |
| Cloud Run instance count | > 8 of 10 max for 15 min | Email | Capacity warning before throttling |
| Billing budget on the project | 50 %, 80 %, 100 % of monthly cap | Email | Backstop against runaway spend |
| Build failures (Cloud Build) | Any failure on `main` | Slack/email | Deploy hygiene |

**Dashboard (one panel per row):** request count, 5xx rate, P95 latency, instance count, container CPU, container memory, log error rate, build success rate, Anthropic spend (once exported).

**Custom metrics worth exporting:**

- `custom.googleapis.com/hvac/agent_tool_invocations` labeled by tool name + outcome — one log-based metric is enough.
- `custom.googleapis.com/hvac/anthropic_tokens` — emit from `APIUsageTracker` to Cloud Monitoring on each request. This requires uncommenting `google-cloud-monitoring>=2.15.0` in `requirements.txt` and a small writer in `utils_tracking.py`.
- `custom.googleapis.com/hvac/cache_hit_rate` — log-based metric off `utils_cache.py` log lines is sufficient; no SDK change needed.

**Error Reporting:** add `google-cloud-error-reporting>=1.9.0` to `requirements.txt` and `error_reporting.Client().setup_logging()` in `cloud_config.py`. Stack traces in logs auto-aggregate.

---

## 5. Action plan, ordered

### Phase 1 — close the loop on the in-flight branch (this week)

1. **Commit the new files.** `git add .gcloudignore DEPLOY_SETUP.md && git commit -m "Add gcloud-first deploy setup and gcloudignore"`. They're useful and should not float as untracked work.
2. **Walk DEPLOY_SETUP.md sections 1–6** against a fresh `gcloud` session and confirm each step actually runs in your environment. The runbook reads correctly but has not been executed end-to-end on this branch.
3. **Do a manual `gcloud builds submit --config cloudbuild.yaml --substitutions=_ENVIRONMENT=staging`** to validate the existing pipeline before adding any new logic. Confirm staging URL responds.
4. **Drop `|| echo` from cloudbuild.yaml step 1** so failing tests fail the build. One-line change.
5. **Pin the cloud-sdk builder image** in steps 4, 5, 6.

### Phase 2 — registry + branch hygiene (next week)

6. **Migrate to Artifact Registry.**
   ```bash
   gcloud artifacts repositories create hvac-estimator \
     --repository-format=docker --location=us-central1
   ```
   Replace `gcr.io/$PROJECT_ID/${_SERVICE_NAME}` with `us-central1-docker.pkg.dev/$PROJECT_ID/hvac-estimator/${_SERVICE_NAME}` in `cloudbuild.yaml` (10 occurrences across the build, push, deploy, and `images:` blocks — `grep -n 'gcr.io/\$PROJECT_ID'` to enumerate). Enable vulnerability scanning in the AR repo settings.
7. **Decide branching model.** Recommended path: merge `feature/google-cloud-sdk-only` into `main`, retire `master`, set `main` as the trigger branch. If you want to keep `master`, change DEPLOY_SETUP.md and the trigger to `^master$` — but `main` is the GitHub/most-everyone default and worth standardizing on.
8. **Create the build trigger** per DEPLOY_SETUP.md step 5. Pick Cloud Source Repos OR GitHub, not both.

### Phase 3 — safe deploys (week 3)

9. **Add `--no-traffic` to staging and prod deploys**, then promote after smoke-test:
   ```yaml
   - '--no-traffic'  # added to gcloud run deploy args
   # then:
   - id: promote-staging
     entrypoint: gcloud
     args: ['run', 'services', 'update-traffic',
            '${_SERVICE_NAME}-staging', '--to-latest',
            '--region', '${_REGION}']
     waitFor: ['smoke-test']
   ```
10. **Add a prod smoke-test step** mirroring the staging one, gated on `_ENVIRONMENT=production`.
11. **Add a Cloud Build → Slack notifier.** Cloud Run a tiny function on the `cloud-builds` Pub/Sub topic. There's a Google sample for this — copy it.

### Phase 4 — monitoring baseline (week 3–4)

12. **Create two uptime checks** (staging + prod) in Cloud Monitoring console, 60-s frequency, 3 regions.
13. **Create the alert policies in §4.2** as Terraform or `gcloud monitoring policies create` commands. Commit the YAML to a new `monitoring/` directory in the repo.
14. **Set up notification channels.** At minimum: your email. Better: an alert email alias + SMS for prod-only critical.
15. **Set a billing budget** at the project level: monthly cap with 50/80/100 % alerts. Two-minute task in console.
16. **Add Error Reporting.** `pip install google-cloud-error-reporting`, add `error_reporting.Client().setup_logging()` to `cloud_config.py:_setup_logging()` next to the existing Cloud Logging setup. Add `roles/errorreporting.writer` to the runtime SA.

### Phase 5 — custom metrics (week 4+)

17. **Uncomment `google-cloud-monitoring`** in `requirements.txt`.
18. **Emit `anthropic_tokens` and `agent_tool_invocations` metrics** from `utils_tracking.py` and `claude_agent_tools.py`. Add `roles/monitoring.metricWriter` to the runtime SA.
19. **Build the dashboard** in Cloud Monitoring with the panels listed in §4.2.

---

## 6. Risks and watch-items

- **The `|| echo` in cloudbuild.yaml step 1 is doing real work.** Some tests genuinely require API keys and will be skipped via pytest markers; some might fail because the test fixtures aren't set up. Removing the swallow will surface real failures — budget half a day to triage and fix or properly skip those.
- **Migrating `gcr.io` → Artifact Registry** changes IAM. The Cloud Build SA already has `roles/storage.admin`; for AR you also need `roles/artifactregistry.writer` (already in DEPLOY_SETUP.md step 4). Verify before flipping the YAML.
- **`--no-traffic` + promote** on Streamlit specifically: Streamlit holds long-lived sessions over WebSocket. Traffic split mid-session can drop a session. For a deploy-during-business-hours scenario, prefer scheduled deploys or accept the disconnect.
- **Branch `feature/google-cloud-sdk-only` is untested in CI** because no trigger exists yet. The first manual `gcloud builds submit` from this branch is the integration test for the entire CI/CD setup.
- **`master` and `main` divergence** is the single biggest source of confusion in the next two weeks. Pick one.

---

## 7. Out-of-scope notes (for a future strategy doc)

- Cost control beyond a billing budget — Anthropic spend optimization, prompt caching, instance right-sizing
- IAM hardening — least-privilege review of `roles/storage.objectAdmin` and `roles/datastore.user` on the runtime SA
- Disaster recovery — Firestore export schedule, GCS object versioning, runbook for restoring prod from staging
- Multi-region / failover — currently single-region us-central1
- VPC + private Firestore — keeping all traffic off the public internet
- Audit logging strategy — Data Access logs are off by default; turning them on costs money but is necessary for compliance work

These are real, but deferred until the deploy + monitoring baseline above is solid.

---

## Appendix A — file inventory referenced in this strategy

| File | Role | Status |
|---|---|---|
| `cloudbuild.yaml` | CI/CD pipeline | Existing, needs the changes in Phase 1–3 |
| `Dockerfile` | Container build | Existing, no changes needed |
| `cloud_config.py` | Env detection + backend selection | Existing, add Error Reporting hook in Phase 4 |
| `utils_tracking.py` | API spend tracking | Existing, add Cloud Monitoring writer in Phase 5 |
| `requirements.txt` | Python deps | Uncomment monitoring, add error-reporting in Phase 4–5 |
| `DEPLOY_SETUP.md` | Bootstrap runbook | New (uncommitted), commit it in Phase 1 |
| `.gcloudignore` | Build context filter | New (uncommitted), commit it in Phase 1 |
| `secrets_manager.py` | Secret Manager wrapper | Existing, no changes |
| `gcs_storage.py` | GCS abstraction | Existing, no changes |
| `firestore_cache.py` | Firestore cache | Existing, no changes |
| `monitoring/` (new) | Alert policies + dashboards as code | To be created in Phase 4 |
