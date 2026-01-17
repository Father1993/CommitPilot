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

### Step 2: Run Tests

**Critical:** Always run tests before release:

```bash
pytest tests/ -v
```

Ensure all tests pass (should show `18 passed`).

### Step 3: Create Release Notes

Update `docs/changelog.md` with release notes for the new version.

### Step 4: Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.1 -m "Release version 1.0.0"

# Push tag to GitHub
git push origin v1.0.1
```

### Step 5: Create Release on GitHub

1. Go to your repository on GitHub
2. Click **"Releases"** → **"Create a new release"**
3. Select tag: `v1.0.1`
4. Release title: `v1.0.1` or `Release 1.0.0`
5. Description: Copy from `docs/changelog.md` for this version
6. Check **"Set as the latest release"**
7. Click **"Publish release"**

### Step 6: Verify Release

- Check that release appears on GitHub Releases page
- Verify tag is created correctly
- Test installation from release

## Release Checklist

- [ ] All code is committed and pushed
- [ ] Version updated in `auto_commit.py`
- [ ] Changelog updated
- [ ] **Tests pass** (run `pytest tests/ -v`)
- [ ] README is up to date
- [ ] LICENSE file exists
- [ ] Git tag created
- [ ] Release published on GitHub

## Running Tests Before Release

**Always run tests before creating a release:**

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest tests/ -v

# Expected output: All tests should pass (18 passed)
```

**Test coverage:**
- Configuration setup and environment variables
- Git operations (diff, status, add, commit, push)
- AI message generation (all providers)
- Error handling and edge cases
- File path handling

**If tests fail:**
- Fix issues before creating release
- Ensure all tests pass before tagging
- Update tests if functionality changed

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
git tag -a v1.0.1 -m "Release version 1.0.0"
git push origin v1.0.1

# 4. Create release on GitHub (via web interface)
```

## Post-Release

After release:
- Monitor for issues
- Update documentation if needed
- Prepare next version development
