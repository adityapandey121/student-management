# Merge conflict notes

## Setup

Two branches were created from `main` (`8c65768`). Each changed the **same
line** of `main.py`, the message printed when the user chooses *6. Exit*:

| Branch | Commit | Change |
|--------|--------|--------|
| `practice/exit-summary` | `5f71870` | `Goodbye!` → `Goodbye! {len(students)} student(s) recorded this session.` |
| `practice/exit-warning` | `5d6c8be` | `Goodbye!` → `Goodbye! Note: records are kept in memory and are lost on exit.` |

```bash
git switch main
git switch -c practice/exit-summary   # edit, commit
git switch main
git switch -c practice/exit-warning   # edit the same line, commit
git push -u origin practice/exit-summary practice/exit-warning
```

## The conflict

```text
$ git switch practice/exit-summary
$ git merge practice/exit-warning
Auto-merging main.py
CONFLICT (content): Merge conflict in main.py
Automatic merge failed; fix conflicts and then commit the result.

$ git status --short
UU main.py
```

Git marked the conflicting hunk in `main.py`:

```text
<<<<<<< HEAD
            print(f"Goodbye! {len(students)} student(s) recorded this session.")
=======
            print("Goodbye! Note: records are kept in memory and are lost on exit.")
>>>>>>> practice/exit-warning
```

- `HEAD` (between `<<<<<<<` and `=======`) is the current branch,
  `practice/exit-summary`.
- Between `=======` and `>>>>>>>` is the incoming branch,
  `practice/exit-warning`.

## Resolution

The two changes do not contradict each other. One adds information (the
count), the other adds a warning. Taking only "ours" or only "theirs" would
silently drop a teammate's intended change, so the resolution **keeps both**
as two lines:

```python
        elif choice == "6":
            print(f"Goodbye! {len(students)} student(s) recorded this session.")
            print("Note: records are kept in memory and are lost on exit.")
            break
```

Steps:

```bash
# edit main.py: remove the markers, combine both changes
grep -n "<<<<<<<\|=======\|>>>>>>>" main.py      # no output = no markers left
python -m py_compile main.py                      # still valid Python
printf '1\nS1\nAlice\nMath\n6\n' | python main.py | tail -2
git add main.py
git commit                                        # merge commit 556b129
```

Verification output:

```text
Goodbye! 1 student(s) recorded this session.
Note: records are kept in memory and are lost on exit.
```

Resulting history:

```text
*   556b129 Merge branch 'practice/exit-warning' into practice/exit-summary
|\
| * 5d6c8be Warn that records are lost when exiting
* | 5f71870 Show number of students recorded when exiting
|/
* 8c65768 initial commit: add student management system files
```

## Lessons

- Conflicts happen when two branches change the same lines. Small, focused
  branches that are merged often make them rarer and smaller.
- Read both sides and understand **why** each change was made before choosing.
  The default should be to keep the intent of both.
- Always check that no markers are left, then run the code or tests before
  committing the merge.
- `git merge --abort` returns to the state before the merge if a resolution
  goes wrong.
