---
name: tdd-workflow
description: Execute TDD red-green-refactor cycle with just verify gate. Use when writing new features or fixing bugs that require test coverage.
allowed-tools:
  - Bash
  - Edit
  - Read
  - Write
---

## TDD Workflow Instructions

### Step 1: Read Specification

```bash
cat .council/BRIEF.md
cat SPEC.md  # if exists
```

### Step 2: Write Failing Test

1. Create test file in `tests/` directory
2. Write test cases covering acceptance criteria
3. Run tests to confirm **red state**:

```bash
source .venv/bin/activate && pytest tests/ -q
```

### Step 3: Implement Minimal Code

1. Write minimum code to pass tests
2. Follow existing code patterns
3. Keep diff small (≤200 lines)

### Step 4: Verify

```bash
just verify
```

### Step 5: Document

Update `.council/NOTES.md` with:

- Changes made
- Contracts declared
- Test coverage

## Example Usage

**Trigger phrases:**

- "Add tests for X"
- "Implement X with TDD"
- "Fix bug in X (TDD)"

**Expected output:**

1. Test file(s) created
2. Implementation code
3. `just verify` output showing all tests pass
