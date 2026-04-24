# Private GitHub Repo → Coolify Deployment — Trainer/Learner Guide

**Audience:** GSE-One trainers running a training where learners deploy apps from **private** GitHub repos to a shared Hetzner/Coolify instance.

**Scope:** This document describes the one-time setup the trainer performs on the Coolify side (a GitHub App declared as a Source), and the email template the trainer sends to learners once a learner hits a `422` during `/gse:deploy` because their repo is private.

**Why this exists:** Coolify cannot clone a private GitHub repo via anonymous HTTPS — it returns `422` from the `/applications/public` endpoint. To unblock this, Coolify supports a "GitHub App" source: the trainer registers a GitHub App once, each learner installs it on their own GitHub account with read access to their repo, and the trainer passes the Source UUID to each learner so that `deploy.py` can target the right authenticated source.

---

## A. Trainer-side one-time setup (~15 min)

Do this **once** per training program (reusable across all learners and all future cohorts).

### A.1 — Coolify: create the GitHub App source

1. In the Coolify UI (left sidebar): **Sources → + New → GitHub App**.
2. Fill in:
   - **Name**: a reusable identifier (e.g., `<your-training-namespace>-training`).
   - **Organization (on GitHub)**: your own GitHub account or a dedicated org you own (NOT the learner's account — see Ownership note below).
   - **System Wide**: check if your Coolify instance will serve multiple teams; leave unchecked otherwise.
   - **Self-hosted / Enterprise GitHub** fields: leave at defaults (`https://github.com`, `https://api.github.com`, `git`, `22`) unless you're using GHE Server.
3. Click **Continue**, then on the next page click **Register Now** (the Automated Installation path).
4. You are redirected to `github.com` with a pre-filled manifest. On the "Create GitHub App for `<your-account>`" page, do **not** modify the permissions — click **Create GitHub App**.
5. GitHub redirects back to Coolify. Your Source is now registered (App ID, Client ID/Secret, Webhook Secret, Private Key all auto-populated).

**Ownership note.** The GitHub App is owned by the trainer — *not* by any learner. The App owner holds the private key that Coolify uses to authenticate. Each learner will *install* this App on their own GitHub account as a separate, controlled gesture; installation ≠ ownership. A learner can revoke their installation at any time without affecting other learners.

### A.2 — **CRITICAL** — Make the App publicly installable

By default, the Coolify-generated manifest creates the App in **"Only on this account"** mode, meaning only the trainer's account can install it. Learners trying to install it will see a message saying the App is private and cannot be installed on their account. This step is frequently missed and is the **most common failure point** of this setup.

Fix:

1. Open `https://github.com/settings/apps/<your-app-slug>` (replace `<your-app-slug>` with your App's name, e.g., `<your-training-namespace>-training`).
2. Click the **Advanced** tab in the left sidebar.
3. Scroll down to the **Danger zone** section (it's cosmetic — this action is reversible).
4. Find the block **"Make this GitHub App public"** with the description *"Allow this GitHub App to be installed on other accounts"*.
5. Click **Make public**. Confirm the dialog.

**Verify** via `gh` CLI (optional but recommended):

```bash
gh api /apps/<your-app-slug> --jq '.slug, .html_url, .owner.login'
```

If this returns three lines (slug, html_url, owner) with no error, the App is publicly installable.

### A.3 — Collect the two values to share with learners

You need to share **two pieces of information** with every learner who wants to deploy a private repo:

1. **Install link** — `https://github.com/apps/<your-app-slug>/installations/new`

   Find this by navigating to `github.com/settings/apps/<your-app-slug>`, then clicking **Install App** in the left sidebar, then copying the URL of the page you land on.

2. **Coolify Source UUID** — visible in the URL of the Coolify Source page (`https://<your-coolify>/source/github/<UUID-here>`).

Both values are **identical for all your learners**, forever (until you rotate or delete the App). Store them in your trainer notes.

### A.4 — Trainer self-install (recommended smoke test)

Before exposing the setup to any learner, install the App on your own GitHub account as a smoke test:

1. Click **Install Repositories on GitHub** on the Coolify Source page (or open the install link directly).
2. Select your own account → "Only select repositories" → tick any test repo → Install.
3. Return to the Coolify Source page, refresh. The red warning *"You must complete this step before you can use this source!"* should disappear, and an Installations row for your account should appear.

If the warning remains after a refresh, investigate (webhook delivery logs in the App's Advanced tab, or Coolify logs).

---

## B. Email template to send to a blocked learner

Once a learner hits a `422` during `/gse:deploy` because their GitHub repo is private, send them this email. Replace the **two placeholders** (`<APP-SLUG>` and `<SOURCE-UUID>`) with your actual values from A.3.

**Perspective note.** GSE-One learners interact with their project through an **orchestrator agent** (Claude Code, Cursor, or opencode running the GSE-One plugin) — they do not typically run Python scripts or shell commands directly. This template is written accordingly: Step 1 is a browser-interactive action the learner must do themselves (GitHub login is out-of-scope for any IDE agent), but Steps 2 and 3 are **prompts the learner sends to the orchestrator**, which then adopts the `deploy-operator` role and executes the underlying `deploy.py` operations. This keeps the learner in their natural working surface (the IDE chat) instead of forcing a context switch to a terminal.

---

**Subject:** Coolify deployment — private GitHub repo: 3 steps on your side (~5 min)

Hi `<first-name>`,

You ran `/gse:deploy` and the GSE agent returned a **422** error from Coolify, flagging your **private GitHub repo** as the blocker. This is expected: Coolify cannot clone a private repo without explicit authorization from you. You have **3 small steps** left — Step 1 is a quick browser click, Steps 2 and 3 are just prompts to paste into your GSE orchestrator chat.

---

### Step 1 — Install the GitHub App on your GitHub account (~2 min, browser)

This step involves a GitHub login, so it has to happen in your browser — your IDE agent cannot do it for you.

1. Open this link in your browser:
   **`https://github.com/apps/<APP-SLUG>/installations/new`**
2. GitHub asks which account to install the App on. **Choose your personal GitHub account** (the one that owns the repo you want to deploy).
3. On the next screen, two scope options appear:
   - Do **NOT** pick "All repositories" (scope too broad).
   - Pick **"Only select repositories"**.
4. In the list that appears, **tick only the repo you want to deploy** (the one you passed to `--github-repo` in the `deploy-app` command the agent generated).
5. Click the green **Install** button at the bottom.

**Your privacy guarantees stay full:** your repo remains private, the App has **only read access** (Contents: Read, Metadata: Read, Pull requests: Read) on the repo you ticked, and **only you** can revoke that access at any time from `github.com/settings/installations`.

---

### Step 2 — Ask your GSE orchestrator to persist the Coolify Source UUID (~30 s)

In your IDE (Cursor, Claude Code, or opencode — wherever you installed GSE-One), at the root of your project, **paste this prompt** to the GSE orchestrator chat:

> I just installed the trainer's GitHub App on my GitHub account to authorize Coolify access to my private repo. Please persist the Coolify Source UUID `<SOURCE-UUID>` into the `COOLIFY_GITHUB_APP_UUID` variable of my project's `.env`, using the `deploy.py env-set` subcommand (or the equivalent routing for my install mode). Then show me the resulting `.env` line so I can confirm it was written correctly.

The orchestrator will adopt the `deploy-operator` role, resolve the correct `deploy.py` path for your install (`.cursor/tools/`, `.claude/tools/`, plugin-mode, etc.), run the persistence, and read back the updated `.env` entry. No need to touch a terminal or know any path.

---

### Step 3 — Ask the orchestrator to relaunch the deployment sequentially

Still in your IDE chat, **paste this prompt**:

> Please re-run the `/gse:deploy` Phase 6 step for my application(s). My prior attempt failed with a Coolify `422` because my repo was private; I have now installed the GitHub App (Step 1) and `COOLIFY_GITHUB_APP_UUID` is set in `.env` (Step 2). Use the exact same `deploy-app` parameters you generated earlier (check our previous conversation for `--name`, `--subdomain`, `--github-repo`, `--branch`, `--type`, `--port` — or read them from `.gse/deploy.json → applications[]` if available). If I have multiple apps to deploy, run them **one at a time, sequentially** — wait for each to return a `healthy` health check AND print its final URL before starting the next. Do NOT parallelize. Report back each app's URL when it becomes healthy.

The orchestrator recovers the prior parameters, confirms them with you if it has any ambiguity, then executes each `deploy-app` in series — waiting on the health check between them. This **sequential** constraint is important: parallel invocations can create duplicate Coolify projects (it already happened once in your session history — ask your trainer if you want the explanation).

---

### If 422 still persists after Step 3

Four possible causes. For each, paste the suggested prompt to your orchestrator rather than running commands yourself.

**Cause 1 — GitHub App was marked as private (trainer-side fix needed)**

Symptom during Step 1: GitHub shows *"This GitHub App is marked as private and cannot be installed on this account"*. You cannot fix this yourself — only the trainer (App owner) can toggle it. Send your trainer a quick message:

> The install link showed "This GitHub App is marked as private" — can you flip the visibility to public on your end? Takes ~30 seconds.

**Cause 2 — App was not actually installed**

Prompt your orchestrator:

> Check whether the GitHub App `<APP-SLUG>` is installed on my GitHub account, and if so which repositories it has access to. Use the `gh` CLI (`gh api /user/installations` should give a list — the installation we care about is the one whose `app_slug` equals `<APP-SLUG>`).

The orchestrator will query GitHub and tell you whether the install is present and what repos it covers. If missing → redo Step 1.

**Cause 3 — Your target repo was not ticked during install**

Prompt your orchestrator:

> Show me which repositories the `<APP-SLUG>` App installation on my GitHub account has access to. If my target repo is missing, explain how to add it.

Typically the orchestrator will direct you to `github.com/settings/installations` → click `<APP-SLUG>` → Configure → tick the repo → Save.

**Cause 4 — The UUID in `.env` is wrong**

Prompt your orchestrator:

> Show me the current value of `COOLIFY_GITHUB_APP_UUID` in my project's `.env`. I want to compare it to the reference UUID my trainer gave me.

The orchestrator will read `.env` via `deploy.py env-get` and display the value. Compare against `<SOURCE-UUID>` — no leading/trailing whitespace, no quotes, no accidentally-copied surrounding URL fragment.

If none of the above resolves the 422, send your trainer the exact error message (screenshot or copy-paste of the orchestrator chat around the failure). The trainer may need to fall back to creating the Coolify application via the UI manually — this is an acknowledged gap in v0.62.3 (see section E below).

Happy deploying!

Your Trainer

---

## C. Trainer-side observability while the learner is acting

As the learner executes step 1 (Install), two things happen that you can watch from your side:

1. **GitHub → App Advanced tab → Recent Deliveries**: a new `installation.created` event appears with a green checkmark. URL: `https://github.com/settings/apps/<APP-SLUG>/advanced`.
2. **Coolify → Sources → Your App**: a new Installations row appears for the learner's GitHub account, listing the repo they ticked. URL: `https://<your-coolify>/source/github/<SOURCE-UUID>`.

If neither appears within a few minutes of the learner saying "I clicked Install", the install likely failed silently on their side — ask for a screenshot of the GitHub page immediately after their Install click.

Once the learner runs step 3 (deploy-app), two new **Resources** rows appear under the same Source page (one per deployed app). You can follow the build logs live from the Coolify UI.

---

## D. Reuse for subsequent learners

For every new learner after this first one, the trainer does **nothing** in Coolify or GitHub. You simply send the same email template with the same `<APP-SLUG>` and `<SOURCE-UUID>` values. A single Source in Coolify supports N installations (one per learner account), with no limit.

If you want per-learner isolation, you could create multiple GitHub Apps (one per cohort), but this is usually unnecessary — each learner's installation is already scoped to their own repos and revocable independently.

---

## E. Future improvement — deploy.py auto-detection

As of GSE-One v0.62.3, the Python tool `deploy.py` **does not yet** dispatch to the Coolify `/applications/private-github-app` endpoint when `COOLIFY_GITHUB_APP_UUID` is set. The agent-level guidance in `src/agents/deploy-operator.md` + `src/activities/deploy.md` documents the troubleshooting flow, but the automated deployment for private repos is not end-to-end yet. A follow-up release will implement the Python side (new `create_private_github_app_application` method in `coolify_client.py` + routing in `deploy_app()`).

Until then, this document provides the documented manual-unblock path. Track the follow-up as part of Scope B in the internal issue tracker (or see the `deploy-operator.md` anti-pattern note on private repos for pointers).
