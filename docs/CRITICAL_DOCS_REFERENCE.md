# Critical Documentation References

This file contains detailed references to critical documentation files that Claude must read before working on the codebase.

## Essential Reading Order

Before starting any development work, read these files in the following order:

### 1. DATABASE_DOCUMENTATION.md
- **19 Database Tables** with complete schema
- Essential queries and relationships
- Real-time statistics and monitoring data
- Read before: Any database-related feature, schema changes, SQL queries

### 2. API_ENDPOINTS_DOCUMENTATION.md
- **80+ REST API Endpoints** with examples
- Rate limiting rules and security features
- 11 endpoint categories covering all functionality
- Read before: API implementation, frontend integration, authentication

### 3. DOCS_CONTENT_COMPILATION.md
- **437+ Documentation Sections** for user features
- Complete user workflows and feature requirements
- Critical user limits and constraints
- Read before: UI/UX implementation, user-facing features, workflow planning

### 4. WORKFLOW_GUIDE.md
- **VPS Deployment Configuration** with Redis setup
- Troubleshooting common production issues
- Symbolic links and static file configuration
- Read before: Production deployment, environment setup, issue resolution

## Quick Verification Commands

```bash
# Confirm file existence and size
ls -lh DATABASE_DOCUMENTATION.md API_ENDPOINTS_DOCUMENTATION.md DOCS_CONTENT_COMPILATION.md WORKFLOW_GUIDE.md

# Count lines to verify completeness
wc -l DATABASE_DOCUMENTATION.md    # Should be ~1390 lines
wc -l API_ENDPOINTS_DOCUMENTATION.md  # Should be ~1700 lines
wc -l DOCS_CONTENT_COMPILATION.md     # Should be ~1357 lines
wc -l WORKFLOW_GUIDE.md                # Should be ~517 lines
```

## Cross-Reference Implementation Patterns

When implementing features, follow this pattern:

1. **Planning Phase:**
   - Read `DOCS_CONTENT_COMPILATION.md` → User requirements
   - Read `API_ENDPOINTS_DOCUMENTATION.md` → API design
   - Read `DATABASE_DOCUMENTATION.md` → Data schema

2. **Development Phase:**
   - Reference `DATABASE_DOCUMENTATION.md` → SQL queries
   - Reference `API_ENDPOINTS_DOCUMENTATION.md` → Endpoints
   - Reference `WORKFLOW_GUIDE.md` → Production config

3. **Testing Phase:**
   - Verify against API documentation
   - Verify data integrity
   - Test user workflows

4. **Deployment Phase:**
   - Follow workflow guide checklist
   - Verify all configurations

## Rate Limiting Rules (Reference)

| Endpoint Category | Limit | Window | Applies To |
|------------------|-------|--------|------------|
| General API | 1000 requests | 1 minute | All endpoints |
| Package Requests | 3 requests | 1 hour | Per user |
| Email Verification | 5 emails | 1 hour | Per user |
| Comments | 20 comments | 1 hour | Per user |
| Compilation | 5 concurrent | - | Global |
| File Upload | 10 files | 1 day | Per user |

## Security Features (Reference)

- ✅ 25+ dangerous pattern detection for LaTeX
- ✅ Package whitelist enforcement (50+ packages)
- ✅ Resource limits: 45s timeout, 300MB memory, 5 concurrent
- ✅ Redis-based rate limiting with ProxyFix
- ✅ XSS protection via HTML escaping

## User Limits (Reference)

- SVG files: Max **10MB** per file, **10 files/day**
- Comments: Max **5000 characters**, rate limit **20/hour**
- Images: Max **60MP** (60,000,000 pixels), max **2000 DPI**
- Package requests: **3 requests/hour**