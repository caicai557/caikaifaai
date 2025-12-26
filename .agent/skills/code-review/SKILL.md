---
name: code-review
description: Perform thorough code review with security and quality checks. Use before commits or when reviewing PRs.
allowed-tools:
  - Bash
  - Read
---

## Code Review Instructions

### Step 1: Gather Context

```bash
git diff HEAD~1
git log --oneline -5
```

### Step 2: Check Quality Gates

```bash
just verify
```

### Step 3: Security Scan

Review for:

- [ ] No hardcoded secrets
- [ ] No eval/exec with user input
- [ ] No SQL injection vectors
- [ ] No path traversal vulnerabilities

### Step 4: Contract Verification

Check against `.council/CONTRACTS.md`:

- [ ] Exception types match specification
- [ ] Return types are consistent
- [ ] Breaking changes documented in DECISIONS.md

### Step 5: Output Review Summary

```yaml
review:
  status: APPROVED | CHANGES_REQUESTED | BLOCKED
  security_issues: []
  quality_issues: []
  suggestions: []
  blocked_reason: null
```

## Example Usage

**Trigger phrases:**

- "Review this code"
- "Check PR before merge"
- "Security review"

**Expected output:**

- Review summary YAML
- List of issues (if any)
- Approval or rejection with reasons
