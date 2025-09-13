# IETF Rate Limit Headers Internet-Draft Repository

This repository contains the IETF Internet-Draft for RateLimit header fields for HTTP. It uses the martinthomson/i-d-template system for building RFC-formatted documents from Markdown source.

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information here is incomplete or found to be in error.**

## Working Effectively

### Bootstrap and Setup
- Install required tools:
  ```bash
  # Add local gem bin to PATH
  export PATH="$PATH:/home/runner/.local/share/gem/ruby/3.2.0/bin:/home/runner/.local/bin"
  
  # Install IETF drafting tools
  gem install --user-install kramdown-rfc
  pip install xml2rfc http-sfv
  ```

### Building the Draft
- **Primary build command:** `make` 
- **Expected build time:** 2-3 seconds when failing due to network issues, 2-5 minutes when successful. **NEVER CANCEL** - set timeout to 15+ minutes.
- **Network dependency:** **CRITICAL** - Requires internet access to download RFC references from bib.ietf.org and API access to github.com
- **Build status in CI environments:** **CURRENTLY FAILS** due to network restrictions blocking bib.ietf.org access
- **Build validation:** The build process correctly generates intermediate XML but fails on final processing due to missing RFC references
- **Common build issues:**
  - Network restrictions: Build will fail with "Failed to open TCP connection to bib.ietf.org:443" - this is expected in restricted environments
  - GitHub API limits: "403 Client Error: Forbidden for url: https://api.github.com/repos/ietf-wg-httpapi/ratelimit-headers"
  - Missing tools: Run bootstrap commands above
  - Permission errors: Use `--user-install` for gem installations

### Alternative Build Methods
- **Docker build:** `docker compose up test`
  - Expected time: 45 seconds when failing due to network issues. **NEVER CANCEL** - set timeout: 10+ minutes.
  - **CURRENTLY FAILS** due to network connectivity restrictions in CI environments
  - Only use when native tools fail and in environments with full internet access

### Testing and Validation
- **Python tests:** Run rate limit header parsing tests
  ```bash
  python3 test_ratelimit.py
  python3 -c "import test_ratelimit; test_ratelimit.test_policy(); print('Policy test passed')"
  python3 -c "import test_ratelimit; test_ratelimit.test_get_policy(); print('Get policy test passed')"
  ```
  - Expected time: Under 5 seconds
  - Tests validate HTTP Structured Field Value parsing for rate limit headers

### Successful Build Artifacts
- **In environments with full internet access**, build creates:
  - `draft-ietf-httpapi-ratelimit-headers.txt` (RFC text format)
  - `draft-ietf-httpapi-ratelimit-headers.html` (HTML format)
  - `draft-ietf-httpapi-ratelimit-headers.xml` (intermediate XML)
- **In restricted environments**: Build tools work correctly but final document generation fails due to missing RFC references

## Validation Scenarios

**ALWAYS run these validation steps after making changes to the draft:**

1. **Build validation:**
   ```bash
   export PATH="$PATH:/home/runner/.local/share/gem/ruby/3.2.0/bin:/home/runner/.local/bin"
   time make
   ```
   - **Expected in CI environments**: Will fail with network connectivity errors - this is normal
   - Verify kramdown-rfc processes the Markdown correctly (no kramdown errors)
   - Verify build reaches xml2rfc stage before network failures
   - **In full internet environments**: Check that .txt and .html files are generated

2. **Python code validation:**
   ```bash
   python3 test_ratelimit.py
   ```
   - Ensures rate limit header examples in draft are syntactically correct
   - Validates HTTP Structured Field parsing works as expected

3. **Draft content validation:**
   - Review generated .txt file for proper RFC formatting
   - Check that all cross-references resolve correctly
   - Verify examples render properly in HTML output

## Repository Structure and Key Files

### Essential Files
- `draft-ietf-httpapi-ratelimit-headers.md` - Main Internet-Draft source (RFC-style Markdown)
- `test_ratelimit.py` - Python tests for rate limit header parsing and validation
- `Makefile` - Build system (uses martinthomson/i-d-template)
- `docker-compose.yml` - Alternative Docker-based build environment

### Generated/Build Files
- `lib/` - Build system tools (automatically downloaded)
- `.refcache/` - Cached RFC references
- `*.xml`, `*.txt`, `*.html` - Build artifacts

### GitHub Actions
- `.github/workflows/ghpages.yml` - Updates editor's copy on push
- `.github/workflows/publish.yaml` - Publishes drafts on tag
- `.github/workflows/update.yaml` - Updates template files

## Common Tasks

### Editing the Draft
- Edit `draft-ietf-httpapi-ratelimit-headers.md` using RFC markdown syntax
- Always validate changes with full build and test cycle
- Check both text and HTML output for proper formatting

### Testing Header Examples
- Update `test_ratelimit.py` when adding new header field examples
- Run tests to ensure examples use correct HTTP Structured Field syntax
- Validate parsing behavior matches specification

### Build Troubleshooting
- **Network restrictions**: Build will fail with "Failed to open TCP connection to bib.ietf.org:443" - this is expected in CI environments with limited internet access
- **GitHub API limits**: "403 Client Error: Forbidden" - occurs in CI environments, doesn't affect functionality
- **Missing tools**: Re-run bootstrap installation commands
- **Permission errors**: Ensure `--user-install` flag for gem installations
- **Validation approach**: Even when builds fail due to network issues, verify that kramdown-rfc processes the markdown correctly before network calls

## Timing and Performance Expectations

### Build Commands
- `make`: 2-3 seconds when failing on network issues, 2-5 minutes when successful - **NEVER CANCEL**, timeout: 15+ minutes
- `docker compose up test`: 45 seconds when failing on network issues - **NEVER CANCEL**, timeout: 10+ minutes
- Python tests: Under 5 seconds - timeout: 30 seconds

### GitHub Actions
- CI builds typically complete in 2-5 minutes
- May take longer during peak usage or network issues
- Check GitHub Actions logs for detailed build progress

## References and Documentation

### IETF Template System
- Based on martinthomson/i-d-template
- Uses kramdown-rfc for Markdown to XML conversion
- Uses xml2rfc for final document generation

### Rate Limit Headers Specification
- Defines HTTP header fields for communicating rate limiting information
- Uses HTTP Structured Fields format (RFC 8941)
- Python tests validate compliance with structured field syntax

**Remember: ALWAYS run the full build and test cycle after making any changes. The GitHub Actions CI will fail if the draft doesn't build correctly.**