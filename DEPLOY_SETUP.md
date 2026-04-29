# Deploy Setup — Insulation Estimator → Cloud Run

Project: `insulation-estimator`
Service: `hvac-estimator`
Region: `us-central1`
Runtime: Streamlit on Cloud Run, image built by Cloud Build

This is a one-time bootstrap. After it's done, every `git push google main` triggers a build + deploy automatically.

---

## 0. Prereqs (one time on your Mac)

```bash
# Install gcloud if you don't have it
brew install --cask google-cloud-sdk

# Log in and set the active project
gcloud auth login
gcloud config set project insulation-estimator
gcloud config set run/region us-central1
gcloud auth application-default login
```

---

## 1. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  sourcerepo.googleapis.com \
  iam.googleapis.com
```

---

## 2. Create the GCS bucket and Firestore database

```bash
# GCS bucket for PDF uploads (staging)
gcloud storage buckets create gs://insulation-estimator-hvac-uploads-staging \
  --location=us-central1 \
  --uniform-bucket-level-access

# Production bucket (skip if you only want staging for now)
gcloud storage buckets create gs://insulation-estimator-hvac-uploads \
  --location=us-central1 \
  --uniform-bucket-level-access

# Firestore in Native mode (one-time per project)
gcloud firestore databases create --location=us-central1
```

---

## 3. Store API keys in Secret Manager

```bash
# Anthropic
printf "sk-ant-xxxxxxxx" | gcloud secrets create anthropic-api-key \
  --replication-policy=automatic --data-file=-

# Gemini
printf "AIzaXXXXXX" | gcloud secrets create gemini-api-key \
  --replication-policy=automatic --data-file=-
```

To rotate later: `gcloud secrets versions add anthropic-api-key --data-file=-` then paste the key.

---

## 4. Service account for Cloud Run + permissions

```bash
PROJECT_ID=insulation-estimator
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Runtime service account (used by the Cloud Run service)
gcloud iam service-accounts create hvac-estimator-sa \
  --display-name="HVAC Estimator Cloud Run runtime"

SA="hvac-estimator-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Runtime perms — read secrets, R/W Firestore + GCS, write logs
for ROLE in \
  roles/secretmanager.secretAccessor \
  roles/datastore.user \
  roles/storage.objectAdmin \
  roles/logging.logWriter \
  roles/aiplatform.user; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA}" --role="$ROLE"
done

# Cloud Build service account perms — deploy to Run + read secrets
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
for ROLE in \
  roles/run.admin \
  roles/iam.serviceAccountUser \
  roles/secretmanager.secretAccessor \
  roles/storage.admin \
  roles/artifactregistry.admin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CB_SA}" --role="$ROLE"
done
```

---

## 5. Wire the repo to GCP (git push → deploy)

You have two options. Pick one.

### Option A — Cloud Source Repositories (simplest, no GitHub needed)

```bash
# From this repo's root:
gcloud source repos create insulation-estimator

# Add it as a git remote and push
git remote add google \
  https://source.developers.google.com/p/insulation-estimator/r/insulation-estimator
git push --all google
git push --tags google

# Create the build trigger — every push to main runs cloudbuild.yaml
gcloud builds triggers create cloud-source-repositories \
  --name=deploy-on-push-main \
  --repo=insulation-estimator \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=staging
```

From now on:

```bash
git add .
git commit -m "your message"
git push google main          # triggers build + deploy automatically
```

### Option B — GitHub (if your repo lives on GitHub already)

1. Console → Cloud Build → Triggers → Connect repository → GitHub → authorize.
2. Pick the repo, set branch to `^main$`, config = `cloudbuild.yaml`, add substitution `_ENVIRONMENT=staging`.
3. `git push origin main` will now build + deploy.

CLI equivalent (after the GitHub App is connected):

```bash
gcloud builds triggers create github \
  --name=deploy-on-push-main \
  --repo-owner=YOUR_GH_USER \
  --repo-name=YOUR_GH_REPO \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=staging
```

---

## 6. First manual deploy (skip the trigger, ship now)

If you want to deploy immediately without setting up a remote:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=staging
```

Then grab the URL:

```bash
gcloud run services describe hvac-estimator-staging \
  --region=us-central1 --format='value(status.url)'
```

---

## 7. Going to production

Production deploy requires the prod bucket (step 2) and uses the runtime SA + auth-required mode. Trigger it explicitly:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=production
```

Production service is `hvac-estimator` (no `-staging` suffix) and is `--no-allow-unauthenticated` — grant access:

```bash
gcloud run services add-iam-policy-binding hvac-estimator \
  --member="user:glmoss@guaranteedinsulation.com" \
  --role="roles/run.invoker" \
  --region=us-central1
```

---

## Troubleshooting


| Symptom                                    | Fix                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Build fails: "permission denied on secret" | Re-run the Cloud Build IAM bindings in step 4                                                                                                                                                                                                                                                                                               |
| `gcloud builds submit` uploads gigabytes   | `.gcloudignore` is missing or wrong — confirm `venv/`, `.git/`, `*.pdf` are listed                                                                                                                                                                                                                                                          |
| Cloud Run boots then 503s                  | Check logs: `gcloud run services logs read hvac-estimator-staging --region us-central1 --limit 100`                                                                                                                                                                                                                                         |
| Streamlit health check fails               | The Dockerfile hits `/_stcore/health` — make sure `agent_estimation_app.py` actually starts                                                                                                                                                                                                                                                 |
| `gcr.io` deprecation warning               | Cloudbuild.yaml currently pushes to `gcr.io/$PROJECT_ID`. Still works through 2026 but you can switch to Artifact Registry: replace `gcr.io/$PROJECT_ID` with `us-central1-docker.pkg.dev/$PROJECT_ID/hvac-estimator` and run `gcloud artifacts repositories create hvac-estimator --repository-format=docker --location=us-central1` first |


---

## Files this setup added

- `.gcloudignore` — keeps build uploads small and free of secrets
- `DEPLOY_SETUP.md` — this file

Files that were already in the repo and are doing the heavy lifting:

- `Dockerfile` — multi-stage Python 3.10 + Streamlit, runs on `$PORT`
- `cloudbuild.yaml` — test → build → push → deploy → smoke-test
- `requirements.txt` — pinned deps including google-cloud-* SDKs

