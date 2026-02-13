# DNS Daily Report

A bash script for generating daily DNS query reports from Pi-hole, organized by client device and delivered via email.

## Description

This tool queries Pi-hole's SQLite database to generate daily summaries of DNS queries for specified client devices. Reports are saved locally and emailed automatically, making it easy to monitor network activity and DNS usage patterns.

## Features

- Query Pi-hole database for DNS activity per client IP
- Generate daily reports showing top 100 domains queried
- Organize reports by client IP in separate directories
- Create combined summary reports
- AI-powered content analysis using Google Gemini
- Automatic email delivery of daily summaries
- Configurable via command-line arguments

## Prerequisites

- Pi-hole installed and running
- `mailutils` and `ssmtp` (or similar mail transfer agent)
- User must be in the `pihole` group to access the database
- SQLite3
- Python (for AI analysis feature)
- Google Gemini API key (for content analysis)

### Install Dependencies

```bash
sudo apt-get update
sudo apt-get install mailutils ssmtp sqlite3 python3 python3-pip
```

### Install Python Dependencies (for AI analysis)

```bash
pip3 install -r requirements.txt
```

### Configure Email (SSMTP with Gmail)

Edit `/etc/ssmtp/ssmtp.conf`:

```
root=your-email@gmail.com
mailhub=smtp.gmail.com:587
AuthUser=your-email@gmail.com
AuthPass=your-app-password
UseSTARTTLS=YES
FromLineOverride=YES
```

For Gmail, generate an app password at: https://myaccount.google.com/apppasswords

Test email configuration:
```bash
echo "Test" | mail -s "Test Subject" your-email@gmail.com
```

### Grant Database Access

Add your user to the `pihole` group:

```bash
sudo usermod -a -G pihole $USER
```

Log out and back in for the group change to take effect.

### Configure Gemini API (Optional)

For AI-powered content analysis:

1. Get a Gemini API key: https://makersuite.google.com/app/apikey

2. Set the environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

3. For persistent configuration, add to your crontab:
```bash
crontab -e
```

Add before your cron job line:
```
GEMINI_API_KEY=your-api-key-here
0 0 * * * /path/to/daily-report.sh --email "your@email.com" --ips "192.168.1.100" --dir "/home/pi/reports"
```

The AI analysis will automatically run if `GEMINI_API_KEY` is set, analyzing DNS queries for age-inappropriate content (social media, chat apps, adult content, etc.).

#### Retry Logic

The Gemini API client includes automatic retry logic with exponential backoff:
- 3 retry attempts on network or API errors
- Exponential backoff between retries (2-10 seconds)
- Handles transient failures and rate limits automatically

## Usage

```bash
./daily-report.sh --email <receivers> --ips <client_ips> --dir <report_directory>
```

### Arguments

- `--email`, `-e`: Comma-separated list of email recipients
- `--ips`, `-i`: Space-separated list of client IP addresses to monitor
- `--dir`, `-d`: Directory where reports will be saved
- `--help`, `-h`: Display help message

### Example

```bash
./daily-report.sh \
  --email "admin@example.com,user@example.com" \
  --ips "192.168.1.100 192.168.1.101 192.168.1.102" \
  --dir "/home/pi/reports"
```

## Cron Job Setup

To run the script automatically every day at midnight:

1. Make the script executable:
```bash
chmod +x daily-report.sh
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add the following line (adjust paths and parameters):
```
0 0 * * * /path/to/daily-report.sh --email "your@email.com" --ips "192.168.1.100 192.168.1.101" --dir "/home/pi/reports"
```

## Report Structure

Reports are organized as follows:

```
<report_dir>/
├── summary_YYYY-MM-DD.txt          # Combined report (emailed)
├── 192.168.1.100/
│   └── YYYY-MM-DD.txt              # Individual client report
├── 192.168.1.101/
│   └── YYYY-MM-DD.txt
└── ...
```

Each report contains:
- Domain names queried
- Number of queries per domain
- Top 100 domains sorted by query count

## Troubleshooting

### Permission Denied on Database

Ensure your user is in the `pihole` group:
```bash
groups
```

If `pihole` is not listed, add yourself and log out/in:
```bash
sudo usermod -a -G pihole $USER
```

### Email Not Sending

Test your mail configuration:
```bash
echo "Test" | mail -s "Test" your@email.com
```

Check SSMTP logs:
```bash
sudo tail -f /var/log/mail.log
```

### No Data in Reports

Verify Pi-hole database location:
```bash
ls -l /etc/pihole/pihole-FTL.db
```

Check if client IPs are correct:
```bash
sqlite3 /etc/pihole/pihole-FTL.db "SELECT DISTINCT client FROM queries LIMIT 10;"
```

## License

This project is provided as-is for personal use.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.
