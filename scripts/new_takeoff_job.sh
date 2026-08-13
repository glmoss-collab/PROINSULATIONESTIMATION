#!/usr/bin/env bash
# Create a job folder for the next mechanical PDF takeoff.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/new_takeoff_job.sh <job-slug>"
  echo "Example: scripts/new_takeoff_job.sh lawrenceville-mob"
  exit 1
fi

slug="$1"
root="$(cd "$(dirname "$0")/.." && pwd)"
job="$root/estimates/$slug"

mkdir -p "$job/input" "$job/inventory"
cat > "$job/README.md" <<EOF
# $slug

1. Put PDFs in \`input/\` (gitignores \`*.pdf\`):
   - \`input/drawings.pdf\`
   - \`input/specs.pdf\`
2. Inventory:
   \`\`\`bash
   python3 scripts/inventory_mech_pdfs.py \\
     --drawings estimates/$slug/input/drawings.pdf \\
     --specs estimates/$slug/input/specs.pdf \\
     --out estimates/$slug/inventory
   \`\`\`
3. Take off from \`inventory/\` + the PDFs. Use rectangular SF:
   \`2 * (W + H + 2t) / 12 * LF\`
4. Price from \`pricebook_sample.json\` (or your live book). No invented keys.
5. Write the bid to \`GWINNETT_MOB_BID.txt\`-style text in this folder.

See \`estimates/REPEAT_TAKEOFF.md\`.
EOF

echo "Created $job"
echo "Copy drawings.pdf and specs.pdf into $job/input/"
