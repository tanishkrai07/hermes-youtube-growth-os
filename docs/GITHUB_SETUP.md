# GitHub Setup

Use a private GitHub repo for this system.

## Recommended Steps

From inside `hermes_youtube_growth_os/`:

```bash
git init
git add .
git commit -m "Initialize Hermes YouTube Growth OS"
```

Then create a private GitHub repo named:

```text
hermes-youtube-growth-os
```

Push:

```bash
git remote add origin git@github.com:YOUR_USERNAME/hermes-youtube-growth-os.git
git branch -M main
git push -u origin main
```

## Privacy Rules

Do not commit:

- Telegram bot token
- OpenRouter key
- AWS credentials
- YouTube cookies/session data
- Raw long-form video renders
- Raw audio exports

Store secrets in `.env` locally or AWS Secrets Manager.

## Suggested Branches

- `main`: stable operating system.
- `daily-memory`: automated daily memory updates.
- `content-production`: scripts, thumbnails, metadata currently being built.

## Commit Style

Examples:

- `Add daily competitor snapshot for 2026-05-16`
- `Update winning patterns after week 1 analytics`
- `Add thumbnail swipe examples for sleep pillar`
- `Revise Hermes script prompt for stronger retention hooks`
