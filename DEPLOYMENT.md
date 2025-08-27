# Deployment Guide

This document provides instructions for deploying the Agentic Connector Builder WebApp to various platforms.

## Vercel Deployment

The application is configured for easy deployment to Vercel using static site generation.

### Prerequisites

- A [Vercel account](https://vercel.com)
- This repository pushed to GitHub, GitLab, or Bitbucket

### Automatic Deployment (Recommended)

1. **Connect Repository to Vercel:**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your repository

2. **Configure Build Settings:**
   - Vercel will automatically detect the `vercel.json` configuration
   - Framework Preset: Other
   - Build Command: `pip install -r requirements.txt && reflex init && reflex export --frontend-only --no-zip`
   - Output Directory: `.web/build/client`
   - Install Command: `pip install -r requirements.txt`

3. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy your application
   - You'll receive a live URL for your deployed app

### Manual Deployment

If you prefer to deploy manually:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize Reflex
reflex init

# 3. Export static build
reflex export --frontend-only --no-zip

# 4. Deploy the .web/build/client directory to your hosting provider
```

### Environment Variables

The application currently doesn't require any environment variables for basic functionality. If you extend the app to include external API calls or database connections, add them in the Vercel dashboard under Project Settings > Environment Variables.

### Custom Domain

To use a custom domain:

1. Go to your project in Vercel Dashboard
2. Click on the "Domains" tab
3. Add your custom domain
4. Follow Vercel's instructions to configure DNS

## Local Development

For local development:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
reflex run
```

The application will be available at `http://localhost:3000`.

## Build Verification

To verify your build works locally before deploying:

```bash
# Build the application
reflex init
reflex export --frontend-only --no-zip

# Serve the static files (requires a static file server)
cd .web/build/client
python -m http.server 8000
```

Open `http://localhost:8000` to test the static build.

## Troubleshooting

### Build Fails

If the build fails, check:

1. **Python Version:** Ensure Python 3.11+ is available
2. **Dependencies:** Verify all dependencies in `requirements.txt` are installable
3. **Reflex Version:** Check if you're using a compatible Reflex version

### Runtime Errors

If you encounter runtime errors:

1. **Check Console:** Open browser dev tools and check for JavaScript errors
2. **Assets Loading:** Ensure all CSS/JS assets are loading correctly
3. **SPA Fallback:** For client-side routing issues, check that `__spa-fallback.html` exists

### Performance Issues

For performance optimization:

1. **Monaco Editor:** The Monaco editor may increase bundle size - consider lazy loading for large applications
2. **Static Assets:** Leverage Vercel's CDN for optimal asset delivery
3. **Caching:** Configure appropriate cache headers for static assets

## Additional Deployment Options

### Netlify

For Netlify deployment:

1. Create a `netlify.toml` file:
```toml
[build]
  command = "pip install -r requirements.txt && reflex init && reflex export --frontend-only --no-zip"
  publish = ".web/build/client"

[build.environment]
  PYTHON_VERSION = "3.11"
```

### GitHub Pages

For GitHub Pages:

1. Use GitHub Actions to build and deploy
2. Create `.github/workflows/deploy.yml` with static build process
3. Deploy to `gh-pages` branch

## Support

For deployment issues:

1. Check the [Reflex documentation](https://reflex.dev/docs/)
2. Review [Vercel documentation](https://vercel.com/docs)
3. Open an issue in this repository