# PyPI Publishing Setup

This repository is configured for automated PyPI publishing using GitHub Actions with trusted publishing.

## 🔐 Required Setup

### 1. Configure Trusted Publishing on PyPI

1. **Create accounts:**
   - [PyPI account](https://pypi.org/account/register/) (for production releases)
   - [TestPyPI account](https://test.pypi.org/account/register/) (for testing)

2. **Configure trusted publishing:**
   - Go to PyPI → Account Settings → Publishing
   - Add a new "pending publisher" with:
     - **Owner:** `obzenner` (GitHub username/org)
     - **Repository:** `archy-repo`
     - **Workflow:** `publish-pypi.yml`
     - **Environment:** `pypi` (optional, for production)
   
   - Repeat for TestPyPI with environment: `testpypi`

### 2. Configure GitHub Environments (Optional but Recommended)

For additional protection, configure environments in GitHub:

1. Go to repository → Settings → Environments
2. Create `pypi` environment:
   - Add required reviewers (recommended for production)
   - Set deployment protection rules
3. Create `testpypi` environment (for testing)

### 3. Publishing Process

**Manual Publishing:**
```bash
# Go to GitHub Actions → Publish to PyPI → Run workflow
# Choose where to publish:
# - testpypi: For testing (safe)
# - pypi: For production release
# - both: Publish to both (test first, then production)
```

**Command Line Alternative:**
```bash
# You can also trigger from command line using gh CLI
gh workflow run publish-pypi.yml -f publish_to=testpypi
gh workflow run publish-pypi.yml -f publish_to=pypi
```

## 🚀 Workflow Triggers

- **Manual Only:** All publishing is triggered manually via `workflow_dispatch`
- **No Automatic Triggers:** Complete control over when and where to publish

## 🔗 Useful Links

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments)
