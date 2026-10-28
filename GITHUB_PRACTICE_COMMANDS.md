# Git and GitHub Practice Commands

Replace `YOUR_USERNAME` with your GitHub username. First create an **empty** GitHub repository called `student-management`.

## 1. Initialize and push the project
```powershell
git init
git branch -M main
git status
git add .
git commit -m "Initial commit: add student management system"
git remote add origin https://github.com/YOUR_USERNAME/student-management.git
git push -u origin main
```

If Git identity is not configured:
```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

## 2. Check and update main before starting work
```powershell
git status
git remote -v
git fetch origin
git switch main
git pull --ff-only origin main
```
Commit or safely stash any uncommitted changes before switching branches.

## 3. Create a feature branch
```powershell
git switch -c feature/student-count
git branch --show-current
```

## 4. Make a code change
The project already includes a student count feature. For practice, add a new small feature or modify a message in `main.py`.

## 5. Review, commit, and push
```powershell
git diff
git status
git add main.py
git commit -m "Update student management feature"
git push -u origin feature/student-count
```

## 6. Create a Pull Request
On GitHub, open the repository and choose **Compare & pull request**. Set:
- Base: `main`
- Compare: `feature/student-count`

Write a title and description, create the PR, review it, and merge when ready.

## 7. Update local main after merge
```powershell
git switch main
git pull --ff-only origin main
git branch -d feature/student-count
```
