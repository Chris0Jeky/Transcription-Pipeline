# Git setup (run on your machine)

Everything is prepared: `.gitignore`, `.env` (your token, ignored), `.env.example`,
`.gitkeep` folder placeholders, and the READMEs. You just need to create the repo
locally and push it. (This couldn't be done from the assistant sandbox because
OneDrive's cloud-sync interferes with git's internal files there. On your own PC
it works normally.)

## 1. Create the local repo
Double-click **`setup_git.bat`**, or run in a terminal from this folder:
```bat
git init
git branch -M main
git add -A
git commit -m "Initial commit: From the Boys transcription pipeline"
```

## 2. Confirm the right things are tracked
```bat
git ls-files
```
You should see the `Transcription Pipeline/` code, the READMEs, `.env.example`,
and the empty-folder `.gitkeep` placeholders — but NOT `.env`, any audio, the
`.docx` files, or the highlighted transcripts.

Sanity-check that secrets/content are ignored:
```bat
git check-ignore "Transcription Pipeline/.env" AUDIO/DAY_3/JELY_INTERVIEW
```
(Both should print, meaning they're ignored.)

## 3. Publish to GitHub
Option A - website + terminal:
1. Create an **empty** repo at https://github.com/new (no README, no .gitignore).
2. Then:
```bat
git remote add origin https://github.com/YOURNAME/from-the-boys.git
git push -u origin main
```

Option B - GitHub CLI (if installed):
```bat
gh repo create from-the-boys --private --source . --remote origin --push
```

## Notes
- **Rotate your Hugging Face token.** It was shared in chat, so regenerate it at
  huggingface.co (Settings -> Access Tokens) once you're set up, and update `.env`.
  Never commit `.env` — it's already ignored.
- **Private vs public:** keep it **private** unless you're sure. The code is safe
  to share; the token and content are ignored, but private is the safe default.
- To add a collaborator (Jake), use the repo's Settings -> Collaborators on GitHub.
