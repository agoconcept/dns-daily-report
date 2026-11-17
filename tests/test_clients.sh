#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPT_DIR}/clients.sh"

PASS=0
FAIL=0

assert_equals() {
    local desc="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        PASS=$((PASS+1))
    else
        FAIL=$((FAIL+1))
        echo "FAIL: ${desc}"
        echo "  expected: ${expected}"
        echo "  actual:   ${actual}"
    fi
}

TMPDIR_TEST="$(mktemp -d)"
trap 'rm -rf "${TMPDIR_TEST}"' EXIT

cat > "${TMPDIR_TEST}/clients.json" <<'EOF'
{
  "192.168.1.135": "Alice's tablet",
  "192.168.1.141": "Bob's laptop"
}
EOF

declare -A CLIENT_DESCRIPTIONS=()
load_client_descriptions "${TMPDIR_TEST}/clients.json"
assert_equals "descriptions loaded from valid JSON" \
    "Alice's tablet" "${CLIENT_DESCRIPTIONS[192.168.1.135]}"
assert_equals "second description loaded" \
    "Bob's laptop" "${CLIENT_DESCRIPTIONS[192.168.1.141]}"

declare -A CLIENT_DESCRIPTIONS=()
load_client_descriptions "${TMPDIR_TEST}/does_not_exist.json"
assert_equals "missing config file yields no descriptions" \
    "0" "${#CLIENT_DESCRIPTIONS[@]}"

echo '{"192.168.1.135": broken' > "${TMPDIR_TEST}/broken.json"
declare -A CLIENT_DESCRIPTIONS=()
load_client_descriptions "${TMPDIR_TEST}/broken.json" 2>/dev/null
assert_equals "malformed JSON yields no descriptions" \
    "0" "${#CLIENT_DESCRIPTIONS[@]}"

declare -A CLIENT_DESCRIPTIONS=()
echo '{}' > "${TMPDIR_TEST}/empty.json"
load_client_descriptions "${TMPDIR_TEST}/empty.json"
assert_equals "empty JSON object yields no descriptions" \
    "0" "${#CLIENT_DESCRIPTIONS[@]}"

declare -A CLIENT_DESCRIPTIONS=(["192.168.1.135"]="Alice's tablet")
assert_equals "header includes description" \
    "=== Report for 192.168.1.135 (Alice's tablet) ===" \
    "$(client_header 192.168.1.135)"

CLIENT_DESCRIPTIONS=()
assert_equals "header falls back to IP only" \
    "=== Report for 192.168.1.100 ===" \
    "$(client_header 192.168.1.100)"

declare -A CLIENT_DESCRIPTIONS=(["192.168.1.135"]="Alice's tablet" ["192.168.1.141"]="Bob's laptop")
assert_equals "client section lists known and unknown IPs" \
    "=== Clients ===
- 192.168.1.135: Alice's tablet
- 192.168.1.141: Bob's laptop
- 192.168.1.100" \
    "$(clients_section "192.168.1.135 192.168.1.141 192.168.1.100")"

echo ""
echo "Tests: ${PASS} passed, ${FAIL} failed"
[[ "${FAIL}" -eq 0 ]]
