# Theonix OS Release Key
# =======================
# This file contains the *public* key ID and fingerprint of the Theonix OS
# Release signing key. Private key is never stored in this repository.
#
# Key details:
#   Name:        Theonix OS Release Key
#   Email:       security@theonix.org
#   Type:        RSA 4096
#   Expires:     2 years from generation date
#
# Setup instructions (one-time, by the release manager):
# -------------------------------------------------------
#
# 1. Generate the key pair (run on an air-gapped machine if possible):
#    gpg --batch --gen-key <<EOF
#    Key-Type: RSA
#    Key-Length: 4096
#    Key-Usage: sign
#    Subkey-Type: RSA
#    Subkey-Length: 4096
#    Subkey-Usage: sign
#    Name-Real: Theonix OS Release Key
#    Name-Email: security@theonix.org
#    Expire-Date: 2y
#    %no-protection
#    %commit
#    EOF
#
# 2. Export the public key:
#    gpg --armor --export security@theonix.org > repo/keys/theonix-release.pub
#
# 3. Get the key fingerprint and store it:
#    gpg --fingerprint security@theonix.org > repo/keys/fingerprint.txt
#
# 4. Set THEONIX_GPG_KEY_ID for CI:
#    export THEONIX_GPG_KEY_ID=$(gpg --list-keys --with-colons security@theonix.org \
#      | awk -F: '/^fpr/{print $10; exit}')
#
# 5. Upload the public key to a keyserver:
#    gpg --keyserver keys.openpgp.org --send-keys "${THEONIX_GPG_KEY_ID}"
#
# 6. Store THEONIX_GPG_KEY_ID and the private key export as a GitHub Secret.
#    The private key must NEVER be committed to this repository.
#
# IMPORTANT: repo/keys/*.key and repo/keys/*.pem are in .gitignore.
#            Only this README and the .pub file should be committed.
