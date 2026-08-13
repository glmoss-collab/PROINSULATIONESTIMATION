# Repeat a PDF takeoff (same task as Gwinnett MOB)

You do **not** need Gmail or Dropbox. You need a machine with this repo, two PDFs, and the takeoff tools.

## What “this task” is

1. Upload **mechanical drawings** + **specs**.
2. Inventory pages, find **230700 / HVAC Insulation**, pull size tags.
3. Take off **wrap** (shafts, risers, core, roof) with  
   `SF = 2 × (W + H + 2t) / 12 × LF`.
4. Apply GI scope (wrap yes, liner/flex/exhaust no unless noted).
5. Price from the pricebook. Write a bid you can compare to a human number.

Gwinnett example: `estimates/gwinnett_mob/`.

---

## Option A — Laptop (fastest to own)

```bash
git clone <this-repo>
cd PROINSULATIONESTIMATION
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-takeoff.txt

scripts/new_takeoff_job.sh my-job
# copy drawings.pdf and specs.pdf into estimates/my-job/input/

python3 scripts/inventory_mech_pdfs.py \
  --drawings estimates/my-job/input/drawings.pdf \
  --specs estimates/my-job/input/specs.pdf \
  --out estimates/my-job/inventory
```

Then take off from `estimates/my-job/inventory/` (page list, `spec_insulation.txt`, size callouts) plus the PDFs. Copy `estimates/gwinnett_mob/calculate_gwinnett_takeoff.py` as a starting calculator and **replace the job-specific sizes and LF**. Do not reuse Gwinnett lengths on another building.

Optional full UI (not required for takeoff):

```bash
pip install -r requirements.txt
streamlit run guaranteed_insulation_app.py
```

That app still does **not** replace schedule/riser takeoff. Use it after you have a measurement table.

---

## Option B — Cursor on this repo (what we just did)

1. Open this repository in Cursor.
2. Start a new agent chat.
3. Attach the two PDFs (drawings + specs).
4. Paste a prompt like:

```
New takeoff job. PDFs attached: mechanical drawings and specs.

1. Run: python3 scripts/new_takeoff_job.sh <job-slug>
2. Copy or point at the attached PDFs.
3. Run scripts/inventory_mech_pdfs.py into estimates/<job-slug>/inventory
4. Follow TAKEOFF_ACCURACY.md and estimates/REPEAT_TAKEOFF.md
5. Take off GI wrap + HVAC piping. Include risers.
6. Use SF = 2*(W+H+2t)/12*LF for rectangular duct. Do not use first-number-as-diameter.
7. Price from pricebook_sample.json only. Fail if a key is missing.
8. Write estimates/<job-slug>/BID.txt and takeoff.json
```

5. Review the bid before you send it.

Cloud agents on this repo should install `requirements-takeoff.txt` via `.cursor/environment.json` so they do not start without PyMuPDF.

---

## Option C — Cursor Cloud environment (same setup every agent)

This repo now has `.cursor/environment.json`:

```json
{ "install": "pip3 install --user -r requirements-takeoff.txt" }
```

To make every new Cloud Agent boot with those packages already installed:

1. Open [Cloud Agents environments](https://cursor.com/dashboard/cloud-agents/environments).
2. Create or select an environment for `glmoss-collab/proinsulationestimation`.
3. Point it at this repo (so it picks up `.cursor/environment.json`).
4. Start a new agent **from that environment**, attach the two PDFs, use the prompt in Option B.

This run had **no linked environment**, which is why `pymupdf` had to be installed mid-job. Linking the environment avoids that.

Do not put API keys in `environment.json`. Pricebook stays in the repo (`pricebook_sample.json`) or a local file you pass in.

---

## Every job folder

```
estimates/<job-slug>/
  input/drawings.pdf      # not committed (*.pdf is gitignored)
  input/specs.pdf
  inventory/              # from inventory_mech_pdfs.py
  takeoff.json
  BID.txt
  README.md
```

Create it with `scripts/new_takeoff_job.sh <job-slug>`.

---

## Checklist before you trust the number

Same as `TAKEOFF_ACCURACY.md`:

- [ ] Drawing index vs files (all M sheets present)
- [ ] 230700 (or 23 07 13/16/19) extracted
- [ ] Per-sheet scale (not one scale for the whole PDF)
- [ ] Risers use floor-to-floor from the elevation/riser sheet
- [ ] Liner / flex / exhaust excluded unless the spec says wrap them
- [ ] Large ducts priced on **SF**, not a flat $/LF
- [ ] Missing pricebook keys flagged, not defaulted to $5
- [ ] You spot-check 2–3 long runs

---

## What you still do yourself

The inventory script does **not** measure LF. You (or the agent, with you checking) still:

- Read shaft/riser heights
- Measure roof and core runs at the sheet scale
- Decide liner vs wrap vs exterior jacket
- Decide tenant fit-out NIC vs allowance
