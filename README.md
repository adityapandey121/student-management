# Student Management System

A beginner-friendly Python command-line project for practicing Git and GitHub.

## Features
- Add students
- View all students
- Search by student ID
- Delete students
- Count students

## Requirements
- Python 3.10 or newer
- Git
- A GitHub account

## Run the project
```bash
python main.py
```

## GitHub practice workflow
1. Create an empty GitHub repository named `student-management`.
2. Initialize and push this project to `main`.
3. Create a feature branch: `git switch -c feature/student-count`.
4. Make a change, then run `git diff` and `git status`.
5. Commit: `git add main.py && git commit -m "Add student count feature"`.
6. Push: `git push -u origin feature/student-count`.
7. Open a Pull Request on GitHub from `feature/student-count` into `main`.
8. Review and merge the PR, then update local `main`.

## Note
This demo stores data in memory, so student records reset when the program exits.
