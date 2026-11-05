# Privacy and public contributions

## What belongs in Git

Source, documentation, generic example configuration and synthetic tests belong in Git. Personal statements, transaction CSVs, real classification patterns, screenshots of actual balances and local environment files do not.

The `.gitignore` excludes private inputs, data outputs, local configuration, agent state and common financial export formats. Setup installs repository-local commit/push hooks when no existing hooks configuration is present. CI runs the same privacy checker against reachable history.

## Review before publishing

```bash
git status --short
git diff --cached --stat
git diff --cached
npm run privacy
npm run privacy:history
```

The checker reads staged Git blobs, rather than trusting the working tree. History mode inspects all commits reachable from HEAD, including commit messages and email metadata. It flags private file paths, common account/phone-like identifiers, email addresses, secrets and private keys without printing matched values. Use a GitHub noreply email for public commits.

This is a heuristic, not proof of anonymity: it cannot recognize every name, merchant association, medical detail or unique spending pattern. Review source and diffs manually. Do not force-add ignored data or bypass the hooks.

`.gitignore` does not remove files already tracked, and deleting a secret in a new commit does not remove it from history. If sensitive history was published, stop further publication, coordinate a history cleanup with the owner, and rotate exposed credentials if applicable. Other clones, forks and caches may retain copies.

## Local application boundary

- The app reads a server-side local file and serves it to the local browser. Export paths are not client-configurable query parameters.
- The API sends `Cache-Control: no-store` and excludes unused dedicated account/card/raw-row columns. Descriptions and merchant details are still private data.
- Servers bind to loopback by default. There is no authentication or encryption at rest. Other local users/processes with file access can read data.
- Dependencies are installed from package registries during setup; runtime import/analysis does not upload transactions. Nuxt telemetry is disabled.
- A cloud AI assistant is a separate service. Use fictional samples/header names, or consciously authorize access to private material; no app setting changes the assistant provider's data handling.
- Builds and screenshots should be verified with the synthetic demo. Never publish a deployment artifact containing a real dataset or server-rendered private page.

## Local configuration

Use `.env` for a private `NUXT_DATA_FILE` path and `private/rules.json` for personal matching rules. Never use a `NUXT_PUBLIC_` variable for secrets or private file paths. Preserve local backups outside the public Git history.
