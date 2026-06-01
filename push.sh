#!/bin/bash

# Default commit message if none provided
COMMIT_MSG=${1:-"Update logic apps: fixed scheduler and weather automation"}

echo "🚀 Preparing to push changes..."

# Ensure remote origin is set to the correct repository
REPO_URL="https://github.com/harys-rifai/TeleAI"
if ! git remote get-url origin &> /dev/null; then
    echo "🔗 Adding remote origin: $REPO_URL"
    git remote add origin "$REPO_URL"
else
    echo "✅ Remote origin already configured."
fi

# Add changes excluding sensitive and temporary files
git add . ':!/.agents/*' ':!.env' ':!__pycache__/*' ':!*.pyc' ':!staticfiles/*' ':!venv/*' ':!*.sqlite3'

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "ℹ️  No changes detected, skipping commit."
else
    echo "📝 Committing: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
fi

# Push to current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📤 Pushing to origin $CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo "✅ Done!"