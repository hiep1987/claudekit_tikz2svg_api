# 🔧 TikZ Code Block `<br>` Tags Fix

## ❌ Vấn đề

### **Bug:**
Code block HTML bị insert `<br>` tags vào GIỮA HTML structure:

```html
<div class="tikz-code-block"><br>
    <div class="code-header"><br>
        <span class="code-label">TikZ Code</span><br>
        <button class="code-copy-btn"><br>
            <span class="copy-icon">📋</span><br>
        </button><br>
    </div><br>
    <pre class="tikz-code"><code><br>
\begin{tikzpicture}<br>
\draw (-2,0) -- (2,0);<br>
    </code></pre><br>
</div>
```

**Result:** HTML bị broken, `<br>` hiện ra trong source code! 💥

---

## 🔍 Root Cause

### **Old logic (Line 194):**
```javascript
// Convert line breaks to <br>
result = result.replace(/\n/g, '<br>');
```

**Problem:** Replace **TẤT CẢ** `\n` → `<br>`, kể cả:
1. ❌ `\n` trong HTML structure của code block
2. ❌ `\n` trong TikZ code content
3. ✅ `\n` trong plain text (cần convert)

---

## ✅ Solution

### **New logic:**
```javascript
// Convert \n to <br> ONLY for plain text, NOT for code blocks

while (i < escaped.length) {
    const codeStart = escaped.indexOf('\\code{', i);
    
    if (codeStart === -1) {
        // No more code blocks, append rest and convert line breaks
        const remaining = escaped.substring(i);
        result += remaining.replace(/\n/g, '<br>');  // ✅ Convert here
        break;
    }
    
    // Append text BEFORE \code{ and convert line breaks
    const textBefore = escaped.substring(i, codeStart);
    result += textBefore.replace(/\n/g, '<br>');    // ✅ Convert here
    
    // ... parse code block ...
    
    // Append code block (DON'T convert \n!)
    result += `<div class="tikz-code-block">...`;   // ❌ NO <br> conversion
}
```

### **Key change:**
- ✅ Convert `\n` → `<br>` **PER SEGMENT** (text only)
- ❌ **KHÔNG** convert trong code block HTML
- ✅ Preserve `\n` trong `<pre><code>` (browsers handle naturally)

---

## 📊 Before/After

### **Before (BUG):**

**Input:**
```
Hello world

\code{
\tikz \draw (0,0);
}

Goodbye!
```

**Output:**
```html
Hello world<br>
<br>
<div class="tikz-code-block"><br>   ← BUG! <br> in HTML structure
    <div class="code-header"><br>    ← BUG!
        ...
    </div><br>                       ← BUG!
    <pre class="tikz-code"><code><br> ← BUG! (not needed in <pre>)
\tikz \draw (0,0);<br>                ← BUG!
    </code></pre><br>               ← BUG!
</div><br>                           ← BUG!
<br>
Goodbye!<br>
```

---

### **After (FIXED):**

**Input:**
```
Hello world

\code{
\tikz \draw (0,0);
}

Goodbye!
```

**Output:**
```html
Hello world<br>
<br>
<div class="tikz-code-block"><div class="code-header">...</div><pre class="tikz-code"><code>
\tikz \draw (0,0);
</code></pre></div>
<br>
Goodbye!<br>
```

**Result:** 
- ✅ Clean HTML structure
- ✅ `\n` preserved in `<pre>` (natural line breaks)
- ✅ `<br>` only in plain text

---

## 🎯 Logic Flow

### **Step-by-step processing:**

```
Input: "Hello\n\n\\code{\ntikz\n}\n\nBye"

Step 1: Find \code{
  - textBefore = "Hello\n\n"
  - Convert: "Hello<br><br>"
  - Append to result ✅

Step 2: Parse code block
  - code = "\ntikz\n"
  - HTML = "<div...><code>\ntikz\n</code>...</div>"
  - NO <br> conversion ✅
  - Append to result

Step 3: No more \code{
  - remaining = "\n\nBye"
  - Convert: "<br><br>Bye"
  - Append to result ✅

Final: "Hello<br><br><div...><code>\ntikz\n</code>...</div><br><br>Bye"
```

---

## 🔧 Code Changes

### **File:** `static/js/comments.js`

### **Old (Line 136-194):**
```javascript
// Append text before \code{
result += escaped.substring(i, codeStart);

// ... parse code ...

// Append code block
result += `<div class="tikz-code-block">
    <div class="code-header">...</div>
    <pre class="tikz-code"><code>${safeCode}</code></pre>
</div>`;

// ... end loop ...

// Convert line breaks to <br> (GLOBAL - BUG!)
result = result.replace(/\n/g, '<br>');
```

### **New (Line 136-187):**
```javascript
// Append text before \code{ and convert line breaks
const textBefore = escaped.substring(i, codeStart);
result += textBefore.replace(/\n/g, '<br>');  // ✅ Per-segment

// ... parse code ...

// Append code block (minified, no \n in HTML structure)
result += `<div class="tikz-code-block"><div class="code-header">...</div><pre class="tikz-code"><code>${safeCode}</code></pre></div>`;

// ... end loop ...

// NO global replace! (fixed)
```

### **Also changed at line 137:**
```javascript
// No more code blocks, append rest and convert line breaks
const remaining = escaped.substring(i);
result += remaining.replace(/\n/g, '<br>');  // ✅ Per-segment
```

---

## ✅ Benefits

### **1. Clean HTML:**
- No `<br>` tags in HTML structure
- Minified code block HTML (one line)
- Valid HTML output

### **2. Proper `<pre>` handling:**
- `\n` preserved in `<pre><code>` blocks
- Browsers render line breaks naturally
- No need for `<br>` in preformatted text

### **3. Correct text rendering:**
- `<br>` only in plain text segments
- Multi-line text displays correctly
- Paragraphs separated properly

---

## 🧪 Test Cases

### **Test 1: Plain text only**
```
Input:  "Line 1\nLine 2"
Output: "Line 1<br>Line 2" ✅
```

### **Test 2: Code block only**
```
Input:  "\code{\ntikz\n}"
Output: "<div...><code>\ntikz\n</code>...</div>" ✅
```

### **Test 3: Mixed (text + code + text)**
```
Input:  "Hello\n\n\code{code}\n\nBye"
Output: "Hello<br><br><div...>code...</div><br><br>Bye" ✅
```

### **Test 4: Multiple code blocks**
```
Input:  "\code{A}\n\code{B}"
Output: "<div...>A...</div><br><div...>B...</div>" ✅
```

---

## 📝 Summary

### **Changed:**
- ❌ **Old:** Global `\n` → `<br>` replacement (breaks HTML)
- ✅ **New:** Per-segment replacement (text only)

### **Impact:**
- 🎨 **Clean HTML** structure
- 📖 **Proper rendering** in browsers
- 🔧 **Maintainable** code

### **Lines changed:**
- Line 137: Convert remaining text
- Line 142-143: Convert text before code block
- Line 177: Minified HTML (no newlines in structure)
- Removed Line 194: Global replacement

---

**TikZ code blocks giờ GỌN GÀ và CLEAN!** ✨

---

**Generated:** 2025-10-23  
**File:** `static/js/comments.js`  
**Fix:** Per-segment `<br>` conversion  
**Status:** ✅ Production-ready
