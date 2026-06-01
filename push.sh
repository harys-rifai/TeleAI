#!/bin/bash

# Add changes excluding .agents directory and .env
git add . ':!/.agents/' ':!.env'

# Commit with message
git commit -m "Update project files"

# Push to remote
git push