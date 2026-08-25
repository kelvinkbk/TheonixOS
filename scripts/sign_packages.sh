#!/usr/bin/env bash
# =============================================================================
# Theonix OS — repo/scripts/sign_packages.sh
# =============================================================================
# Signs all unsigned packages in the repository directory and rebuilds
# the repository database with GPG signatures.
#
# Prerequisites:
#   - GPG key for Theonix OS Release imported and trusted
#   - THEONIX_GPG_KEY_ID set in environment or this script
#   - pacman repo-add installed
#
# Usage:
#   export THEONIX_GPG_KEY_ID="ABCD1234ABCD1234"
#   ./repo/scripts/sign_packages.sh [repo_path]
# =============================================================================

set -euo pipefail

REPO_PATH="${1:-repo/x86_64}"
REPO_DB_NAME="theonix"

if [[ -z "${THEONIX_GPG_KEY_ID:-}" ]]; then
    echo "ERROR: THEONIX_GPG_KEY_ID environment variable is not set." >&2
    echo "       Export the GPG key ID of the Theonix Release Key:" >&2
    echo "       export THEONIX_GPG_KEY_ID=\$(gpg --list-keys --with-colons security@theonix.org | awk -F: '/^fpr/{print \$10; exit}')" >&2
    exit 1
fi

if [[ ! -d "${REPO_PATH}" ]]; then
    echo "ERROR: Repository directory not found: ${REPO_PATH}" >&2
    exit 1
fi

echo "==> Signing packages in: ${REPO_PATH}"
echo "==> GPG Key ID: ${THEONIX_GPG_KEY_ID}"
echo ""

SIGNED=0
SKIPPED=0

# Sign each package that doesn't already have a valid signature
for pkg in "${REPO_PATH}"/*.pkg.tar.zst; do
    [[ -e "${pkg}" ]] || continue

    sig="${pkg}.sig"

    if [[ -f "${sig}" ]]; then
        # Verify existing signature is valid
        if gpg --batch --verify "${sig}" "${pkg}" &>/dev/null; then
            echo "    [SKIP] Already signed: $(basename "${pkg}")"
            SKIPPED=$(( SKIPPED + 1 ))
            continue
        else
            echo "    [WARN] Invalid/expired signature found — re-signing: $(basename "${pkg}")"
            rm -f "${sig}"
        fi
    fi

    echo "    [SIGN] $(basename "${pkg}")"
    gpg --batch \
        --no-tty \
        --detach-sign \
        --use-agent \
        --local-user "${THEONIX_GPG_KEY_ID}" \
        "${pkg}"

    SIGNED=$(( SIGNED + 1 ))
done

echo ""
echo "==> Signed: ${SIGNED} packages  |  Skipped (already signed): ${SKIPPED}"

# Rebuild the repository database with signature
echo "==> Rebuilding repository database..."

# Remove old database to force full rebuild
rm -f "${REPO_PATH}/${REPO_DB_NAME}.db.tar.gz"
rm -f "${REPO_PATH}/${REPO_DB_NAME}.db.tar.gz.sig"
rm -f "${REPO_PATH}/${REPO_DB_NAME}.files.tar.gz"

# repo-add: add all packages to the database, verify package signatures
repo-add \
    --sign \
    --key "${THEONIX_GPG_KEY_ID}" \
    --verify \
    "${REPO_PATH}/${REPO_DB_NAME}.db.tar.gz" \
    "${REPO_PATH}"/*.pkg.tar.zst

echo ""
echo "==> Repository database rebuilt and signed."
echo "==> Artifacts:"
ls -lh "${REPO_PATH}/${REPO_DB_NAME}".* 2>/dev/null || true
