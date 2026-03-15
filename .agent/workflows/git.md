---
description: Manage the Git workflow for ContextDesk - commits, branches, and pushes
---

// turbo-all

## Branch Strategy

- `main`: stable, production-ready code. Only receives merges from `develop`.
- `develop`: active integration branch. Work happens here.
- `feat/<name>`: optional feature branches off `develop`.

## 1. Initial Setup (run once)

```
git init
git remote add origin https://github.com/jonathangonzalezlpz/context-desk.git
```

## 2. First commit and push to main

```
git add .
git commit -m "feat: initial project scaffold - ContextDesk core architecture"
git branch -M main
git push -u origin main
```

## 3. Create develop branch

```
git checkout -b develop
git push -u origin develop
```

## 4. Commit work on develop

For every chunk of work completed, run:

```
git add .
git commit -m "<type>: <short description>"
git push origin develop
```

Commit types:
- `feat`: new feature
- `fix`: bug fix
- `chore`: tooling, configuration, scaffolding
- `refactor`: code refactor without logic change
- `test`: tests added or modified
- `docs`: documentation only

## 5. Create a feature branch

```
git checkout develop
git checkout -b feat/<feature-name>
```

## 6. Merge feature into develop

```
git checkout develop
git merge --no-ff feat/<feature-name>
git push origin develop
```

## 7. Merge develop into main (release)

```
git checkout main
git merge --no-ff develop
git push origin main
git checkout develop
```
