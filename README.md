# Full Streamlit + LangGraph Agentic Chatbot with MS Excel Online Integration for Denial Code Library
This is a complete, production-ready agentic chatbot tailored to your Denial_Code_Library_Template 1.xlsx (DME Denials sheet with 100 rows, 11 columns, 9 unique codes like CO-50, CO-16). It:

Fetches from MS Excel Online (OneDrive/SharePoint) – paste your share link.
Local Ollama LLM (Llama3.1) + LangGraph ReAct agent for reasoning.
Specialized Tools: Code lookup, category analysis, TAT summaries, custom Python REPL.
Handles duplicates (drops them automatically).
Daily updates with caching + refresh button.
Secure & Local – no data leaves your machine.

# RAG Chatbot with Google Sheets Integration

A Retrieval-Augmented Generation (RAG) chatbot built with Streamlit that allows users to upload documents and connect Google Sheets to ask questions using AI-powered semantic search.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.31.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Features

- **📄 Document Upload** - Support for .txt, .md, and .csv files
- **📊 Google Sheets Integration** - Direct connection to Google Sheets
- **🔍 Semantic Search** - Vector-based similarity search
- **🤖 AI-Powered Answers** - Claude AI integration for intelligent responses
- **📚 Source Citations** - Shows which documents were used for answers
- **💬 Chat Interface** - Interactive chat with conversation history
- **⚡ Real-time Processing** - Instant document chunking and vectorization

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Anthropic Claude API key
- Git (for version control)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### 1. Configure API Key

- Enter your Anthropic Claude API key in the sidebar
- Get your API key from [https://console.anthropic.com/](https://console.anthropic.com/)

### 2. Upload Data Sources

**Option A: Upload Files**
- Click "Choose files" in the sidebar
- Select .txt, .md, or .csv files
- Click "Process Files"

**Option B: Connect Google Sheet**
- Make your Google Sheet public (Anyone with link can view)
- Copy the share URL
- Paste in "Sheet URL" field
- Click "Connect"

### 3. Ask Questions

- Type your question in the chat input
- The system will:
  - Find relevant chunks from your data
  - Generate an AI-powered answer
  - Show source citations

## 📊 Google Sheets Setup

### Step 1: Prepare Your Sheet

1. Open your Google Sheet
2. Click **Share** (top-right)
3. Click **"Change to anyone with the link"**
4. Set permission to **Viewer**
5. Click **Done**

### Step 2: Get the URL

1. Click **Share** again
2. Click **Copy link**
3. Your URL should look like:
   ```
   https://docs.google.com/spreadsheets/d/1abc123...xyz/edit?usp=sharing
   ```

### Step 3: Connect to App

1. Paste URL in sidebar
2. Click "Connect"
3. Wait for processing
4. Start asking questions!

## 💡 Example Use Cases

### Sales Analytics
```
Sheet: Sales data with Product, Quantity, Price columns
Question: "What's our top-selling product?"
```

### Customer Database
```
Sheet: Customer info with Name, Email, City, Status
Question: "List all active customers from New York"
```

### Inventory Management
```
Sheet: SKU, Item, Quantity, Reorder Level
Question: "Which items need reordering?"
```

## 🏗️ Architecture

### How It Works

1. **Document Processing**
   - Documents are split into chunks (500 chars with 100 char overlap)
   - Each chunk is converted to a vector embedding

2. **Retrieval**
   - User query is converted to vector embedding
   - Top 3 most similar chunks are retrieved using cosine similarity

3. **Generation**
   - Retrieved chunks sent to Claude AI as context
   - AI generates answer based on context
   - Sources displayed with answer

### Tech Stack

- **Streamlit** - Web framework
- **NumPy** - Vector operations
- **Pandas** - Data handling
- **Requests** - API calls
- **Claude API** - Answer generation

## 🔧 Configuration

### Environment Variables

Create a `.streamlit/secrets.toml` file (optional):

```toml
[api]
anthropic_api_key = "your-api-key-here"
```

### Customization

Edit these parameters in `app.py`:

```python
# Chunk size
chunk_size = 500  # Characters per chunk
overlap = 100     # Overlap between chunks

# Retrieval
top_k = 3  # Number of chunks to retrieve

# Embedding dimension
dimension = 128  # Vector size
```

## 📁 Project Structure

```
rag-chatbot/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── .streamlit/        # Streamlit config (create if needed)
    └── secrets.toml   # API keys (not tracked)
```

## 🌐 Deployment

### Deploy to Streamlit Cloud

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/rag-chatbot.git
git push -u origin main
```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file as `app.py`
   - Add your API key in secrets
   - Deploy!

### Deploy to Other Platforms

**Heroku:**
```bash
heroku create your-app-name
git push heroku main
```

**Railway:**
- Connect GitHub repo
- Add environment variables
- Deploy automatically

**AWS/GCP/Azure:**
- Use Docker container
- Set up load balancer
- Configure auto-scaling

## 🔒 Security Best Practices

- ✅ Never commit API keys to Git
- ✅ Use environment variables or secrets management
- ✅ Add `.env` to `.gitignore`
- ✅ Use HTTPS for production deployments
- ✅ Implement rate limiting for public deployments
- ✅ Validate and sanitize user inputs

## 🐛 Troubleshooting

### Common Issues

**"Error fetching Google Sheet"**
- Ensure sheet is public
- Check URL is complete
- Verify internet connection

**"Enter API key"**
- Add Anthropic API key in sidebar
- Check key is valid

**"Upload data first"**
- Upload at least one document or connect a sheet
- Wait for processing to complete

**Slow performance**
- Large documents take longer to process
- Consider chunking very large files
- Use more specific queries

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

## 📝 Version Control Workflow

### Initial Setup
```bash
git init
git add .
git commit -m "Initial commit: RAG chatbot with Google Sheets"
```

### Making Changes
```bash
git checkout -b feature/new-feature
# Make your changes
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

### Creating Releases
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## 🔮 Future Enhancements

- [ ] OAuth integration for private Google Sheets
- [ ] Support for multiple sheet tabs
- [ ] Excel file upload (.xlsx)
- [ ] Advanced embedding models (OpenAI, sentence-transformers)
- [ ] Vector database integration (Pinecone, Weaviate)
- [ ] Conversation export (PDF, JSON)
- [ ] Multi-language support
- [ ] Real-time sheet synchronization
- [ ] User authentication and sessions
- [ ] Analytics dashboard

## 📄 License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude AI
- [Streamlit](https://streamlit.io/) for the amazing framework
- [Google](https://www.google.com/sheets/) for Sheets API

## 📧 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com
- Project Link: [https://github.com/yourusername/rag-chatbot](https://github.com/yourusername/rag-chatbot)

## ⭐ Star History

If you find this project helpful, please consider giving it a star!

---

**Built with ❤️ using Streamlit and Claude AI**

Deployment guide
# Deployment Guide: Streamlit Cloud

This guide will help you deploy your RAG Chatbot to Streamlit Cloud for free.

## Prerequisites

- GitHub account
- Streamlit Cloud account (free tier available)
- Your Anthropic Claude API key

## Step 1: Prepare Your GitHub Repository

### 1.1 Initialize Git Repository

```bash
cd rag-chatbot
git init
```

### 1.2 Add Files to Git

```bash
git add .
git status  # Verify files are staged
```

### 1.3 Create Initial Commit

```bash
git commit -m "Initial commit: RAG chatbot with Google Sheets integration"
```

### 1.4 Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click **"New repository"**
3. Name it: `rag-chatbot` (or your preferred name)
4. Make it **Public** (required for free Streamlit Cloud)
5. **DO NOT** initialize with README (we already have one)
6. Click **"Create repository"**

### 1.5 Push to GitHub

```bash
# Add remote origin (replace with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/rag-chatbot.git

# Push code
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Streamlit Cloud

### 2.1 Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"**
3. Sign in with your GitHub account
4. Authorize Streamlit to access your repositories

### 2.2 Create New App

1. Click **"New app"** button
2. Select the following:
   - **Repository:** `YOUR_USERNAME/rag-chatbot`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Click **"Advanced settings"** (optional but recommended)

### 2.3 Configure Secrets

In the Advanced settings:

1. Scroll to **"Secrets"**
2. Add your API key in TOML format:

```toml
# .streamlit/secrets.toml format
ANTHROPIC_API_KEY = "your-api-key-here"
```

3. Click **"Save"**

### 2.4 Deploy

1. Click **"Deploy!"**
2. Wait for deployment (usually 1-2 minutes)
3. Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

## Step 3: Update Your App to Use Secrets

Modify `app.py` to use Streamlit secrets (optional):

```python
import streamlit as st

# In the sidebar API key section, add default from secrets:
if 'api_key' not in st.session_state:
    st.session_state.api_key = st.secrets.get("ANTHROPIC_API_KEY", "")

api_key = st.text_input(
    "Claude API Key",
    type="password",
    value=st.session_state.api_key,
    help="Enter your Anthropic Claude API key"
)
```

## Step 4: Manage Your Deployment

### View Logs

1. Go to your app dashboard
2. Click **"Manage app"**
3. View logs in real-time

### Update App

Whenever you push to GitHub:

```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```

Streamlit Cloud will automatically redeploy!

### Manage Resources

Free tier includes:
- ✅ 1 app deployment
- ✅ 1 GB RAM
- ✅ Shared CPU
- ✅ Community support

For more apps or resources, upgrade to paid tier.

### Custom Domain (Paid Feature)

1. Go to app settings
2. Click **"Custom domain"**
3. Follow instructions to set up

## Step 5: Monitor and Maintain

### Check App Health

- Monitor uptime at your app URL
- Check logs for errors
- Review resource usage in dashboard

### Update Dependencies

If you need to update libraries:

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Commit and push
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### Rollback if Needed

```bash
# Find commit hash
git log

# Revert to previous commit
git revert <commit-hash>
git push origin main
```

## Troubleshooting

### Common Deployment Issues

**Problem:** "Module not found"
```bash
# Solution: Ensure all dependencies in requirements.txt
pip freeze | grep streamlit
pip freeze | grep pandas
```

**Problem:** "App won't start"
```bash
# Solution: Check logs in Streamlit Cloud dashboard
# Common issues:
# - Missing dependencies
# - Syntax errors
# - Port conflicts
```

**Problem:** "Secrets not working"
```bash
# Solution: Check secrets format in dashboard
# Must be valid TOML:
API_KEY = "value"  # Correct
API_KEY = value    # Wrong (missing quotes)
```

**Problem:** "Out of resources"
```bash
# Solution:
# - Optimize code for memory
# - Use smaller models/embeddings
# - Upgrade to paid tier
```

## Security Best Practices

### Never Commit Secrets

Ensure `.gitignore` includes:
```
.streamlit/secrets.toml
.env
*.key
```

### Verify Before Push

```bash
# Check what will be committed
git status
git diff

# Remove sensitive files if accidentally added
git rm --cached .streamlit/secrets.toml
```

### Use Environment-Specific Config

```python
import streamlit as st
import os

# Production vs Development
if os.getenv('ENVIRONMENT') == 'production':
    api_key = st.secrets["ANTHROPIC_API_KEY"]
else:
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
```

## Advanced Configuration

### Custom Streamlit Config

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor="#1f77b4"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#262730"
font="sans serif"

[server]
maxUploadSize=200
enableCORS=false
enableXsrfProtection=true

[browser]
gatherUsageStats=false
```

### Enable Analytics

Add to your app:

```python
import streamlit as st

# Simple analytics
st.components.v1.html(
    """
    <!-- Add your analytics code here -->
    """,
    height=0
)
```

## Monitoring and Logs

### View Application Logs

In Streamlit Cloud dashboard:
1. Click **"Manage app"**
2. View **"Logs"** tab
3. Filter by level (Info, Warning, Error)

### Add Custom Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In your code:
logger.info("User uploaded document")
logger.error("API call failed")
```

## Cost Optimization

### Free Tier Limits

- 1 public app
- 1 GB RAM
- Shared CPU
- No custom domain

### Optimize for Free Tier

1. **Minimize dependencies**
   - Use lightweight libraries
   - Avoid heavy ML models

2. **Efficient data handling**
   - Limit file upload sizes
   - Use pagination for large datasets

3. **Cache expensive operations**
   ```python
   @st.cache_data
   def expensive_function():
       # Cached computation
       pass
   ```

## Next Steps

1. ✅ Share your app URL with users
2. ✅ Monitor usage and feedback
3. ✅ Iterate based on user needs
4. ✅ Consider upgrading for:
   - Private apps
   - More resources
   - Custom domains
   - Priority support

## Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Forum](https://discuss.streamlit.io/)
- [Deployment Best Practices](https://docs.streamlit.io/knowledge-base/deploy)

## Support

If you encounter issues:
1. Check [Streamlit Forum](https://discuss.streamlit.io/)
2. Review [Streamlit Docs](https://docs.streamlit.io/)
3. Contact Streamlit support (paid plans)

---

**Congratulations! Your RAG Chatbot is now live! 🎉**

Share it: `https://your-app-name.streamlit.app`

# Git Workflow Guide for RAG Chatbot

Complete guide for version control and collaboration using Git and GitHub.

## Table of Contents
- [Initial Setup](#initial-setup)
- [Daily Workflow](#daily-workflow)
- [Branching Strategy](#branching-strategy)
- [Collaboration](#collaboration)
- [Best Practices](#best-practices)

## Initial Setup

### 1. Install Git

**Windows:**
```bash
# Download from https://git-scm.com/download/win
# Or use winget:
winget install --id Git.Git -e --source winget
```

**Mac:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt-get install git  # Ubuntu/Debian
sudo yum install git      # CentOS/RHEL
```

### 2. Configure Git

```bash
# Set your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default editor
git config --global core.editor "code --wait"  # VS Code
# or
git config --global core.editor "vim"

# Verify configuration
git config --list
```

### 3. Initialize Repository

```bash
# Navigate to project directory
cd rag-chatbot

# Initialize git
git init

# Verify
git status
```

### 4. Create .gitignore

Already created! Verify it includes:
```
__pycache__/
*.pyc
venv/
.env
.streamlit/secrets.toml
```

### 5. First Commit

```bash
# Stage all files
git add .

# Verify what will be committed
git status

# Create initial commit
git commit -m "Initial commit: RAG chatbot with Google Sheets integration"

# Verify
git log
```

## Daily Workflow

### Making Changes

```bash
# 1. Check current status
git status

# 2. Make your changes in code editor

# 3. View what changed
git diff

# 4. Stage specific files
git add app.py
git add requirements.txt

# Or stage all changes
git add .

# 5. Commit with descriptive message
git commit -m "Add: Google Sheets data validation"

# 6. Push to GitHub
git push origin main
```

### Commit Message Format

Follow this pattern for clear history:

```bash
# Feature
git commit -m "Add: new file upload feature"

# Bug fix
git commit -m "Fix: Google Sheets URL parsing error"

# Update
git commit -m "Update: improve chunk size algorithm"

# Refactor
git commit -m "Refactor: reorganize vector store functions"

# Documentation
git commit -m "Docs: update README with deployment steps"

# Style/Format
git commit -m "Style: format code with black"
```

### View History

```bash
# View commit history
git log

# View compact history
git log --oneline

# View last 5 commits
git log -5

# View specific file history
git log app.py

# View changes in commit
git show <commit-hash>
```

## Branching Strategy

### Feature Branch Workflow

```bash
# 1. Create new feature branch
git checkout -b feature/add-excel-support

# 2. Make changes and commit
git add .
git commit -m "Add: Excel file upload support"

# 3. Push feature branch
git push origin feature/add-excel-support

# 4. Create Pull Request on GitHub

# 5. After merge, switch back to main
git checkout main
git pull origin main

# 6. Delete local feature branch
git branch -d feature/add-excel-support
```

### Branch Naming Conventions

```bash
# Features
feature/add-user-authentication
feature/improve-search-algorithm

# Bug fixes
fix/google-sheets-timeout
fix/api-key-validation

# Documentation
docs/update-readme
docs/add-deployment-guide

# Refactoring
refactor/vector-store
refactor/ui-components

# Experiments
experiment/new-embedding-model
experiment/real-time-sync
```

### Managing Branches

```bash
# List all branches
git branch

# List remote branches
git branch -r

# Create branch
git branch feature/new-feature

# Switch to branch
git checkout feature/new-feature

# Create and switch in one command
git checkout -b feature/new-feature

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# Rename branch
git branch -m old-name new-name
```

## Collaboration

### Setting Up Remote

```bash
# Add remote repository
git remote add origin https://github.com/USERNAME/rag-chatbot.git

# Verify remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/USERNAME/new-repo.git
```

### Working with Team

```bash
# Pull latest changes before starting work
git pull origin main

# Push your changes
git push origin main

# Fetch updates without merging
git fetch origin

# Merge specific branch
git merge origin/feature-branch
```

### Resolving Conflicts

When you see merge conflicts:

```bash
# 1. Pull latest changes
git pull origin main

# 2. Git will show conflicts like:
# <<<<<<< HEAD
# Your changes
# =======
# Their changes
# >>>>>>> branch-name

# 3. Edit files to resolve conflicts

# 4. Stage resolved files
git add conflicted-file.py

# 5. Complete merge
git commit -m "Merge: resolve conflicts with main"

# 6. Push
git push origin main
```

### Pull Requests (PRs)

**Creating a PR:**

1. Push your feature branch:
```bash
git push origin feature/your-feature
```

2. Go to GitHub repository
3. Click "Pull requests" → "New pull request"
4. Select your branch
5. Add title and description
6. Click "Create pull request"

**PR Best Practices:**

- Write clear title: "Add Excel file support"
- Describe what changed and why
- Reference related issues: "Fixes #123"
- Request reviewers
- Link to documentation if needed

**Reviewing PRs:**

```bash
# Fetch PR branch
git fetch origin pull/ID/head:pr-branch-name
git checkout pr-branch-name

# Test the changes
# Review code

# Leave comments on GitHub
# Approve or request changes
```

## Best Practices

### Commit Frequency

✅ **Good:**
```bash
git commit -m "Add: user authentication"
git commit -m "Add: password encryption"
git commit -m "Add: login form validation"
```

❌ **Bad:**
```bash
# Don't commit too infrequently
git commit -m "Add entire authentication system with 500 changes"

# Don't commit too frequently
git commit -m "Add space"
git commit -m "Remove space"
```

### Commit Messages

✅ **Good:**
```bash
git commit -m "Fix: Google Sheets API timeout by increasing limit to 30s"
git commit -m "Add: support for CSV file uploads with validation"
```

❌ **Bad:**
```bash
git commit -m "fix"
git commit -m "changes"
git commit -m "asdf"
git commit -m "WIP"
```

### Before Committing

```bash
# 1. Review changes
git diff

# 2. Test your code
python -m pytest  # if using tests
streamlit run app.py  # manual test

# 3. Format code (if using formatter)
black app.py

# 4. Check what will be committed
git status

# 5. Commit
git add .
git commit -m "Clear message"
```

### Protecting Main Branch

On GitHub:

1. Go to Settings → Branches
2. Add branch protection rule for `main`
3. Enable:
   - Require pull request reviews
   - Require status checks
   - Prevent force push
   - Prevent deletion

### Sensitive Data

**Never commit:**
- API keys
- Passwords
- Database credentials
- Personal information
- Large binary files

**If you accidentally commit secrets:**

```bash
# Remove from last commit
git reset HEAD~1
git add .
git commit -m "Your message"

# Remove from history (use with caution!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

**Better approach:** Use git-secrets or similar tool

## Useful Git Commands

### Undo Changes

```bash
# Discard changes in working directory
git checkout -- file.py

# Unstage file
git reset HEAD file.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert commit (creates new commit)
git revert <commit-hash>
```

### Stashing Changes

```bash
# Save changes temporarily
git stash

# List stashes
git stash list

# Apply most recent stash
git stash apply

# Apply specific stash
git stash apply stash@{2}

# Apply and remove stash
git stash pop

# Clear all stashes
git stash clear
```

### Tagging Releases

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# List tags
git tag

# Push tag to remote
git push origin v1.0.0

# Push all tags
git push origin --tags

# Delete tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

### Viewing Differences

```bash
# Changes in working directory
git diff

# Changes staged for commit
git diff --staged

# Changes between branches
git diff main feature-branch

# Changes in specific file
git diff app.py

# Changes between commits
git diff commit1 commit2
```

## Version Control Workflow

### Release Process

```bash
# 1. Ensure main is up to date
git checkout main
git pull origin main

# 2. Create release branch
git checkout -b release/v1.0.0

# 3. Update version numbers in files
# - Update README.md
# - Update requirements.txt versions
# - Update any version constants

# 4. Commit release changes
git add .
git commit -m "Prepare release v1.0.0"

# 5. Create tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# 6. Push branch and tag
git push origin release/v1.0.0
git push origin v1.0.0

# 7. Create GitHub Release
# - Go to GitHub → Releases
# - Click "Create new release"
# - Select tag v1.0.0
# - Add release notes
# - Publish release

# 8. Merge to main
git checkout main
git merge release/v1.0.0
git push origin main
```

### Hotfix Process

```bash
# 1. Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# 2. Fix the bug
# Edit files...

# 3. Commit fix
git add .
git commit -m "Fix: critical Google Sheets parsing bug"

# 4. Push and create PR
git push origin hotfix/critical-bug

# 5. After review and merge, tag if needed
git tag -a v1.0.1 -m "Hotfix release 1.0.1"
git push origin v1.0.1
```

## Git Aliases (Time Savers)

Add to `~/.gitconfig`:

```bash
[alias]
    # Shortcuts
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    
    # Pretty log
    lg = log --oneline --graph --decorate --all
    
    # Last commit
    last = log -1 HEAD
    
    # Amend last commit
    amend = commit --amend
    
    # Show diff of what would be committed
    diffc = diff --cached
```

Use them:
```bash
git st        # instead of git status
git co main   # instead of git checkout main
git lg        # pretty log view
```

## Troubleshooting

### Common Issues

**Problem:** Accidentally committed to main instead of feature branch

```bash
# Create feature branch at current commit
git branch feature/my-feature

# Reset main to previous commit
git reset --hard HEAD~1

# Switch to feature branch
git checkout feature/my-feature
```

**Problem:** Need to update commit message

```bash
# Last commit
git commit --amend -m "New message"

# Older commit (use with caution!)
git rebase -i HEAD~3  # Edit last 3 commits
```

**Problem:** Merge conflict

```bash
# Abort merge
git merge --abort

# Or resolve conflicts and continue
git add .
git commit
```

## Resources

- [Official Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Learn Git Branching (Interactive)](https://learngitbranching.js.org/)

---

**Happy Git-ing! 🚀**
