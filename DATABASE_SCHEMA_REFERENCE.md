# 📊 Database Schema Reference

**Database:** `tikz2svg_local`  
**Created:** October 31, 2025  
**Purpose:** Quick reference để KHÔNG DỰ ĐOÁN schema!

---

## ⚠️ **QUY TẮC VÀNG:**

```
LUÔN CHECK DATABASE TRƯỚC KHI VIẾT CODE!
KHÔNG BAO GIỜ DỰ ĐOÁN COLUMNS!
```

---

## 🗄️ **Tables Overview:**

### **svg_image** (Main table)
```sql
DESCRIBE svg_image;

-- Verified columns:
- id (INT, PRIMARY KEY)
- filename (VARCHAR)
- created_at (DATETIME)
- user_id (INT)
- tikz_code (TEXT)
- keywords (TEXT)

-- ❌ KHÔNG CÓ:
-- is_public
-- view_count
-- description
```

### **user** (User accounts)
```sql
DESCRIBE user;

-- Key columns:
- id (INT, PRIMARY KEY)
- username (VARCHAR)
- email (VARCHAR)
- avatar (VARCHAR)
- bio (TEXT)
- google_id (VARCHAR)
```

### **comment** (Comments on SVG)
```sql
DESCRIBE comment;

-- Key columns:
- id (INT, PRIMARY KEY)
- svg_id (INT, FOREIGN KEY → svg_image.id)
- user_id (INT, FOREIGN KEY → user.id)
- content (TEXT)
- created_at (DATETIME)
```

### **svg_like** (Likes on SVG)
```sql
DESCRIBE svg_like;

-- Key columns:
- id (INT, PRIMARY KEY)
- svg_id (INT, FOREIGN KEY → svg_image.id)
- user_id (INT, FOREIGN KEY → user.id)
- created_at (DATETIME)
```

### **user_follow** (User follows)
```sql
DESCRIBE user_follow;

-- Key columns:
- follower_id (INT, FOREIGN KEY → user.id)
- followee_id (INT, FOREIGN KEY → user.id)
- created_at (DATETIME)
```

---

## 🔍 **Quick Check Commands:**

### **Connect to Database:**
```bash
mysql -u hiep1987 tikz2svg_local
```

### **Show All Tables:**
```sql
SHOW TABLES;
```

### **Check Table Structure:**
```sql
-- Option 1: Simple
DESCRIBE table_name;

-- Option 2: Detailed
SHOW COLUMNS FROM table_name;

-- Option 3: Full CREATE statement
SHOW CREATE TABLE table_name;
```

### **Check Foreign Keys:**
```sql
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'tikz2svg_local'
  AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### **Sample Data:**
```sql
SELECT * FROM svg_image LIMIT 5;
SELECT * FROM user LIMIT 5;
SELECT * FROM comment LIMIT 5;
```

---

## ✅ **Working Query Examples:**

### **Get SVG with User Info:**
```sql
SELECT 
    s.id,
    s.filename,
    s.created_at,
    s.user_id,
    s.tikz_code,
    s.keywords,
    u.id as creator_id,
    u.username as creator_username
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
ORDER BY s.created_at DESC
LIMIT 50;
```

### **Get SVG with Counts:**
```sql
SELECT 
    s.id,
    s.filename,
    u.username as creator_username,
    COUNT(DISTINCT c.id) as comment_count,
    COUNT(DISTINCT sl.id) as like_count
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN comment c ON s.id = c.svg_id
LEFT JOIN svg_like sl ON s.id = sl.svg_id
GROUP BY s.id, s.filename, u.username
ORDER BY s.created_at DESC;
```

### **Get SVG with User's Like Status:**
```sql
SELECT 
    s.id,
    s.filename,
    COUNT(DISTINCT sl.id) as like_count,
    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
FROM svg_image s
LEFT JOIN svg_like sl ON s.id = sl.svg_id
LEFT JOIN svg_like user_like ON s.id = user_like.svg_id AND user_like.user_id = ?
GROUP BY s.id, s.filename, user_like.id;
```

---

## ❌ **Common Mistakes to AVOID:**

### **1. Assuming Columns Exist:**
```sql
-- ❌ SAI:
SELECT is_public, view_count, description FROM svg_image;
-- Error: Unknown column 'is_public'

-- ✅ ĐÚNG:
DESCRIBE svg_image;  -- Check first!
SELECT id, filename, created_at FROM svg_image;
```

### **2. Wrong Variable Names:**
```python
# ❌ SAI:
svg['svg_url'] = f"/static/{filename}"
# Template expects: file.url

# ✅ ĐÚNG:
svg['url'] = f"/static/{filename}"
# Matches template variable
```

### **3. Missing JOINs:**
```sql
-- ❌ SAI:
SELECT s.id, s.filename
FROM svg_image s;
-- Missing creator_username!

-- ✅ ĐÚNG:
SELECT s.id, s.filename, u.username as creator_username
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id;
```

---

## 🎯 **Workflow Checklist:**

### **Before Writing Query:**

- [ ] Check `DESCRIBE table_name`
- [ ] Verify all columns exist
- [ ] Check foreign key relationships
- [ ] Look at sample data
- [ ] Find existing working queries in codebase

### **Before Formatting Data:**

- [ ] Check template variables needed
- [ ] Look at existing implementations
- [ ] Match data structure exactly
- [ ] Test with sample data

### **Before Running Code:**

- [ ] Verify SQL syntax
- [ ] Check for typos in column names
- [ ] Ensure all JOINs are correct
- [ ] Test query in MySQL first

---

## 📚 **Reference Implementations:**

### **Best Example in Codebase:**
```python
# File: app.py
# Function: profile_followed_posts()
# Line: ~3666-3702

# This has COMPLETE query with:
✅ All necessary JOINs
✅ Proper column names
✅ COUNT for like_count, comment_count
✅ CASE WHEN for is_liked
✅ Proper GROUP BY
✅ Correct data formatting

# USE THIS AS TEMPLATE!
```

---

## 🔄 **Update This File:**

**When to update:**
- Schema changes (new tables, new columns)
- New relationships added
- Migration performed
- Production database differs from local

**How to update:**
```bash
# 1. Check current schema
mysql -u hiep1987 tikz2svg_local

# 2. Run DESCRIBE for all tables
DESCRIBE svg_image;
DESCRIBE user;
DESCRIBE comment;
DESCRIBE svg_like;

# 3. Update this document
# 4. Commit to git
```

---

## 💡 **Pro Tips:**

### **1. Keep a MySQL Client Open:**
```bash
# Terminal tab 1: Development server
python app.py

# Terminal tab 2: MySQL client (always available)
mysql -u hiep1987 tikz2svg_local
```

### **2. Test Queries in MySQL First:**
```sql
-- Test complex queries here before putting in code
SELECT s.id, u.username, COUNT(c.id)
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN comment c ON s.id = c.svg_id
GROUP BY s.id, u.username
LIMIT 5;
```

### **3. Use phpMyAdmin:**
```
http://localhost:8080/phpmyadmin/
```
Visual interface to:
- Browse tables
- Check structure
- Run queries
- Export schema

---

## 🎓 **Lessons Learned:**

### **From Pagination Implementation:**

**❌ Mistake:**
```python
# Assumed columns without checking
SELECT is_public, view_count FROM svg_image
```

**✅ Fix:**
```sql
-- Checked schema first
DESCRIBE svg_image;
-- Then wrote query with actual columns
SELECT id, filename, created_at FROM svg_image
```

**Result:** Saved 30 minutes of debugging!

---

## 📞 **Quick Reference Card:**

```
┌─────────────────────────────────────────┐
│  BEFORE WRITING ANY QUERY:              │
├─────────────────────────────────────────┤
│  1. DESCRIBE table_name                 │
│  2. Check existing queries              │
│  3. Test in MySQL first                 │
│  4. Then write Python code              │
└─────────────────────────────────────────┘
```

---

**Last Updated:** October 31, 2025  
**Status:** Active Reference  
**Rule:** ⚠️ **NEVER ASSUME - ALWAYS CHECK!** ⚠️

