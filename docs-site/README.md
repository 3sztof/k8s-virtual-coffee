# Virtual Coffee Platform Documentation

This directory contains the documentation site for the Virtual Coffee Platform, built with [Docusaurus](https://docusaurus.io/).

## Local Development

To develop the documentation site locally:

```bash
# Install dependencies
cd docs-site
npm install

# Start the development server
npm start
```

This will start a local development server and open up a browser window. Most changes are reflected live without having to restart the server.

## Build

To build the static site:

```bash
# Build the site
cd docs-site
npm run build
```

This command generates static content into the `build` directory that can be served using any static content hosting service.

## Deployment

The documentation site is automatically deployed to GitHub Pages when changes are pushed to the main branch. The deployment is handled by a GitHub Actions workflow defined in `.github/workflows/documentation.yml`.

### Manual Deployment

If you need to deploy the site manually:

```bash
# Deploy to GitHub Pages
cd docs-site
npm run deploy
```

This command builds the website and pushes it to the `gh-pages` branch of your repository.

## Adding New Documentation

### Adding New Pages

1. Create a new Markdown file in the appropriate directory under `docs-site/docs/`
2. Add front matter at the top of the file:

```md
---
sidebar_position: 1
---

# Title of Your Page

Content goes here...
```

3. Update the sidebar configuration in `sidebars.js` if needed

### Adding Images

1. Place image files in the `docs-site/static/img/` directory
2. Reference them in your Markdown files:

```md
![Alt text](/img/your-image.png)
```

## Customization

### Site Configuration

The site configuration is in `docusaurus.config.js`. You can customize:

- Site metadata
- Navigation bar
- Footer
- Theme settings

### Styling

Custom CSS can be added in `src/css/custom.css`.

## Structure

The documentation is organized into the following sections:

- **User Guide**: Documentation for end users
- **Admin Guide**: Documentation for administrators
- **Deployment**: Documentation for deployment and operations

Each section has its own sidebar configuration in `sidebars.js`.