#!/usr/bin/env bash
# init_branches.sh – Erstellt alle Team-Branches
# Voraussetzung: git remote origin ist konfiguriert
set -e

echo "=== Branch-Initialisierung ==="

# develop erstellen
git checkout main
git checkout -b develop 2>/dev/null || git checkout develop
echo "Branch 'develop' bereit."

# Team-Branches erstellen
TEAMS="data-ingestion climate-analysis visualization simulation knowledge-base ai-explanation frontend api"

for team in $TEAMS; do
    git checkout develop
    if git show-ref --verify --quiet refs/heads/team/$team; then
        echo "Branch 'team/$team' existiert bereits."
    else
        git checkout -b team/$team
        echo "Branch 'team/$team' erstellt."
    fi
    git checkout develop
done

echo ""
echo "=== Alle Branches erstellt ==="
git branch -a
echo ""
echo "Push zu GitHub:"
echo "  git push origin --all"
