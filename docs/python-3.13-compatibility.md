# Python 3.13 Compatibility Notes

## asyncpg Build Issues with Python 3.13

If you encounter build errors when installing dependencies on Python 3.13, this is likely due to `asyncpg` requiring compilation.

### Error
```
error: command '/usr/bin/gcc' failed with exit code 1
```

### Solution

#### Option 1: Use psycopg[binary] (Recommended)

This project now uses `psycopg[binary]` instead of `asyncpg`:

```bash
pip install -r requirements.txt
```

**Psycopg** is a mature PostgreSQL adapter with pre-built wheels for Python 3.13, so no compilation is needed.

#### Option 2: Install Build Tools (if you want asyncpg)

```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev libpq-dev

# Then try again
pip install asyncpg==0.30.0
```

#### Option 3: Use Different Python Version

If you need to stick with `asyncpg`, use Python 3.11 or 3.12:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Why This Matters

- **asyncpg**: Pure C extension, requires compilation, highly optimized
- **psycopg**: Pure Python + optional C extensions (pre-built for Python 3.13)

Both work well. Psycopg with binary wheels is more portable and requires less setup.

### Testing PostgreSQL Connectivity

Both libraries work with our smoke tests. The connectivity tests automatically detect which library is available:

```bash
# Run smoke tests (works with either library)
./scripts/run_smoke_tests.sh --service postgres
```

### Migration Path

If you later need to switch back to `asyncpg`:

1. Wait for asyncpg to release Python 3.13 wheels
2. Update `requirements.txt` to use asyncpg
3. Optionally convert async code to use asyncpg's API

For now, **psycopg is the recommended choice** for Python 3.13.
