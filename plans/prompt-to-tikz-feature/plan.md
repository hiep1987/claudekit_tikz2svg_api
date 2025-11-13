# Implementation Plan: Prompt-to-TikZ Generation Feature

**Project:** TikZ2SVG Application
**Feature:** AI-powered TikZ code generation from Vietnamese/English prompts
**Status:** Planning Phase
**Estimated Duration:** 3-5 days
**Priority:** High - Major User Value Enhancement

---

## 📋 Executive Summary

Add AI-powered prompt-to-TikZ generation to enhance user experience. Users describe desired diagrams in natural language (Vietnamese/English), system generates TikZ code via tikz-api service, users review/edit/use generated code.

### User Flow
```
User describes diagram → AI generates TikZ → Preview code → Copy/Use → Compile to SVG
```

### Key Benefits
- **Accessibility:** Non-experts create TikZ diagrams
- **Efficiency:** Faster diagram creation
- **Learning:** Users learn TikZ syntax from examples
- **Differentiation:** Unique feature vs competitors

---

## 🎯 Feature Requirements Summary

### Functional Requirements
1. **Input:** Large textarea for Vietnamese/English prompts (4-10 lines)
2. **Generation:** Call tikz-api service at `/Users/hieplequoc/Projects/tikz-api`
3. **Authentication:** Login required (existing middleware)
4. **Rate Limiting:** 10 requests/10 minutes per user
5. **Display:** Syntax-highlighted generated code
6. **Actions:** Copy to clipboard, Use in main editor
7. **History:** Optional last 10 generations per user
8. **Error Handling:** Timeout (30s), API errors, network issues

### Non-Functional Requirements
1. **Performance:** Response time <5s (tikz-api typical)
2. **Security:** Input validation, XSS protection
3. **UX:** Loading states, clear error messages
4. **Mobile:** Responsive design
5. **Accessibility:** WCAG AAA compliance
6. **Scalability:** Handle multiple concurrent requests

---

## 🏗️ Technical Architecture

### Frontend Components
```
┌─────────────────────────────────────────┐
│   Prompt Input Section                  │
│   - Textarea (prompt)                   │
│   - Generate button                     │
│   - Loading spinner                     │
└─────────────────────────────────────────┘
           ↓ AJAX POST
┌─────────────────────────────────────────┐
│   Flask Backend                         │
│   - /api/tikz/generate endpoint         │
│   - Auth check (@login_required)        │
│   - Rate limiting (10/10min)            │
└─────────────────────────────────────────┘
           ↓ HTTP POST
┌─────────────────────────────────────────┐
│   TikZ-API Service (FastAPI)            │
│   - POST /api/v1/generate               │
│   - Gemini AI processing                │
│   - Return TikZ code + metadata         │
└─────────────────────────────────────────┘
           ↓ JSON Response
┌─────────────────────────────────────────┐
│   Generated Code Display                │
│   - CodeMirror syntax highlighting      │
│   - Copy button                         │
│   - Use in editor button                │
│   - History dropdown (optional)         │
└─────────────────────────────────────────┘
```

### Database Schema (Optional History)
```sql
CREATE TABLE tikz_generations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    prompt TEXT NOT NULL,
    generated_code TEXT NOT NULL,
    diagram_type VARCHAR(50),
    latex_packages JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### API Integration
- **tikz-api URL:** `http://localhost:8000` (dev) / configured URL (prod)
- **Endpoint:** `POST /api/v1/generate`
- **Request:**
  ```json
  {
    "prompt": "vẽ bảng biến thiên hàm số y = x^3 - 3x + 1"
  }
  ```
- **Response:**
  ```json
  {
    "tikz_code": "\\begin{tikzpicture}...",
    "type": "variation_table",
    "latex_preamble": ["amsmath", "tikz", "tkz-tab"],
    "status": "success"
  }
  ```

---

## 📦 Implementation Phases

### Phase 1: Backend Infrastructure (Day 1)
**File:** `phase-01-backend-infrastructure.md`

**Objectives:**
- Create `/api/tikz/generate` endpoint
- Implement authentication middleware
- Configure rate limiting (10/10min)
- Integrate with tikz-api service
- Optional: Database schema for history

**Deliverables:**
- Working API endpoint
- Rate limiting rules
- Error handling framework
- Database migrations (if history enabled)

**Estimated Time:** 4-6 hours

---

### Phase 2: Frontend UI (Day 1-2)
**File:** `phase-02-frontend-ui.md`

**Objectives:**
- Add HTML structure after `.input-preview-section`
- Create CSS styles (follow CSS Foundation)
- Design responsive layout (mobile-first)
- Accessibility compliance

**Deliverables:**
- HTML section in `templates/index.html`
- CSS file `static/css/prompt-to-tikz.css`
- Mobile-responsive design
- WCAG AAA compliant UI

**Estimated Time:** 4-6 hours

---

### Phase 3: JavaScript Functionality (Day 2-3)
**File:** `phase-03-javascript-functionality.md`

**Objectives:**
- AJAX request to `/api/tikz/generate`
- Loading state management
- CodeMirror integration for generated code
- Copy to clipboard functionality
- Sync generated code to main editor
- Error handling UI

**Deliverables:**
- JavaScript module `static/js/prompt-to-tikz.js`
- AJAX error handling
- Clipboard API integration
- Code editor synchronization

**Estimated Time:** 6-8 hours

---

### Phase 4: Integration & Optimization (Day 3-4)
**File:** `phase-04-integration-optimization.md`

**Objectives:**
- History feature (last 10 generations)
- Quick access dropdown
- Performance optimization
- Caching strategies
- Enhanced error messages

**Deliverables:**
- History UI component
- Database queries optimization
- Redis caching (optional)
- Comprehensive error messages

**Estimated Time:** 4-6 hours

---

### Phase 5: Testing & Deployment (Day 4-5)
**File:** `phase-05-testing-deployment.md`

**Objectives:**
- Unit tests (backend endpoints)
- Integration tests (API workflow)
- Frontend tests (JavaScript)
- User acceptance testing
- Documentation updates
- Production deployment

**Deliverables:**
- Test suite (pytest)
- Test coverage report
- Updated documentation
- Deployment checklist

**Estimated Time:** 6-8 hours

---

## 🔧 Technical Specifications

### Environment Variables
```bash
# tikz-api service configuration
TIKZ_API_URL=http://localhost:8000
TIKZ_API_TIMEOUT=30
TIKZ_API_RATE_LIMIT=10  # requests per 10 minutes
```

### Rate Limiting Configuration
```python
# app.py
RATE_LIMITS = {
    'tikz_generation': "10 per 10 minutes",  # New limit
    'api_general': "1000 per minute",         # Existing
    'api_write': "50 per minute",             # Existing
}
```

### Frontend Technologies
- **CodeMirror:** Already integrated (version from existing setup)
- **Clipboard API:** Native browser API
- **Fetch API:** AJAX requests
- **CSS Foundation:** Follow existing design system

### Backend Technologies
- **Flask:** Existing framework
- **Flask-Limiter:** Existing rate limiting
- **requests:** HTTP client for tikz-api
- **MySQL:** Existing database (optional history)

---

## ⚠️ Risk Assessment

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| tikz-api service downtime | High | Graceful error handling, timeout |
| Rate limit conflicts | Medium | Separate limiter for generation |
| Large generated code | Low | Limit prompt length (500 chars) |
| CodeMirror conflicts | Medium | Test with existing editor instance |

### UX Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Slow generation (>5s) | Medium | Loading spinner, timeout message |
| Unclear error messages | High | User-friendly Vietnamese messages |
| Mobile usability | Medium | Responsive design, touch-friendly |
| Prompt quality issues | High | Example prompts, prompt guidelines |

---

## 📊 Success Metrics

### Quantitative Metrics
- **Adoption Rate:** >30% users try generation within 1st week
- **Success Rate:** >80% generations produce valid TikZ
- **Response Time:** <5s average, <30s max
- **Error Rate:** <10% API errors
- **Mobile Usage:** >40% requests from mobile

### Qualitative Metrics
- User feedback (5-star rating)
- Feature discovery rate
- Learning curve reduction
- User retention increase

---

## 📚 Documentation Requirements

### User Documentation
1. **User Guide:** "How to use prompt-to-TikZ generation"
2. **Example Prompts:** Library of good prompts
3. **Troubleshooting:** Common issues and fixes
4. **Video Tutorial:** Screen recording demo

### Technical Documentation
1. **API Documentation:** `/api/tikz/generate` endpoint
2. **Integration Guide:** tikz-api service setup
3. **Database Schema:** tikz_generations table (if history)
4. **Rate Limiting:** Rules and bypass procedures

### Update Existing Docs
- `DOCS_CONTENT_COMPILATION.md` - Add new feature section
- `CLAUDE.md` - Update feature list
- `README.md` - Update feature highlights

---

## 🚀 Deployment Strategy

### Development Environment
1. Run tikz-api locally: `cd tikz-api && python main.py`
2. Set `TIKZ_API_URL=http://localhost:8000` in `.env`
3. Test full workflow end-to-end
4. Verify rate limiting behavior

### Staging Environment
1. Deploy tikz-api to staging VPS
2. Update `TIKZ_API_URL` to staging URL
3. Run integration tests
4. UAT with test users

### Production Environment
1. Deploy tikz-api to production VPS (same or separate server)
2. Configure production `TIKZ_API_URL`
3. Enable Redis for rate limiting
4. Monitor logs and performance
5. Gradual rollout (10% → 50% → 100%)

---

## 📝 Open Questions

### Phase 1 Decisions
- [ ] Enable history feature? (Adds complexity, provides value)
- [ ] Separate VPS for tikz-api or same server?
- [ ] Redis caching for generated code?
- [ ] Store latex_preamble in database?

### UX Decisions
- [ ] Where to place section? After input-preview or separate tab?
- [ ] Show history as dropdown or sidebar?
- [ ] Auto-compile after "Use code"?
- [ ] Show example prompts on empty state?

### Technical Decisions
- [ ] Timeout value: 30s or 60s?
- [ ] Rate limit: 10/10min or 15/10min?
- [ ] Max prompt length: 500 or 1000 chars?
- [ ] Cache TTL for generated code?

---

## 📅 Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Backend | 4-6 hours | None |
| Phase 2: Frontend UI | 4-6 hours | None (parallel with Phase 1) |
| Phase 3: JavaScript | 6-8 hours | Phase 1, Phase 2 |
| Phase 4: Integration | 4-6 hours | Phase 3 |
| Phase 5: Testing | 6-8 hours | All phases |
| **Total** | **24-34 hours** | **3-5 days** |

---

## 📞 Next Steps

1. **Review Plan:** Stakeholder approval
2. **Decide Options:** History feature? Placement? Rate limits?
3. **Setup Environment:** Ensure tikz-api running locally
4. **Start Phase 1:** Backend infrastructure
5. **Parallel Phase 2:** Frontend UI (can start simultaneously)

---

## 📂 Related Documents

- **Phase Details:** See `phase-XX-*.md` files in this directory
- **tikz-api Docs:** `/Users/hieplequoc/Projects/tikz-api/README.md`
- **Project Instructions:** `/Users/hieplequoc/Projects/claudekit_tikz2svg_api/CLAUDE.md`
- **CSS Foundation:** `CSS_FOUNDATION_MIGRATION_SUMMARY.md`

---

**Created:** 2025-11-13
**Author:** Claude Code (Planning Agent)
**Status:** Draft - Awaiting Review
