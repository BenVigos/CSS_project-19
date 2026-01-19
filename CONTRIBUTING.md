# 🛠 Developer Workflow

### 1. Initial Setup
Run `uv sync` to install dependencies and create the virtual environment.

### 2. Daily Routine (Pull Before Coding)
Always stay up to date:
```bash
git checkout main
git pull origin main
uv sync
```

### 3. Feature Development
Do not code on 'main'. Use the 'dev' branch:
```bash
git checkout dev
# If dev doesn't exist: git checkout -b dev
```

### 4. Managing Packages with uv
```bash
uv add <package_name>  # Install a new library
uv run main.py         # Run your script
```

### 5. Committing Work
```bash
git add .
git commit -m "Your description"
git push origin dev
```
