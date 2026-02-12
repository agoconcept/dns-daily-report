#!/bin/bash

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

# Initialize report
COMBINED_REPORT="${REPORT_DIR}/summary_${DATE}.txt"
> "$COMBINED_REPORT"

# Iterate over all client IPs
for CLIENT_IP in $CLIENT_IPS; do

    echo "=== Report for ${CLIENT_IP} ===" >> "$COMBINED_REPORT"
    echo "" >> "$COMBINED_REPORT"

    mkdir -p "$REPORT_DIR"/${CLIENT_IP}

    REPORT_FILE="${REPORT_DIR}/${CLIENT_IP}/${DATE}.txt"

    # Get data directly from Pi Hole SQLite
    sqlite3 /etc/pihole/pihole-FTL.db <<EOF > "$REPORT_FILE"
.headers on
.mode column
SELECT domain, COUNT(*) as queries
FROM queries
WHERE client='${CLIENT_IP}'
AND timestamp > ${TIMESTAMP}
GROUP BY domain
ORDER BY queries DESC
LIMIT 100;
EOF

    cat "$REPORT_FILE" >> "$COMBINED_REPORT"
    echo -e "\n\n" >> "$COMBINED_REPORT"
done

# Analyze report with Gemini (if GEMINI_API_KEY is set)
if [[ -n "${GEMINI_API_KEY}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ANALYSIS_FILE="${REPORT_DIR}/analysis_${DATE}.txt"

    if python3 "${SCRIPT_DIR}/analyze_report.py" "$COMBINED_REPORT" > "$ANALYSIS_FILE" 2>&1; then
        echo -e "\n\n=== AI ANALYSIS ===" >> "$COMBINED_REPORT"
        cat "$ANALYSIS_FILE" >> "$COMBINED_REPORT"
    fi
fi

# Send email
cat "$COMBINED_REPORT" | mail -s "Pi-hole Daily Report - ${DATE}" "$EMAIL"

