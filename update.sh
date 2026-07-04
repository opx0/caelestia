#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Caelestia Automated Update Script
#
# Automates the process of stashing local changes, pulling upstream updates,
# rebasing, popping stashed changes, and rebuilding the local package database
# if the PKGBUILD changed.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

log() { echo -e "${CYAN}▸${RESET} $1"; }
ok()  { echo -e "${GREEN}✓${RESET} $1"; }
warn() { echo -e "${YELLOW}⚠${RESET} $1"; }
fail() { echo -e "${RED}✗${RESET} $1"; echo ""; exit 1; }

REPO_DIR="$HOME/.local/share/caelestia"
LOCAL_REPO_DIR="/var/cache/pacman/local-repo"

cd "$REPO_DIR"

# 1. Check if git repository is clean
HAS_CHANGES=false
if ! git diff --quiet || ! git diff --cached --quiet; then
  HAS_CHANGES=true
fi

# 2. Save pre-update commit hash to check for PKGBUILD updates later
PREV_COMMIT=$(git rev-parse HEAD)

# 3. Stash changes if any exist
if [ "$HAS_CHANGES" = true ]; then
  log "Stashing your local modifications..."
  git stash -u
fi

# 4. Fetch and rebase
log "Fetching latest upstream updates..."
git fetch upstream

CURRENT_BRANCH=$(git branch --show-current)
log "Rebasing branch '$CURRENT_BRANCH' onto 'upstream/main'..."
if ! git rebase upstream/main; then
  warn "Rebase encountered conflicts! Aborting rebase. Please resolve manually."
  git rebase --abort
  if [ "$HAS_CHANGES" = true ]; then
    git stash pop || true
  fi
  fail "Rebase failed."
fi

# 5. Restore stashed changes
if [ "$HAS_CHANGES" = true ]; then
  log "Restoring your local modifications..."
  if ! git stash pop; then
    warn "Conflicts occurred while restoring your stashed changes! Please resolve them manually."
    log "To see the conflicts, check 'git status'."
    exit 0
  fi
fi

ok "Repository successfully updated!"

# 6. Check if PKGBUILD changed
POST_COMMIT=$(git rev-parse HEAD)
if git diff --name-only "$PREV_COMMIT" "$POST_COMMIT" | grep -q "PKGBUILD"; then
  log "PKGBUILD has changed. Rebuilding package..."
  
  # Clean old pkg files
  rm -f caelestia-meta-*.pkg.tar.zst
  
  # Rebuild package
  if makepkg -s --noconfirm; then
    log "Copying new package to local-repo..."
    cp caelestia-meta-*.pkg.tar.zst "$LOCAL_REPO_DIR/"
    
    log "Updating local-repo database..."
    repo-add "$LOCAL_REPO_DIR/local-repo.db.tar.gz" "$LOCAL_REPO_DIR"/caelestia-meta-*.pkg.tar.zst
    
    ok "Metapackage rebuilt successfully!"
    log "Please run: ${GREEN}sudo pacman -Syu${RESET} to complete the update on your system."
  else
    fail "Failed to build the metapackage."
  fi
else
  ok "No PKGBUILD updates detected. No package rebuild needed."
fi

# 7. Push to personal fork (optional, checks if origin exists)
if git remote | grep -q "^origin$"; then
  log "Backing up branch '$CURRENT_BRANCH' to your personal fork..."
  if git push origin "$CURRENT_BRANCH" --force-with-lease; then
    ok "Fork backup complete!"
  else
    warn "Failed to push backup to origin fork."
  fi
fi

ok "All done!"
