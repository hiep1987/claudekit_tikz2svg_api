# ✅ CSS Development Checklist - TikZ to SVG

## 🚫 **CRITICAL: NO !important Rule**

**Before writing any CSS, remember:**
- ❌ **NEVER** use `!important`
- ✅ **ALWAYS** use higher specificity instead

## 📋 **Pre-Development Checklist**

### **1. Bootstrap Override Strategy**
- [ ] Identify what Bootstrap styles need to be overridden
- [ ] Calculate required specificity level
- [ ] Use `.tikz-app` scoping + IDs for higher specificity
- [ ] Test in browser DevTools

### **2. Specificity Calculation**
```css
/* Instead of this: */
.menu a { text-decoration: none !important; }

/* Use this pattern: */
.tikz-app #container .menu a { text-decoration: none; }
```

### **3. Common Bootstrap Overrides**

**Links:**
```css
.tikz-app #component-container .link-element a {
    text-decoration: none;
    color: var(--your-color);
}
```

**Lists:**
```css
.tikz-app #list-container .list-component {
    list-style: none;
    padding: 0;
    margin: 0;
}
```

**Buttons:**
```css
.tikz-app .button-container .custom-btn {
    background: var(--button-bg);
    border: none;
}
```

## 🔍 **Code Review Checklist**

### **Before Commit:**
- [ ] No `!important` declarations found
- [ ] All styles scoped with `.tikz-app`
- [ ] Using foundation variables where possible
- [ ] Higher specificity used for Bootstrap overrides
- [ ] Tested in browser DevTools
- [ ] No CSS conflicts with existing styles

### **Testing Commands:**
```bash
# Check for !important usage
grep -rn "!important" static/css/

# Check for unscoped styles
grep -rn "^[^.#].*{" static/css/

# Verify foundation variables usage
grep -rn "var(--" static/css/
```

## 🛠️ **Debugging Tools**

### **Browser DevTools:**
1. **Inspect Element** → **Computed** tab
2. Check which styles are being overridden
3. Look at specificity values
4. Test new selectors in Console

### **Specificity Calculator:**
- Use: https://specificity.keegan.st/
- Input your selector to see specificity score
- Compare with Bootstrap selectors

## 📖 **Quick Reference**

### **Specificity Values:**
- Inline styles: `1000`
- IDs: `100` 
- Classes: `10`
- Elements: `1`

### **Common Bootstrap Specificity:**
- `a`: 1
- `.btn`: 10
- `#navbar .nav-link`: 110
- `.navbar .navbar-nav .nav-link`: 30

### **Our Override Pattern:**
```css
/* Specificity: 221 */
.tikz-app #container #sub-container .component element
```

## 🎯 **Project-Specific Patterns**

### **Navigation Menu:**
```css
.tikz-app #scrollable-menu #scrollable-menu-list .menu-item a {
    /* Specificity: 221 - Overrides Bootstrap links */
}
```

### **File Cards:**
```css
.tikz-app .files-section .file-card .card-element {
    /* Specificity: 40 - Usually sufficient */
}
```

### **Buttons:**
```css
.tikz-app .button-container .custom-btn-class {
    /* Specificity: 30 - Good for button overrides */
}
```

---

**Remember: Clean CSS is predictable CSS. No shortcuts with `!important`!** 🚀
