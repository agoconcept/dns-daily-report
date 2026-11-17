if ! declare -F log > /dev/null; then
    log() { echo "[clients] $*" >&2; }
fi

declare -A CLIENT_DESCRIPTIONS=()

load_client_descriptions() {
    local config_file="$1"
    local line ip desc

    if [[ ! -f "${config_file}" ]]; then
        log "Config file not found: ${config_file}, no descriptions loaded"
        return 0
    fi

    if ! line_out=$(python3 -c '
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for ip, desc in data.items():
    print(f"{ip}\t{desc}")
' "${config_file}" 2>/dev/null); then
        log "Failed to parse ${config_file}, no descriptions loaded"
        return 0
    fi

    while IFS=$'\t' read -r ip desc; do
        [[ -z "${ip}" ]] && continue
        CLIENT_DESCRIPTIONS[$ip]="$desc"
    done <<< "$line_out"
}

client_header() {
    local ip="$1"
    local desc="${CLIENT_DESCRIPTIONS[$ip]:-}"
    if [[ -n "${desc}" ]]; then
        echo "=== Report for ${ip} (${desc}) ==="
    else
        echo "=== Report for ${ip} ==="
    fi
}

clients_section() {
    local ip_list="$1"
    local ip desc
    echo "=== Clients ==="
    for ip in $ip_list; do
        desc="${CLIENT_DESCRIPTIONS[$ip]:-}"
        if [[ -n "${desc}" ]]; then
            echo "- ${ip}: ${desc}"
        else
            echo "- ${ip}"
        fi
    done
}
