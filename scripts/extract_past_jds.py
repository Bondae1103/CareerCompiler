"""Extract real JDs previously supplied by the user across conversation transcripts."""

import json
import re
from pathlib import Path

brain_dir = Path(r"C:\Users\Anoop\.gemini\antigravity\brain")
out_dir = Path("data/raw_jds")
out_dir.mkdir(parents=True, exist_ok=True)

jds = []

for cid_dir in sorted(brain_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
    if not cid_dir.is_dir():
        continue
    cid = cid_dir.name
    tpath = cid_dir / ".system_generated" / "logs" / "transcript.jsonl"
    if not tpath.is_file():
        continue

    with open(tpath, encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
            except Exception:
                continue

            if data.get("type") == "USER_INPUT" or data.get("source") == "USER_EXPLICIT":
                content = str(data.get("content", ""))
                m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                text = m.group(1).strip() if m else content.strip()
                low = text.lower()

                title = ""
                # Specific known company JDs
                if "ea hyderabad" in low or "electronic arts" in low:
                    title = "ea_ai_software_engineer_intern"
                elif "caterpillar" in low and ("software engineer" in low or "digital platform" in low):
                    title = "caterpillar_software_engineer_intern"
                elif "sanofi" in low and "internship" in low:
                    title = "sanofi_digital_internship"
                elif "optum" in low and ("tdp" in low or "software engineering" in low):
                    title = "optum_tdp_software_engineer"
                elif "data scientist i intern" in low:
                    title = "data_scientist_i_intern"
                elif "four work streams" in low and "product mindset" in low:
                    title = "fintech_product_analytics_intern"

                if title:
                    # Clean out conversational prefix if user said "optmize my resume for this JD:"
                    clean_text = text
                    prefix_match = re.match(
                        r"^(?:optmize my resume for this jd:|do any of my existing resumes fit this job description perfectly\.? its as a sde at [^:]+:|new jds i want to fulfil:|this a jd for a company i want to apply to:)\s*",
                        clean_text,
                        re.IGNORECASE,
                    )
                    if prefix_match:
                        clean_text = clean_text[prefix_match.end():].strip()

                    jds.append({
                        "cid": cid,
                        "step": idx,
                        "key": title,
                        "raw_text": clean_text,
                        "length": len(clean_text),
                    })

# Deduplicate by key keeping the cleanest/longest
seen = {}
for item in jds:
    k = item["key"]
    if k not in seen or item["length"] > seen[k]["length"]:
        seen[k] = item

print(f"Extracted {len(seen)} unique high-quality real JDs from past conversations:")
for i, (k, item) in enumerate(seen.items()):
    out_file = out_dir / f"{k}.txt"
    out_file.write_text(item["raw_text"], encoding="utf-8")
    print(f"  {i+1}. {k} ({item['length']} chars) -> {out_file}")
