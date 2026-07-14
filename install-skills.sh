#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target_root=${CODEX_HOME:-"$HOME/.codex"}/skills
source_skill="$repo_root/codex-skills/airjet-product-reconstruction"
target_skill="$target_root/airjet-product-reconstruction"
source_ansys_skill="$repo_root/codex-skills/airjet-ansys-automation"
target_ansys_skill="$target_root/airjet-ansys-automation"
manifest="$repo_root/codex-skills/skills-manifest.json"
official_commit=49f948faa9258a0c61caceaf225e179651397431

mkdir -p "$target_root" "$target_skill" "$target_ansys_skill"
rsync -a --delete "$source_skill/" "$target_skill/"
rsync -a --delete "$source_ansys_skill/" "$target_ansys_skill/"

if ! grep -Fq "\"commit\": \"$official_commit\"" "$manifest"; then
  printf 'MANIFEST_LOCK_MISMATCH official commit\n' >&2
  exit 1
fi

skill_hash() {
  entry=$1
  if [ ! -f "$entry" ]; then
    return 1
  fi
  perl -pe 's/\r\n?/\n/g' "$entry" | shasum -a 256 | awk '{print $1}'
}

has_required() {
  name=$1
  shift
  for relative in "$@"; do
    if [ ! -f "$target_root/$name/$relative" ]; then
      return 1
    fi
  done
  return 0
}

jupyter_expected=62f102e8554b25716dccef0ffab4572d4e3eaf05ccc76562d33a065bc9c521fb
pdf_expected=d108cf2b36355ab37eb5962933f4d09785ec002f3105c506129320209306b9d2
ansys_expected=0b0efd83d2c1e1e38879cda9fd46633442570b7d482f28d146931eb072f07cbd
jupyter_actual=$(skill_hash "$target_root/jupyter-notebook/SKILL.md" || true)
pdf_actual=$(skill_hash "$target_root/pdf/SKILL.md" || true)
official_needed=0

if [ "$jupyter_actual" != "$jupyter_expected" ] || ! has_required jupyter-notebook \
  LICENSE.txt SKILL.md agents/openai.yaml assets/experiment-template.ipynb \
  assets/jupyter-small.svg assets/jupyter.png assets/tutorial-template.ipynb \
  references/experiment-patterns.md references/notebook-structure.md \
  references/quality-checklist.md references/tutorial-patterns.md scripts/new_notebook.py; then
  official_needed=1
fi
if [ "$pdf_actual" != "$pdf_expected" ] || ! has_required pdf \
  LICENSE.txt SKILL.md agents/openai.yaml assets/pdf.png; then
  official_needed=1
fi

if [ "$official_needed" -eq 1 ]; then
  command -v curl >/dev/null 2>&1 || { printf 'MISSING_TOOL curl\n' >&2; exit 1; }
  command -v unzip >/dev/null 2>&1 || { printf 'MISSING_TOOL unzip\n' >&2; exit 1; }
  temp_root=$(mktemp -d "${TMPDIR:-/tmp}/openai-skills.XXXXXX")
  trap 'rm -rf "$temp_root"' EXIT HUP INT TERM
  archive="$temp_root/openai-skills.zip"
  curl -L --fail "https://github.com/openai/skills/archive/$official_commit.zip" -o "$archive"
  unzip -q "$archive" -d "$temp_root"
  extracted="$temp_root/skills-$official_commit"
  rsync -a --delete "$extracted/skills/.curated/jupyter-notebook/" "$target_root/jupyter-notebook/"
  rsync -a --delete "$extracted/skills/.curated/pdf/" "$target_root/pdf/"
fi

check_skill() {
  name=$1
  expected=$2
  entry="$target_root/$name/SKILL.md"
  if [ ! -f "$entry" ]; then
    printf 'MISSING %s\n' "$name" >&2
    return 1
  fi
  actual=$(perl -pe 's/\r\n?/\n/g' "$entry" | shasum -a 256 | awk '{print $1}')
  if [ "$actual" != "$expected" ]; then
    printf 'HASH_MISMATCH %s expected=%s actual=%s\n' "$name" "$expected" "$actual" >&2
    return 1
  fi
  printf 'PASS %s %s\n' "$name" "$actual"
}

check_required() {
  name=$1
  shift
  for relative in "$@"; do
    path="$target_root/$name/$relative"
    if [ ! -f "$path" ]; then
      printf 'MISSING_REQUIRED %s %s\n' "$name" "$relative" >&2
      return 1
    fi
  done
  printf 'FILES_PASS %s count=%s\n' "$name" "$#"
}

check_skill airjet-product-reconstruction 56a977a9723b0b53158f93b21674308accc51937baacfdb55b00c29e3356a63f
check_skill airjet-ansys-automation "$ansys_expected"
check_skill jupyter-notebook "$jupyter_expected"
check_skill pdf "$pdf_expected"

check_required airjet-product-reconstruction \
  SKILL.md agents/openai.yaml references/evidence-rules.md references/stage-routing.md \
  references/windows-operation.md scripts/audit_project.py
check_required airjet-ansys-automation \
  SKILL.md agents/openai.yaml references/official-automation-routes.md \
  references/gate-evidence.md scripts/bootstrap_windows.ps1 \
  scripts/airjet_ansys_mcp.py scripts/run_t0_suite.py scripts/run_t1_cad_suite.py \
  scripts/run_t1_semantic_reconstruction_suite.py \
  scripts/test_t1_predecessor_negative.py \
  scripts/test_airjet_ansys_mcp_policy.py
check_required jupyter-notebook \
  LICENSE.txt SKILL.md agents/openai.yaml assets/experiment-template.ipynb \
  assets/jupyter-small.svg assets/jupyter.png assets/tutorial-template.ipynb \
  references/experiment-patterns.md references/notebook-structure.md \
  references/quality-checklist.md references/tutorial-patterns.md scripts/new_notebook.py
check_required pdf LICENSE.txt SKILL.md agents/openai.yaml assets/pdf.png

printf 'Installed project skill to %s\n' "$target_skill"
printf 'Installed ANSYS automation skill to %s\n' "$target_ansys_skill"
printf 'Start a fresh Codex session to load newly installed skills.\n'
