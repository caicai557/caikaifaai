# Justfile for Council

# Run all verification checks
verify:
    ./.venv/bin/pytest tests/
