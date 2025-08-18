# Build Issue: React Server-Side Rendering Error

## Problem
The `reflex export --frontend-only` command fails during the production build with the following error:

```
Error: Element type is invalid: expected a string (for built-in components) or a class/function (for composite components) but got: object.
```

## Details
- **Command**: `uv run reflex export --frontend-only`
- **Error Location**: React server-side rendering during prerendering
- **Build Tool**: React Router with Rolldown/Vite
- **Status**: Temporarily removed from CI to unblock development

## Error Context
The error occurs during the prerendering phase when React Router tries to server-render the application. The error suggests that a React component is receiving an object instead of a valid component type (string or function).

## Potential Causes
1. **Import/Export Issues**: A component might be imported incorrectly (e.g., importing a module object instead of the component itself)
2. **Reflex Component Registration**: Issues with how Reflex components are registered or exported
3. **Dynamic Imports**: Problems with dynamic component loading during SSR
4. **Component Definition**: A component might be defined as an object instead of a function/class

## Investigation Steps
1. Check all component imports in the main application file
2. Verify Reflex component definitions and exports
3. Test with a minimal component setup to isolate the issue
4. Review Reflex documentation for SSR-specific requirements

## Workaround
The build step has been temporarily removed from CI to allow development to continue. The application works correctly in development mode.

## Next Steps
- [ ] Investigate component import/export patterns
- [ ] Test with simplified component structure
- [ ] Check Reflex version compatibility
- [ ] Consider disabling SSR if not required
- [ ] Re-enable build step in CI once resolved
