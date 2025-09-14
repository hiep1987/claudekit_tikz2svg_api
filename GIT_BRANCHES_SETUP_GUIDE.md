# Git Branches Setup Guide for New Projects

## 🎯 Mục tiêu
Hướng dẫn setup Git branches cho dự án mới với 3 nhánh chuẩn.

## 📋 Setup nhánh tối thiểu cho dự án mới

### 1. Nhánh bắt buộc:
```bash
# Nhánh chính - bắt buộc
main (hoặc master)
```

### 2. Nhánh khuyến nghị:
```bash
# Nhánh development - khuyến nghị
develop (hoặc dev)
```

## 🌿 Setup nhánh hoàn chỉnh (3 nhánh chuẩn)

### 1. `main` - Production Branch:
- ✅ Code ổn định, đã test
- ✅ Chỉ merge từ feature branches
- ✅ Không code trực tiếp
- ✅ Dành cho production deployment

### 2. `develop` (hoặc `feature/base-template-migration`) - Development Branch:
- ✅ Nhánh chính cho development
- ✅ Code và test hàng ngày
- ✅ Merge từ feature branches nhỏ
- ✅ Làm việc chính ở đây

### 3. `backup` (hoặc `rollback/base-template-backup`) - Backup Branch:
- ✅ Backup code trước khi thay đổi lớn
- ✅ Rollback khi cần thiết
- ✅ Không code thường xuyên
- ✅ Safety net cho project

## 🚀 Git Flow chuẩn cho dự án mới

### Bước 1: Tạo nhánh chính
```bash
# Tạo nhánh main
git checkout -b main
git push origin main
```

### Bước 2: Tạo nhánh development
```bash
# Tạo nhánh develop
git checkout -b develop
git push origin develop
```

### Bước 3: Tạo nhánh backup (optional)
```bash
# Tạo nhánh backup
git checkout -b backup
git push origin backup
```

### Bước 4: Set default branch
```bash
# Làm việc chính ở develop
git checkout develop
```

## 🔄 Workflow đề xuất

### Development Workflow:
```bash
# 1. Làm việc chính ở develop
git checkout develop

# 2. Code, test, commit
# ... your development work ...

# 3. Commit changes
git add .
git commit -m "Your changes"

# 4. Push lên develop branch
git push origin develop
```

### Feature Development Workflow:
```bash
# 1. Tạo feature branch từ develop
git checkout develop
git checkout -b feature/new-feature

# 2. Code feature
# ... code your feature ...

# 3. Commit và push feature
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 4. Merge feature vào develop
git checkout develop
git merge feature/new-feature
git push origin develop

# 5. Xóa feature branch (optional)
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

### Release Workflow:
```bash
# 1. Khi code ổn định, merge vào main
git checkout main
git merge develop
git push origin main

# 2. Tạo backup trước khi release
git checkout backup
git merge main
git push origin backup
```

## 📝 Best Practices

### 1. Branch Naming Convention:
```bash
# Main branches
main                    # Production
develop                 # Development
backup                  # Backup

# Feature branches
feature/user-auth       # New features
bugfix/login-error      # Bug fixes
hotfix/security-patch   # Hot fixes
```

### 2. Commit Messages:
```bash
# Format: type(scope): description
feat(auth): add user login functionality
fix(ui): resolve button click issue
docs(readme): update installation guide
refactor(css): optimize file_card styles
```

### 3. Branch Protection Rules:
- **main**: Require pull request reviews
- **develop**: Require status checks
- **backup**: Read-only, only merge operations

## 🛡️ Safety Guidelines

### 1. Never work directly on main:
```bash
# ❌ DON'T
git checkout main
# ... code directly ...

# ✅ DO
git checkout develop
# ... code here ...
git checkout main
git merge develop
```

### 2. Always backup before major changes:
```bash
# Before major refactoring
git checkout backup
git merge develop
git push origin backup
```

### 3. Test before merging to main:
```bash
# Test on develop first
git checkout develop
# ... test thoroughly ...

# Then merge to main
git checkout main
git merge develop
```

## 🎯 Quick Setup Commands

### Tạo dự án mới với 3 nhánh:
```bash
# 1. Initialize git
git init

# 2. Create main branch
git checkout -b main
git add .
git commit -m "Initial commit"
git push origin main

# 3. Create develop branch
git checkout -b develop
git push origin develop

# 4. Create backup branch
git checkout -b backup
git push origin backup

# 5. Switch to develop for work
git checkout develop
```

### Verify setup:
```bash
# Check all branches
git branch -a

# Should show:
# * develop
#   main
#   backup
#   remotes/origin/develop
#   remotes/origin/main
#   remotes/origin/backup
```

## 📊 Branch Strategy Summary

| Branch | Purpose | When to use | Who can push |
|--------|---------|-------------|--------------|
| `main` | Production | Stable releases | After review |
| `develop` | Development | Daily work | Developers |
| `backup` | Safety net | Before major changes | Developers |

## 🔧 Advanced Setup (Optional)

### 1. Git Hooks:
```bash
# Pre-commit hook to run tests
#!/bin/sh
npm test
```

### 2. Branch Protection:
- Enable branch protection on GitHub
- Require pull request reviews
- Require status checks

### 3. Automated Deployment:
- `main` → Production
- `develop` → Staging
- `backup` → Archive

## ✅ Checklist for New Project

- [ ] Create `main` branch
- [ ] Create `develop` branch  
- [ ] Create `backup` branch
- [ ] Set `develop` as default working branch
- [ ] Configure branch protection rules
- [ ] Set up CI/CD pipeline
- [ ] Document workflow for team
- [ ] Create feature branch template

---

**Lưu ý: File này nên được lưu trong thư mục templates hoặc docs để sử dụng cho các dự án mới trong tương lai.**
