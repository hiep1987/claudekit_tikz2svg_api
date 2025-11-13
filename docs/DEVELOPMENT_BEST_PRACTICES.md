# Development Best Practices

## Feature Development

### When Adding New Features
1. **Read documentation first:** Check `DOCS_CONTENT_COMPILATION.md` to understand system
2. **Follow existing patterns:** Use existing code patterns and conventions
3. **Security first:** Validate input, escape output, implement rate limiting
4. **Update documentation:** Update relevant .md files
5. **Test thoroughly:** Unit tests, integration tests, manual testing
6. **CSS Foundation:** Use design system variables, no hardcoding
7. **Accessibility:** Ensure WCAG AAA compliance
8. **Mobile-first:** Test on mobile before desktop

### When Fixing Bugs
1. **Reproduce bug:** Confirm bug on local environment
2. **Check related code:** Find potentially affected code
3. **Fix root cause:** Fix the root cause, not just symptoms
4. **Test regressions:** Ensure fix doesn't cause new errors
5. **Update tests:** Add test cases for fixed bugs
6. **Document fix:** Record in commit message and changelog

## System-Specific Guidelines

### TikZ Processing
1. **Test with multiple cases:** Simple, complex, edge cases
2. **Handle errors gracefully:** Provide proper error messages to users
3. **Timeout protection:** Don't let compilation run indefinitely
4. **Package whitelist:** Only allow approved packages
5. **Security validation:** Validate all user-provided LaTeX code
6. **Memory management:** Clean up temp files after compilation

### Comments System
1. **XSS protection:** Always escape HTML, double-escape code blocks
2. **MathJax testing:** Test with complex LaTeX formulas
3. **Nested braces:** Test TikZ code with multiple levels of {}
4. **Character limits:** Enforce 5000 char limit
5. **Rate limiting:** Prevent comment spam
6. **Real-time preview:** Ensure MathJax renders correctly

### CSS Development
1. **Foundation first:** Check master-variables.css first
2. **No hardcoding:** Use var(--variable-name) always
3. **Scoping:** Prefix with .tikz-app
4. **Responsive:** Test breakpoints (mobile, tablet, desktop)
5. **Accessibility:** Check contrast ratios
6. **Browser testing:** Chrome, Firefox, Safari, Edge

## Deployment Process

### Pre-Deployment Checklist
1. **Backup database:** Always backup before deploying
2. **Test staging:** Deploy to staging environment first
3. **Check logs:** Monitor error logs after deployment
4. **Performance:** Check page load times, API response times
5. **Redis:** Ensure Redis running for rate limiting
6. **Static files:** Verify symbolic links working
7. **SSL:** Ensure HTTPS certificates valid

## Code Standards

### Python (PEP 8)
- Use descriptive variable names
- Proper function documentation
- Error handling with try-catch blocks
- Parameterized queries for database operations

### JavaScript (ES6+)
- Proper error handling
- Use async/await for API calls
- Debouncing for real-time features
- Module-based organization

### HTML/CSS
- Semantic HTML structure
- Responsive design principles
- CSS Foundation variables
- Accessibility compliance

### Database
- Consistent naming conventions
- Proper indexing for performance
- Foreign key relationships
- Migration scripts for schema changes

## Security Requirements

### Input Validation
- Sanitize all user input
- Validate file types and sizes
- Implement CSRF protection
- Rate limiting for sensitive endpoints

### Data Protection
- Environment variables for sensitive data
- No hardcoded credentials
- Secure password handling
- XSS prevention

### API Security
- Authentication requirements
- Authorization checks
- Rate limiting implementation
- Request/response logging

## Performance Optimization

### Database
- Query optimization
- Connection pooling
- Index utilization
- Query caching

### Frontend
- Lazy loading
- Image optimization
- CSS/JS minification
- Caching strategies

### File Processing
- Async processing for large files
- Memory management
- Temporary file cleanup
- Resource limits

## Testing Requirements

### Unit Testing
- pytest for backend
- Jest for frontend
- Mock external dependencies
- Edge case coverage

### Integration Testing
- API endpoint testing
- Database operations
- Email functionality
- Third-party integrations

### User Testing
- Complete workflow testing
- Cross-browser compatibility
- Mobile responsiveness
- Accessibility validation

## Documentation Standards

### Code Documentation
- Inline comments for complex logic
- Function docstrings
- API documentation
- Architecture diagrams

### User Documentation
- Feature guides
- FAQ sections
- Troubleshooting guides
- Video tutorials

### Technical Documentation
- Setup instructions
- Deployment guides
- Configuration references
- Security guidelines