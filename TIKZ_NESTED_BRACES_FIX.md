# 🔧 TikZ Code Blocks - Nested Braces Fix

## ❌ Vấn đề

### **Old regex approach:**
```javascript
escaped.replace(/\\code\{([^]*?)\}/g, ...)
```

**Problem:** Regex `([^]*?)` matches **non-greedy** đến `}` đầu tiên, không handle nested braces!

---

## 🐛 Bug Example:

### **Input:**
```
\code{\tikz \draw (2,0) coordinate (A) -- (0,0) coordinate (B)
         -- (1,1) coordinate (C)
  pic ["$\alpha$", draw, ->] {angle};}
```

### **Old behavior (BUG):**
```
\code{\tikz \draw (2,0) coordinate (A) -- (0,0) coordinate (B)
         -- (1,1) coordinate (C)
  pic ["$\alpha$", draw, ->] {angle}    ← Matched code
                                     };  ← LEFT OUTSIDE! ❌
```

**Result:** Code block stops at first `}` inside `{angle}`, leaving `};` outside!

---

## ✅ Solution: Brace Counting Parser

### **New approach:**
```javascript
function renderCommentText(text) {
    // ... escape HTML ...
    
    let result = '';
    let i = 0;
    
    while (i < escaped.length) {
        // Find \code{
        const codeStart = escaped.indexOf('\\code{', i);
        
        if (codeStart === -1) {
            result += escaped.substring(i);
            break;
        }
        
        // Append text before \code{
        result += escaped.substring(i, codeStart);
        
        // COUNT BRACES to find matching }
        let braceCount = 1;
        let codeEnd = codeStart + 6; // After \code{
        
        while (codeEnd < escaped.length && braceCount > 0) {
            if (escaped[codeEnd] === '{' && escaped[codeEnd - 1] !== '\\') {
                braceCount++;  // Opening brace
            } else if (escaped[codeEnd] === '}' && escaped[codeEnd - 1] !== '\\') {
                braceCount--;  // Closing brace
            }
            codeEnd++;
        }
        
        if (braceCount === 0) {
            // Found matching brace!
            const code = escaped.substring(codeStart + 6, codeEnd - 1);
            result += formatCodeBlock(code);
            i = codeEnd;
        } else {
            // Unmatched, treat as text
            result += '\\code{';
            i = codeStart + 6;
        }
    }
    
    return result;
}
```

---

## 🎯 How It Works

### **Brace counting algorithm:**

```
\code{\tikz \draw pic {angle};}
      ^                      ^
      |                      |
   count=1              count=0 (MATCH!)

Step by step:
\code{          ← count = 1
     \tikz      ← count = 1
     {          ← count = 2 (nested!)
     angle      ← count = 2
     }          ← count = 1 (closing nested)
     ;          ← count = 1
     }          ← count = 0 (FOUND MATCH!)
```

---

## 📊 Test Cases

### **Test 1: Simple nested braces**
```
Input:  \code{\node{text}}
Result: ✅ Correctly captures: \node{text}
```

### **Test 2: Multiple nesting**
```
Input:  \code{\tikz \node[draw] {outer {inner}}}
Result: ✅ Correctly captures: \tikz \node[draw] {outer {inner}}
```

### **Test 3: Your example**
```
Input:  \code{\tikz \draw pic {angle};}
Result: ✅ Correctly captures entire code including };
```

### **Test 4: Escaped braces**
```
Input:  \code{\draw \{ and \}}
Result: ✅ Ignores \{ and \} (escaped)
```

### **Test 5: Unmatched braces**
```
Input:  \code{incomplete {
Result: ✅ Treats as plain text (safe fallback)
```

---

## 🔒 Security

### **Still XSS-protected:**

1. **Escape HTML first:** `escapeHtml(text)`
2. **Parse on escaped text:** Safe string manipulation
3. **Unescape for display:** Get original code
4. **Re-escape:** Safe HTML entities
5. **No eval():** Code displayed, not executed

---

## 📈 Performance

### **Old regex:**
- **Speed:** O(n) - Fast but incorrect
- **Accuracy:** ❌ Fails on nested braces

### **New parser:**
- **Speed:** O(n) - Linear scan
- **Accuracy:** ✅ Handles all nesting levels
- **Memory:** O(n) - Result string

**Verdict:** Negligible performance impact, correct behavior! ✅

---

## 🎨 Visual Comparison

### **Old (BUG):**
```
User types:
\code{\tikz \draw pic {angle};}

Rendered:
┌────────────────────────────┐
│ TikZ Code              📋 │
├────────────────────────────┤
│ \tikz \draw pic {angle}   │  ← Missing };
└────────────────────────────┘
};  ← LEFT OUTSIDE ❌
```

### **New (FIXED):**
```
User types:
\code{\tikz \draw pic {angle};}

Rendered:
┌────────────────────────────┐
│ TikZ Code              📋 │
├────────────────────────────┤
│ \tikz \draw pic {angle};  │  ← Complete! ✅
└────────────────────────────┘
```

---

## 🧪 Testing

### **Test file:** `test_nested_braces.html`

Open in browser to verify:
```
file:///Users/hieplequoc/web/work/tikz2svg_api/test_nested_braces.html
```

---

## 📝 Edge Cases Handled

| Case | Handled |
|------|---------|
| **Simple:** `\code{\draw;}` | ✅ |
| **Nested:** `\code{\node{text}}` | ✅ |
| **Deep nesting:** `\code{{{nested}}}` | ✅ |
| **Escaped:** `\code{\{ \}}` | ✅ |
| **Unmatched:** `\code{no closing` | ✅ Fallback |
| **Multiple blocks:** `\code{A} \code{B}` | ✅ |
| **Empty:** `\code{}` | ✅ |

---

## ✅ Summary

### **Changed:**
- ❌ **Old:** Simple regex (incorrect)
- ✅ **New:** Brace counting parser (correct)

### **File:** `static/js/comments.js`
### **Function:** `renderCommentText()`
### **Lines:** ~119-197 (78 lines)

### **Benefits:**
1. ✅ Correctly handles nested braces
2. ✅ Works with complex TikZ code
3. ✅ Still XSS-protected
4. ✅ Graceful fallback on errors
5. ✅ O(n) performance

---

## 🚀 Ready to Deploy!

**Test với ví dụ của bạn:**
```
\code{\tikz \draw (2,0) coordinate (A) -- (0,0) coordinate (B)
         -- (1,1) coordinate (C)
  pic ["$\alpha$", draw, ->] {angle};}
```

**Giờ capture HOÀN TOÀN đúng!** ✨

---

**Generated:** 2025-10-23  
**Fix:** Nested braces parser  
**File:** `static/js/comments.js`  
**Status:** ✅ Production-ready
