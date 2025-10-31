# 🔍 PHASE 1 & 2 SQL QUERIES AUDIT

## 📋 **Kiểm tra tất cả SELECT queries với DATABASE_DOCUMENTATION.md**

---

## ✅ **QUERY 1: Count Total Items (Line 1920)**

### Code:
```sql
SELECT COUNT(*) as total FROM svg_image
```

### Verification:
| Element | Expected (DATABASE_DOCUMENTATION.md) | Actual | Status |
|---------|-------------------------------------|--------|--------|
| Table name | `svg_image` | `svg_image` | ✅ CORRECT |
| Columns | N/A (using COUNT(*)) | N/A | ✅ CORRECT |

**Result:** ✅ **CORRECT**

---

## ✅ **QUERY 2: Fetch Paginated Data (Lines 1930-1951)**

### Code:
```sql
SELECT 
    s.id,
    s.filename,
    s.created_at,
    s.user_id,
    s.tikz_code,
    s.keywords,
    u.id as creator_id,
    COALESCE(u.username, 'Anonymous') as creator_username,
    COUNT(DISTINCT c.id) as comment_count,
    COUNT(DISTINCT sl.id) as like_count,
    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN svg_comments c ON s.filename = c.svg_filename
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
GROUP BY s.id, s.filename, s.created_at, s.user_id, s.tikz_code, s.keywords, u.id, u.username, user_like.id
ORDER BY s.created_at DESC
LIMIT %s OFFSET %s
```

### Verification:

#### **Table: `svg_image` (alias `s`)**
| Column | Expected | Actual | Status |
|--------|----------|--------|--------|
| `id` | ✅ EXISTS | `s.id` | ✅ CORRECT |
| `filename` | ✅ EXISTS | `s.filename` | ✅ CORRECT |
| `created_at` | ✅ EXISTS | `s.created_at` | ✅ CORRECT |
| `user_id` | ✅ EXISTS | `s.user_id` | ✅ CORRECT |
| `tikz_code` | ✅ EXISTS | `s.tikz_code` | ✅ CORRECT |
| `keywords` | ✅ EXISTS | `s.keywords` | ✅ CORRECT |

**svg_image table structure:**
```sql
CREATE TABLE `svg_image` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255),
  `tikz_code` text,
  `keywords` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
)
```
✅ **All columns CORRECT**

---

#### **Table: `user` (alias `u`)**
| Column | Expected | Actual | Status |
|--------|----------|--------|--------|
| `id` | ✅ EXISTS | `u.id` | ✅ CORRECT |
| `username` | ✅ EXISTS | `u.username` | ✅ CORRECT |

**JOIN condition:** `s.user_id = u.id`
- `svg_image.user_id` ✅ EXISTS (foreign key)
- `user.id` ✅ EXISTS (primary key)
- ✅ **JOIN CORRECT**

---

#### **Table: `svg_comments` (alias `c`)**
| Column | Expected | Actual | Status |
|--------|----------|--------|--------|
| `id` | ✅ EXISTS | `c.id` | ✅ CORRECT |
| `svg_filename` | ✅ EXISTS | `c.svg_filename` | ✅ CORRECT |

**svg_comments table structure:**
```sql
CREATE TABLE `svg_comments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `svg_filename` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  `comment_text` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_svg_filename (svg_filename)
)
```

**JOIN condition:** `s.filename = c.svg_filename`
- `svg_image.filename` ✅ EXISTS
- `svg_comments.svg_filename` ✅ EXISTS
- ✅ **JOIN CORRECT**

**Note:** This table uses `svg_filename` (VARCHAR) instead of `svg_id` (INT) for joining!

---

#### **Table: `svg_like` (alias `sl` and `user_like`)**
| Column | Expected | Actual | Status |
|--------|----------|--------|--------|
| `id` | ✅ EXISTS | `sl.id` | ✅ CORRECT |
| `svg_image_id` | ✅ EXISTS | `sl.svg_image_id` | ✅ CORRECT |
| `user_id` | ✅ EXISTS | `user_like.user_id` | ✅ CORRECT |

**svg_like table structure:**
```sql
CREATE TABLE `svg_like` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `svg_image_id` int NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_svg_unique` (`user_id`, `svg_image_id`),
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  FOREIGN KEY (`svg_image_id`) REFERENCES `svg_image` (`id`)
)
```

**JOIN conditions:**
1. `s.id = sl.svg_image_id`
   - `svg_image.id` ✅ EXISTS
   - `svg_like.svg_image_id` ✅ EXISTS (foreign key to `svg_image.id`)
   - ✅ **JOIN CORRECT**

2. `s.id = user_like.svg_image_id AND user_like.user_id = %s`
   - `svg_image.id` ✅ EXISTS
   - `svg_like.svg_image_id` ✅ EXISTS
   - `svg_like.user_id` ✅ EXISTS
   - ✅ **JOIN CORRECT**

---

## 📊 **SUMMARY**

| Query # | Purpose | Tables Used | Status |
|---------|---------|-------------|--------|
| 1 | Count total items | `svg_image` | ✅ CORRECT |
| 2 | Fetch paginated data | `svg_image`, `user`, `svg_comments`, `svg_like` | ✅ CORRECT |

---

## ✅ **ALL QUERIES VERIFIED CORRECT!**

### Key Findings:
1. ✅ All table names match DATABASE_DOCUMENTATION.md
2. ✅ All column names match database schema
3. ✅ All JOIN conditions use correct foreign keys
4. ✅ Special case handled: `svg_comments` uses `svg_filename` (not `svg_id`)
5. ✅ Special case handled: `svg_like` uses `svg_image_id` (not `svg_id`)

---

## 🎯 **LESSONS CONFIRMED:**

### ✅ **Correct Patterns:**
```sql
-- ✅ CORRECT: svg_comments join by filename
LEFT JOIN svg_comments c ON s.filename = c.svg_filename

-- ✅ CORRECT: svg_like join by svg_image_id
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
```

### ❌ **Common Mistakes (AVOIDED):**
```sql
-- ❌ WRONG: svg_comments does NOT have svg_id column
LEFT JOIN svg_comments c ON s.id = c.svg_id

-- ❌ WRONG: table name is svg_comments not comment
LEFT JOIN comment c ON s.filename = c.svg_filename

-- ❌ WRONG: svg_like does NOT have svg_id column
LEFT JOIN svg_like sl ON s.id = sl.svg_id
```

---

## 📝 **DOCUMENTATION REFERENCES:**

### svg_image (Lines 121-140)
- **Columns:** `id`, `filename`, `tikz_code`, `keywords`, `created_at`, `user_id`

### user (Lines 42-69)
- **Columns:** `id`, `username`, `email`, `avatar`, etc.

### svg_comments (Lines 498-518)
- **Columns:** `id`, `svg_filename`, `user_id`, `comment_text`, `created_at`
- **⚠️ Important:** Uses `svg_filename` (VARCHAR) not `svg_id`

### svg_like (Lines 200-210)
- **Columns:** `id`, `user_id`, `svg_image_id`, `created_at`
- **⚠️ Important:** Uses `svg_image_id` not `svg_id`

---

## 🎉 **CONCLUSION**

**All Phase 1 & 2 SQL queries are now CORRECT and match DATABASE_DOCUMENTATION.md exactly!**

**Status:** ✅ **PRODUCTION READY**

---

**Date:** October 31, 2025  
**Audited by:** AI Assistant  
**Reference:** DATABASE_DOCUMENTATION.md (Lines 1-1391)  
**Files checked:** app.py (Lines 1918-1951)

