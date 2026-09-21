# GitHub-ready repository

This ZIP already contains an initialized `.git` directory and full feature-wise commit history. The repository does **not** contain a GitHub remote because a remote URL belongs to your GitHub account/organization.

After extracting:

```bash
git status
git log --oneline --reverse
git branch
```

The packaged branch is `main`.

To publish it to a repository you create on GitHub:

```bash
git remote add origin https://github.com/YOUR_USERNAME/setustock-ncr.git
git push -u origin main
```

If you use SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/setustock-ncr.git
git push -u origin main
```

A GitHub Actions workflow is included at `.github/workflows/ci.yml`. It runs Django checks/tests/migrations and builds the React frontend on pushes and pull requests.
