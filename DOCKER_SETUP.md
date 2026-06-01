# Docker ghcr.io Setup — Quick Action

The Docker image needs one more step: the GitHub token needs `workflow` scope.

## What to do (30 seconds)

1. Go to https://github.com/settings/tokens
2. Find the token used in `.git-credentials` (starts with `ghp_`)
3. Edit it → check `workflow` scope
4. Save

Then run from your terminal:
```bash
cd /root/.hermes/scripts/evolver/evolver-tools
cp docker-publish.workflow.yml .github/workflows/docker-publish.yml
git add .github/workflows/docker-publish.yml
git commit -m "ci: Docker build & publish to ghcr.io"
git push
```

That's it. On the next push to `main` or tag `v*`, GitHub Actions builds and pushes the Docker image to `ghcr.io/evolver-dev/evolver-tools`.

## What this unlocks

After setup, developers worldwide can run:
```bash
docker run --rm ghcr.io/evolver-dev/evolver-tools evtool list
```

This is a new discovery channel — Docker Hub search results, container registries, and dev workflows.
