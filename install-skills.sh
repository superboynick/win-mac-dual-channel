#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target_root=${CODEX_HOME:-"$HOME/.codex"}/skills
source_skill="$repo_root/codex-skills/airjet-product-reconstruction"
target_skill="$target_root/airjet-product-reconstruction"

mkdir -p "$target_root" "$target_skill"
rsync -a --delete "$source_skill/" "$target_skill/"

check_skill() {
  name=$1
  expected=$2
  entry="$target_root/$name/SKILL.md"
  if [ ! -f "$entry" ]; then
    printf 'MISSING %s\n' "$name" >&2
    return 1
  fi
  actual=$(shasum -a 256 "$entry" | awk '{print $1}')
  if [ "$actual" != "$expected" ]; then
    printf 'HASH_MISMATCH %s expected=%s actual=%s\n' "$name" "$expected" "$actual" >&2
    return 1
  fi
  printf 'PASS %s %s\n' "$name" "$actual"
}

check_skill airjet-product-reconstruction cb9fd3c78c09aed5cfb95d04194791f1a8f8799f20ad42cddc03f20f0281386c
check_skill jupyter-notebook 62f102e8554b25716dccef0ffab4572d4e3eaf05ccc76562d33a065bc9c521fb
check_skill pdf d108cf2b36355ab37eb5962933f4d09785ec002f3105c506129320209306b9d2

printf 'Installed project skill to %s\n' "$target_skill"
printf 'Start a fresh Codex session to load newly installed skills.\n'
