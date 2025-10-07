# Nocturnal Archive (Beta Agent)

Lean, reliable research and finance workflows in a single CLI-first agent. This repository now focuses on the shipping beta; earlier backend experiments live on in Git history if you ever need to revisit them.

## ✨ Highlights
- **Deterministic tooling** – guarded shell execution, workspace previews, and formatter-free outputs.
- **Finance shortcuts** – one-hop summaries from the FinSight API with ticker heuristics and trusted sources.
- **Workspace awareness** – structured file listings and preview responses tuned for IDE flows.
- **CLI ready** – install the package, run `nocturnal`, and get to work.

## 🚀 Quick Start

One-liner installer (online):

```bash
curl -fsSL https://get.nocturnal.dev/install.sh | bash
```

```bash
git clone https://github.com/Spectating101/nocturnal-archive.git
cd nocturnal-archive
python3 -m venv .venv
source .venv/bin/activate
pip install .
nocturnal --setup   # one-time Groq key configuration
nocturnal           # interactive session
```

Need the full instructions? See [`docs/INSTALL.md`](docs/INSTALL.md).
Prefer a friendlier walkthrough? Try [`docs/USER_GETTING_STARTED.md`](docs/USER_GETTING_STARTED.md).

## 🧱 Repository Layout

```
nocturnal_archive/     # Python package shipped to users
tests/                 # Regression suite that gates the beta
tools/                 # Operational utilities (security audit, etc.)
docs/                  # Installation + release guides
```

## 📦 Packaging & Distribution

- Runtime dependencies trimmed to `aiohttp`, `groq`, `python-dotenv`, and `rich`.
- `python -m build` produces wheel + sdist with bundled ticker metadata.
- `./tools/packaging/build_secure_cli.sh` compiles a hardened Nuitka binary (see [`docs/SECURE_PACKAGING_GUIDE.md`](docs/SECURE_PACKAGING_GUIDE.md)).
- `nocturnal-update` polls PyPI for upgrades once the package is published.
- Development extras live in `requirements-dev.txt` (`pytest`, `black`, `flake8`, `mypy`, `nuitka`).

## 🧪 Quality Gates

Run the minimal battery before shipping a tag:

```bash
pytest tests/enhanced -q
flake8 nocturnal_archive tests
mypy nocturnal_archive
```

Refer to [`docs/BETA_RELEASE_CHECKLIST.md`](docs/BETA_RELEASE_CHECKLIST.md) for the full release ritual.

## 🔐 Security & Operations

- Shell commands are sandboxed by `_is_safe_shell_command`; blocked attempts surface clear messaging.
- `NocturnalConfig` stores Groq keys in the OS keychain when available, with auto-migration from legacy configs.
- `tools/security_audit.py` validates deployment environments for required secrets.
- Hardened binaries available via the secure packaging script for beta distribution.
- Query throttles are signed with HMAC tokens—tampering with the daily cap falls back to the default and is logged.
- Update checks run silently in the background with `nocturnal-update`.

## 🤝 Contributing

1. Fork and branch from `main`.
2. Keep edits focused on the `nocturnal_archive` package or `tests/` to streamline reviews.
3. Run the quality gates listed above.
4. Submit a PR with a short release note.

## 📄 License

MIT – see [`LICENSE`](LICENSE).

---
