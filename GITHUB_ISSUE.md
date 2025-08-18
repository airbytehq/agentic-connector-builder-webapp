# GitHub Issue: React Server-Side Rendering Error in Production Build

**Title:** Production build fails with "Element type is invalid" during React SSR

**Labels:** bug, build, reflex

**Assignees:** @aaronsteers

**Description:**

## Problem
The `reflex export --frontend-only` command fails during the production build with a React server-side rendering error. This issue was discovered while setting up CI/CD workflows.

## Error Details
```
Error: Element type is invalid: expected a string (for built-in components) or a class/function (for composite components) but got: object.
```

**Full error context:**
- **Command:** `uv run reflex export --frontend-only`
- **Build Tool:** React Router with Rolldown/Vite
- **Phase:** Server-side rendering during prerendering
- **Exit Code:** 1

## Impact
- Production builds cannot be completed
- CI build step had to be temporarily removed
- Application works correctly in development mode

## Root Cause Analysis
The error occurs during the prerendering phase when React Router tries to server-render the application. The error suggests that a React component is receiving an object instead of a valid component type (string or function).

**Potential causes:**
1. **Import/Export Issues:** A component might be imported incorrectly (e.g., importing a module object instead of the component itself)
2. **Reflex Component Registration:** Issues with how Reflex components are registered or exported
3. **Dynamic Imports:** Problems with dynamic component loading during SSR
4. **Component Definition:** A component might be defined as an object instead of a function/class

## Investigation Steps
- [ ] Check all component imports in the main application file
- [ ] Verify Reflex component definitions and exports
- [ ] Test with a minimal component setup to isolate the issue
- [ ] Review Reflex documentation for SSR-specific requirements
- [ ] Check if the issue is related to the Monaco editor integration

## Workaround
The build step has been temporarily removed from CI to allow development to continue. The application works correctly in development mode with `reflex run`.

## Environment
- **Reflex Version:** 0.8.6
- **Python Version:** 3.11-3.13 (tested in CI)
- **Node.js Version:** 20.18.2 (with warning about outdated version)
- **Build Tool:** React Router + Rolldown/Vite

## Related Files
- Main application: `agentic_connector_builder_webapp/agentic_connector_builder_webapp.py`
- CI workflow: `.github/workflows/ci.yml`
- Build documentation: `BUILD_ISSUE.md`

## Next Steps
1. Investigate component import/export patterns
2. Test with simplified component structure
3. Check Reflex version compatibility and SSR requirements
4. Consider disabling SSR if not required for the use case
5. Re-enable build step in CI once resolved

**Requested by:** @aaronsteers during CI/CD setup
**Session:** https://app.devin.ai/sessions/0937a847256e42f2ae060a86cd6b2d1c
