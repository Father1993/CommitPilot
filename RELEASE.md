# Release Guide

## Creating Your First Release on GitHub

### Prerequisites

1. Make sure all changes are committed and pushed:
```bash
git add .
git commit -m "chore: prepare for release"
git push origin main
```

2. Ensure you're on the main branch:
```bash
git checkout main
git pull origin main
```

### Step 1: Update Version

Update version in `auto_commit.py`:
```python
VERSION = "1.0.0"  # Change to your version
```

### Step 2: Create Release Notes

Update `docs/changelog.md` with release notes for the new version.

### Step 3: Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag to GitHub
git push origin v1.0.0
```

### Step 4: Create Release on GitHub

1. Go to your repository on GitHub
2. Click **"Releases"** → **"Create a new release"**
3. Select tag: `v1.0.0`
4. Release title: `v1.0.0` or `Release 1.0.0`
5. Description: Copy from `docs/changelog.md` for this version
6. Check **"Set as the latest release"**
7. Click **"Publish release"**

### Step 5: Verify Release

- Check that release appears on GitHub Releases page
- Verify tag is created correctly
- Test installation from release

## Release Checklist

- [ ] All code is committed and pushed
- [ ] Version updated in `auto_commit.py`
- [ ] Changelog updated
- [ ] Tests pass (if any)
- [ ] README is up to date
- [ ] LICENSE file exists
- [ ] Git tag created
- [ ] Release published on GitHub

## Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

## Example Release Workflow

```bash
# 1. Update version
# Edit auto_commit.py: VERSION = "1.0.0"

# 2. Commit changes
git add .
git commit -m "chore: bump version to 1.0.0"
git push origin main

# 3. Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 4. Create release on GitHub (via web interface)
```

## Post-Release

After release:
- Monitor for issues
- Update documentation if needed
- Prepare next version development
