# BPM Documentation

This directory contains the documentation for the Bioinformatics Project Manager (BPM) project. The documentation is built using [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## 📖 Documentation Site

The documentation is automatically deployed to GitHub Pages and available at:
**https://chaochungkuo.github.io/BPM/**

## 🏗️ Local Development

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. **Install MkDocs and dependencies:**
   ```bash
   pip install mkdocs-material
   pip install mkdocs-git-revision-date-localized-plugin
   pip install mkdocs-minify-plugin
   pip install pymdown-extensions
   ```

2. **Build the documentation:**
   ```bash
   cd doc
   mkdocs build
   ```

3. **Serve locally for development:**
   ```bash
   mkdocs serve
   ```
   
   The documentation will be available at `http://127.0.0.1:8000/`

### Development Workflow

1. **Edit documentation files** in the `docs/` directory
2. **Preview changes** using `mkdocs serve`
3. **Build for production** using `mkdocs build`
4. **Commit and push** changes to trigger automatic deployment

## 📁 Directory Structure

```
doc/
├── mkdocs.yml              # MkDocs configuration
├── README.md              # This file
├── docs/                  # Documentation source files
│   ├── index.md          # Homepage
│   ├── getting-started/  # Installation and setup guides
│   ├── user-guide/       # User documentation
│   ├── admin-guide/      # Administrator documentation
│   ├── developer-guide/  # Developer documentation
│   ├── examples/         # Example workflows and use cases
│   └── troubleshooting/  # Troubleshooting guides
└── assets/               # Static assets (images, etc.)
```

## 🚀 Automatic Deployment

The documentation is automatically deployed using GitHub Actions. When you push changes to the `main` branch, the workflow:

1. **Builds** the documentation using MkDocs
2. **Deploys** it to GitHub Pages
3. **Makes it available** at https://chaochungkuo.github.io/BPM/

### GitHub Action Workflow

The deployment workflow is defined in `.github/workflows/deploy-docs.yml` and triggers on:
- Pushes to `main` branch
- Changes to files in `doc/` directory
- Changes to source code that might affect documentation

## 📝 Contributing to Documentation

### Adding New Pages

1. **Create a new Markdown file** in the appropriate directory under `docs/`
2. **Add navigation entry** in `mkdocs.yml` under the `nav` section
3. **Follow the existing style** and formatting conventions
4. **Test locally** using `mkdocs serve`

### Documentation Style Guide

- **Use clear, concise language**
- **Include code examples** where appropriate
- **Use proper Markdown formatting**
- **Add links** to related pages
- **Include screenshots** for complex procedures
- **Test all code examples** before committing

### Markdown Extensions

This documentation uses several MkDocs extensions:

- **Admonitions**: For notes, warnings, and tips
- **Code highlighting**: For syntax highlighting
- **Tables**: For structured data
- **Task lists**: For checkboxes
- **Emoji**: For visual elements

Example:
```markdown
!!! note "Note"
    This is a note with important information.

!!! warning "Warning"
    This is a warning about potential issues.

!!! tip "Tip"
    This is a helpful tip.
```

## 🔧 Configuration

The main configuration file is `mkdocs.yml` which includes:

- **Site metadata** (name, description, URL)
- **Theme configuration** (Material theme with custom colors)
- **Navigation structure**
- **Plugin settings**
- **Markdown extensions**

### Customizing the Theme

The Material theme is configured with:
- **Primary color**: Indigo
- **Dark/light mode toggle**
- **Search functionality**
- **Git repository integration**
- **Social links**

## 🐛 Troubleshooting

### Common Issues

1. **Build fails**: Check for syntax errors in Markdown files
2. **Navigation broken**: Verify entries in `mkdocs.yml`
3. **Images not showing**: Ensure paths are correct and files exist
4. **Deployment fails**: Check GitHub Actions logs

### Getting Help

- **MkDocs documentation**: https://www.mkdocs.org/
- **Material theme documentation**: https://squidfunk.github.io/mkdocs-material/
- **GitHub Issues**: https://github.com/chaochungkuo/BPM/issues

## 📚 Additional Resources

- **MkDocs User Guide**: https://www.mkdocs.org/user-guide/
- **Material for MkDocs**: https://squidfunk.github.io/mkdocs-material/
- **Markdown Guide**: https://www.markdownguide.org/
- **GitHub Pages**: https://pages.github.com/

## 🤝 Contributing

We welcome contributions to improve the documentation! Please:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test locally** with `mkdocs serve`
5. **Submit a pull request**

For major changes, please open an issue first to discuss what you would like to change. 