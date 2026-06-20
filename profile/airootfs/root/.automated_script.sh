#!/usr/bin/env bash
# Theonix OS — Live ISO Automated Script Runner
# Executes a startup script passed via kernel cmdline: script=https://...
#
# SECURITY POLICY:
#   - Scripts must be served from an allowlisted Theonix domain (HTTPS only)
#   - Every script must have a detached GPG signature (.sig) verified against
#     the Theonix OS Release Key before execution
#   - Any failure in validation causes immediate abort (no partial execution)
#
# ShellCheck: SC2034 exempted for unused vars from /proc/cmdline parsing

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

readonly THEONIX_LOG_TAG="theonix-autostart"
readonly TMP_SCRIPT="/tmp/theonix_startup_script"
readonly TMP_SIG="/tmp/theonix_startup_script.sig"
readonly TRUSTED_DOMAIN_1="theonix.org"
readonly TRUSTED_DOMAIN_2="cdn.theonix.org"
# Fingerprint of the Theonix OS Release GPG key (set during ISO build)
readonly THEONIX_KEY_FINGERPRINT_FILE="/etc/theonix/release_key_fingerprint"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

log_info()  { logger -t "${THEONIX_LOG_TAG}" -- "[INFO]  $*"; echo "[theonix-autostart] INFO:  $*"; }
log_warn()  { logger -t "${THEONIX_LOG_TAG}" -- "[WARN]  $*"; echo "[theonix-autostart] WARN:  $*" >&2; }
log_error() { logger -t "${THEONIX_LOG_TAG}" -- "[ERROR] $*"; echo "[theonix-autostart] ERROR: $*" >&2; }

# ---------------------------------------------------------------------------
# Extract the 'script=' parameter from the kernel cmdline
# Returns an empty string if the parameter is absent.
# ---------------------------------------------------------------------------

script_cmdline() {
    local param
    for param in $(</proc/cmdline); do
        case "${param}" in
            script=*)
                echo "${param#*=}"
                return 0
                ;;
        esac
    done
}

# ---------------------------------------------------------------------------
# Validate that a URL belongs to a trusted Theonix domain.
# Only HTTPS is accepted — plain HTTP is blocked unconditionally.
# ---------------------------------------------------------------------------

is_trusted_url() {
    local url="$1"
    local host

    # Require HTTPS scheme
    if [[ "${url}" != https://* ]]; then
        log_error "Rejected: URL must use HTTPS. Got: ${url}"
        return 1
    fi

    # Extract hostname (between https:// and the next / or end-of-string)
    host="${url#https://}"
    host="${host%%/*}"

    if [[ "${host}" == "${TRUSTED_DOMAIN_1}" || "${host}" == "*.${TRUSTED_DOMAIN_1}" || \
          "${host}" == "${TRUSTED_DOMAIN_2}" ]]; then
        return 0
    fi

    log_error "Rejected: host '${host}' is not in the Theonix trusted domain list."
    log_error "Allowed: ${TRUSTED_DOMAIN_1}, ${TRUSTED_DOMAIN_2}"
    return 1
}

# ---------------------------------------------------------------------------
# Download a file using curl with strict TLS settings.
# ---------------------------------------------------------------------------

secure_download() {
    local url="$1"
    local dest="$2"

    curl \
        --silent \
        --show-error \
        --fail \
        --location \
        --retry 3 \
        --retry-connrefused \
        --max-time 60 \
        --tlsv1.2 \
        --proto '=https' \
        --output "${dest}" \
        "${url}"
}

# ---------------------------------------------------------------------------
# Verify the GPG signature of a downloaded script.
# Requires the Theonix Release Key to be imported into the system keyring.
# ---------------------------------------------------------------------------

verify_gpg_signature() {
    local script_path="$1"
    local sig_path="$2"

    if [[ ! -f "${THEONIX_KEY_FINGERPRINT_FILE}" ]]; then
        log_error "Release key fingerprint file not found: ${THEONIX_KEY_FINGERPRINT_FILE}"
        log_error "Cannot verify signature — aborting for safety."
        return 1
    fi

    local expected_fingerprint
    expected_fingerprint="$(tr -d '[:space:]' < "${THEONIX_KEY_FINGERPRINT_FILE}")"

    if [[ -z "${expected_fingerprint}" ]]; then
        log_error "Release key fingerprint file is empty — aborting."
        return 1
    fi

    # Verify the detached signature; capture the signer's fingerprint
    local gpg_output
    if ! gpg_output="$(gpg --batch --no-tty --status-fd 1 \
            --verify "${sig_path}" "${script_path}" 2>&1)"; then
        log_error "GPG signature verification FAILED."
        log_error "GPG output: ${gpg_output}"
        return 1
    fi

    # Confirm the signing key matches the expected fingerprint
    if ! echo "${gpg_output}" | grep -qF "${expected_fingerprint}"; then
        log_error "Signature is valid but signed by an UNTRUSTED key."
        log_error "Expected fingerprint: ${expected_fingerprint}"
        log_error "GPG output: ${gpg_output}"
        return 1
    fi

    log_info "GPG signature verified successfully (fingerprint: ${expected_fingerprint})."
    return 0
}

# ---------------------------------------------------------------------------
# Main: orchestrate download, validation, and execution
# ---------------------------------------------------------------------------

automated_script() {
    local script_url
    script_url="$(script_cmdline)"

    # Nothing to do if no script= parameter was provided
    if [[ -z "${script_url}" ]]; then
        return 0
    fi

    log_info "Startup script requested: ${script_url}"

    # --- Step 1: Validate the URL is from a trusted Theonix domain ----------
    if ! is_trusted_url "${script_url}"; then
        log_error "Startup script URL failed domain validation. Aborting."
        return 1
    fi

    # --- Step 2: Wait for network availability via systemd ------------------
    log_info "Waiting for network-online.target..."
    if ! systemd-run \
            --pty \
            --quiet \
            --wait \
            --property=Wants=network-online.target \
            --property=After=network-online.target \
            -- /bin/true; then
        log_error "Network did not come online. Aborting."
        return 1
    fi

    # --- Step 3: Download the script ----------------------------------------
    log_info "Downloading script..."
    if ! secure_download "${script_url}" "${TMP_SCRIPT}"; then
        log_error "Failed to download: ${script_url}"
        return 1
    fi

    # --- Step 4: Download the detached GPG signature (.sig) -----------------
    local sig_url="${script_url}.sig"
    log_info "Downloading signature: ${sig_url}"
    if ! secure_download "${sig_url}" "${TMP_SIG}"; then
        log_error "Failed to download signature: ${sig_url}"
        log_error "Scripts without signatures are not permitted."
        rm -f "${TMP_SCRIPT}"
        return 1
    fi

    # --- Step 5: Verify GPG signature before touching the script ------------
    log_info "Verifying GPG signature..."
    if ! verify_gpg_signature "${TMP_SCRIPT}" "${TMP_SIG}"; then
        log_error "Signature verification failed. Script will NOT be executed."
        rm -f "${TMP_SCRIPT}" "${TMP_SIG}"
        return 1
    fi

    # --- Step 6: Make executable and run ------------------------------------
    chmod 700 "${TMP_SCRIPT}"
    log_info "Executing verified startup script..."
    "${TMP_SCRIPT}"
    local exit_code=$?

    # Clean up
    rm -f "${TMP_SCRIPT}" "${TMP_SIG}"

    if [[ ${exit_code} -ne 0 ]]; then
        log_warn "Startup script exited with code ${exit_code}."
    else
        log_info "Startup script completed successfully."
    fi

    return "${exit_code}"
}

# ---------------------------------------------------------------------------
# Entry point: only run from the primary virtual terminal
# ---------------------------------------------------------------------------

if [[ "$(tty)" == "/dev/tty1" ]]; then
    automated_script
fi
