# GSE-One — Guide de publication du plugin

Ce dossier contient la specification (`gse-one-spec-v0.8.md`), le document de conception (`gse-one-implementation-design-v0.8.md`) et l'implementation complete du plugin (`gse-one/`).

Ce guide decrit toutes les etapes pour publier le plugin GSE-One et le rendre installable par les utilisateurs Claude Code et Cursor.

---

## Table des matieres

1. [Architecture mono-plugin](#1-architecture-mono-plugin)
2. [Developper et generer](#2-developper-et-generer)
3. [Publier le plugin](#3-publier-le-plugin)
4. [Recapitulatif des commandes](#4-recapitulatif-des-commandes)

---

## 1. Architecture mono-plugin

GSE-One utilise un **seul dossier deployable** (`plugin/`) qui fonctionne sur les deux plateformes :

```
gse-one/
├── src/                              # Source unique de verite (62 fichiers)
│   ├── principles/                   # 16 principes (P1-P16)
│   ├── activities/                   # 22 skills SKILL.md
│   ├── agents/                       # 9 agents (8 specialises + orchestrateur)
│   └── templates/                    # 15 templates
│
├── plugin/                           # Dossier deployable (52 fichiers)
│   ├── .claude-plugin/plugin.json    # Manifest Claude Code
│   ├── .cursor-plugin/plugin.json    # Manifest Cursor
│   ├── skills/                       # 22 skills (partages)
│   ├── agents/                       # 9 agents (partages)
│   ├── templates/                    # 15 templates (partages)
│   ├── rules/000-gse-methodology.mdc # Cursor uniquement (ignore par Claude)
│   ├── hooks/hooks.claude.json       # Format Claude Code
│   ├── hooks/hooks.cursor.json       # Format Cursor
│   └── settings.json                 # Claude uniquement (ignore par Cursor)
│
├── marketplace/
│   └── .claude-plugin/marketplace.json
│
└── gse_generate.py                   # Generateur: src/ → plugin/
```

**Fichiers partages (46) :** skills, agents, templates — un seul exemplaire, zero divergence.
**Fichiers specifiques (6) :** 2 manifests + 2 hooks + 1 settings + 1 .mdc — generes par paires equivalentes.

---

## 2. Developper et generer

### Modifier les sources

Tous les changements se font dans `src/`. Ne jamais modifier `plugin/` directement — il est regenere.

### Regenerer le plugin

Apres toute modification :

```bash
cd gse-one/
python3 gse_generate.py --clean --verify
```

Le generateur :
1. Copie les skills, agents specialises et templates (partages)
2. Genere l'orchestrateur (`agents/gse-orchestrator.md`) et la regle Cursor (`rules/000-gse-methodology.mdc`) depuis la **meme source** — verifie que le corps est identique
3. Genere les 2 hooks (Claude PascalCase / Cursor camelCase) depuis les memes commandes
4. Genere les 2 manifests et `settings.json`

### Creer le depot GitHub

```bash
cd gse-one/
git init
git add .
git commit -m "feat: GSE-One v0.8.0 — initial release"
gh repo create gse-one/gse-one --public --source=. --push
```

> **Important :** Mettre a jour le champ `repository` dans `plugin/.claude-plugin/plugin.json`, `plugin/.cursor-plugin/plugin.json` et `marketplace/.claude-plugin/marketplace.json` avec l'URL reelle du depot.

---

## 3. Publier le plugin

### Pour Claude Code

#### Methode A — Test local

```bash
claude --plugin-dir ./plugin/
```

Charge le plugin pour la session en cours. `/reload-plugins` pour recharger apres modification.

#### Methode B — Marketplace personnel

1. **Verifier** `marketplace/.claude-plugin/marketplace.json` :
   ```json
   {
     "plugins": [{
       "id": "gse-one",
       "name": "GSE-One",
       "description": "AI engineering companion for structured SDLC management",
       "source": {
         "type": "github",
         "repo": "gse-one/gse-one",
         "path": "plugin"
       },
       "version": "0.8.0"
     }]
   }
   ```

2. **Publier** le depot : `git push origin main`

3. **Les utilisateurs** installent :
   ```bash
   /plugin marketplace add gse-one/gse-one
   /plugin install gse-one@gse-one
   ```

   Scopes disponibles :
   | Scope | Fichier | Usage |
   |-------|---------|-------|
   | `--scope user` | `~/.claude/settings.json` | Personnel (defaut) |
   | `--scope project` | `.claude/settings.json` | Equipe (commit dans le repo) |
   | `--scope local` | `.claude/settings.local.json` | Personnel, gitignore |

#### Methode C — Marketplace officiel Anthropic

1. Soumettre via [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit) ou [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)
2. Plugin path : `plugin`
3. Apres approbation : `claude plugin install gse-one`

### Pour Cursor

#### Methode A — Test local

```bash
# Copier le plugin dans le projet
cp -r gse-one/plugin/ ./gse-one-plugin/
# Dans Cursor : /add-plugin > Local > selectionner ./gse-one-plugin/
```

#### Methode B — Cursor Marketplace

1. Soumettre via [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)
2. Le plugin contient deja `.cursor-plugin/plugin.json` avec les paths corrects
3. Apres approbation : les utilisateurs installent via `/add-plugin`

#### Methode C — Distribution GitHub

Les utilisateurs clonent et installent localement :
```bash
git clone --depth 1 https://github.com/gse-one/gse-one.git /tmp/gse
cp -r /tmp/gse/plugin/ ./gse-one-plugin/
rm -rf /tmp/gse
# Dans Cursor : /add-plugin > Local > selectionner ./gse-one-plugin/
```

---

## 4. Recapitulatif des commandes

### Developpeur

```bash
# Regenerer apres modification
python3 gse_generate.py --clean --verify

# Publier une nouvelle version
# 1. Mettre a jour version dans gse_generate.py (constante VERSION)
# 2. Regenerer
python3 gse_generate.py --clean --verify
# 3. Commit + tag + push
git add .
git commit -m "feat: GSE-One v0.8.1 — description"
git tag v0.8.1
git push origin main --tags
```

### Utilisateur Claude Code

```bash
# Marketplace personnel
/plugin marketplace add gse-one/gse-one
/plugin install gse-one@gse-one

# Marketplace officiel
/plugin install gse-one

# Test local
claude --plugin-dir ./plugin/
```

### Utilisateur Cursor

```bash
# Marketplace officiel
# /add-plugin > chercher "gse-one"

# Local
# /add-plugin > Local > selectionner le dossier plugin/
```

### Verification

Quelle que soit la methode, taper :

```
/gse:go
```

L'agent GSE-One doit repondre, detecter l'etat du projet et proposer l'activite suivante.

---

## Versioning

1. Modifier la constante `VERSION` dans `gse_generate.py`
2. Regenerer : `python3 gse_generate.py --clean --verify` (met a jour les 2 manifests automatiquement)
3. Commit + tag : `git tag v0.8.1 && git push origin main --tags`
4. Claude Code marketplace : mise a jour automatique pour les utilisateurs
5. Cursor : les utilisateurs doivent reinstaller ou mettre a jour via le marketplace
