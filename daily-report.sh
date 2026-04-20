#!/bin/bash

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# Parse arguments
# NOTE! Email list must be comma-separated
# NOTE! Client IPs must be space-separated
OPTS=$(getopt -o he:i:d: --long help,email:,ips:,dir: -n 'daily-report.sh' -- "$@")
eval set -- "$OPTS"
while true; do
    case "$1" in
        -h|--help) echo "Usage: daily-report.sh --email <list of receivers> --ips <list of IPs> --dir <report dir>"; exit 0 ;;
        -e|--email) EMAIL="$2"; shift 2 ;;
        -i|--ips) CLIENT_IPS="$2"; shift 2 ;;
        -d|--dir) REPORT_DIR="$2"; shift 2 ;;
        --) shift; break ;;
        *) exit 1 ;;
    esac
done

# Check if parameters are unset
if [[ -z "${EMAIL}"  ]]; then
    echo "Mail receivers not set"
    exit
fi

if [[ -z "${CLIENT_IPS}"  ]]; then
    echo "Client IPs not set"
    exit
fi

if [[ -z "${REPORT_DIR}"  ]]; then
    echo "Report dir not set"
    exit
fi

# Calculate dates
DATE=$(date -d '1 day ago' +%Y-%m-%d)
TIMESTAMP=$(date -d '1 day ago' +%s)

log "Generating Pi-hole DNS report for ${DATE}"
log "Email: ${EMAIL}"
log "Client IPs: ${CLIENT_IPS}"

# Initialize report
COMBINED_REPORT="${REPORT_DIR}/summary_${DATE}.txt"
> "$COMBINED_REPORT"

# Iterate over all client IPs
for CLIENT_IP in $CLIENT_IPS; do
    log "Querying DNS data for ${CLIENT_IP}..."

    echo "=== Report for ${CLIENT_IP} ===" >> "$COMBINED_REPORT"
    echo "" >> "$COMBINED_REPORT"

    mkdir -p "$REPORT_DIR"/${CLIENT_IP}

    REPORT_FILE="${REPORT_DIR}/${CLIENT_IP}/${DATE}.txt"

    # Get data directly from Pi Hole SQLite
    sqlite3 /etc/pihole/pihole-FTL.db <<EOF > "$REPORT_FILE"
.mode markdown
SELECT
    q.domain,
    COUNT(*) as total_queries,
    SUM(CASE WHEN q.status IN (1, 4, 5, 6, 7, 8, 9, 10, 11) THEN 1 ELSE 0 END) as blocked,
    SUM(CASE WHEN q.status IN (2, 3) THEN 1 ELSE 0 END) as allowed
FROM queries q
LEFT JOIN client_by_id c ON q.client = c.ip
WHERE q.client="${CLIENT_IP}" AND q.timestamp > ${TIMESTAMP}
GROUP BY q.domain
ORDER BY total_queries DESC
LIMIT 500;
EOF

    DOMAIN_COUNT=$(grep -c '.' "$REPORT_FILE" 2>/dev/null || echo 0)
    log "  Found ${DOMAIN_COUNT} domains for ${CLIENT_IP}"

    cat "$REPORT_FILE" >> "$COMBINED_REPORT"
    echo -e "\n\n" >> "$COMBINED_REPORT"
done

# Analyze report with LLM (if an API key is set), otherwise fall back to raw summary
if [[ -n "${ZHIPU_API_KEY}" || -n "${MINIMAX_API_KEY}" || -n "${DEEPSEEK_API_KEY}" || -n "${GEMINI_API_KEY}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ANALYSIS_FILE="${REPORT_DIR}/analysis_${DATE}.txt"
    log "Running AI analysis..."
    python3 "${SCRIPT_DIR}/analyze_report.py" "$COMBINED_REPORT" "$SCRIPT_DIR/res/analysis_template.html" > "$ANALYSIS_FILE"
    if [[ $? -eq 0 ]]; then
        log "Analysis complete: ${ANALYSIS_FILE}"
    else
        log "ERROR: Analysis failed, check ${ANALYSIS_FILE}"
        exit 1
    fi
else
    log "No LLM API key set, sending raw summary"
    echo "No API key defined" | mail -s "Pi-hole Daily Report - ${DATE}" "$EMAIL"
    exit 0
fi

# Send email
log "Sending email to ${EMAIL}"
cat "$ANALYSIS_FILE" | mail -a "Content-Type: text/html; charset=UTF-8" -s "Pi-hole Daily Report - ${DATE}" "$EMAIL"
log "Done"

