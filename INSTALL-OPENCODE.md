# GSE-One — opencode Install Guide

This document covers **only the opencode-specific install, upgrade, uninstall, and local-model setup**. For what GSE-One is, the list of commands, the architecture, and the full lifecycle, see [README.md](README.md) and [gse-one-spec.md](gse-one-spec.md).

---

## 1. Prerequisites

- **opencode** on your `PATH` — check with `opencode --version`. Install: https://opencode.ai
- **Python 3** — ships with macOS and Linux; on Windows use `python`.
- **git** — to clone this repo.

No Node.js, npm, or Bun install required — opencode runs the TS guardrails plugin itself.

---

## 2. Install

### Quick install (curl | sh) — recommended

For most users, the curl one-liner sets up GSE-One for opencode (and any other coding agent on `PATH`) in one command, no clone needed:

```bash
curl -fsSL https://raw.githubusercontent.com/nicolasguelfi/gensem/main/install.sh | sh
```

By default this is no-plugin mode into the current directory (Mode A below). To use the global plugin mode (Mode B below), set `GSE_MODE=plugin` before piping into `sh`. To restrict to opencode only, set `GSE_PLATFORM=opencode`. Full env-var reference: [root README](README.md#environment-variables).

### Manual install (clone + install.py)

For maintainers, forks, or environments without `curl`/`tar`/`python3 ≥ 3.8` on PATH, pick one mode below. **Mode A** is simplest for a single project; **Mode B** gives every project access to GSE-One.

### Mode A — Non-plugin (per-project)

```bash
git clone https://github.com/nicolasguelfi/gensem.git
cd gensem
python3 install.py --platform opencode --mode no-plugin --project-dir /path/to/your-project
```

Writes `<project>/.opencode/` + `AGENTS.md` + `opencode.json` at the project root. The only file outside the project is a 1-line `~/.gse-one` registry.

### Mode B — Plugin (global, `~/.config/opencode/`)

```bash
git clone https://github.com/nicolasguelfi/gensem.git
cd gensem
python3 install.py --platform opencode --mode plugin
```

### Interactive (auto-detects everything)

```bash
python3 install.py
```

After install, launch `opencode` in your project and type `/gse-go`.

---

## 3. Files written

| File | Mode A | Mode B |
|------|:------:|:------:|
| `<project>/.opencode/{skills,commands,agents,plugins}/` | ✓ | — |
| `<project>/AGENTS.md` (GSE block between `<!-- GSE-ONE START -->` / `<!-- GSE-ONE END -->`) | ✓ | — |
| `<project>/opencode.json` (deep-merged) | ✓ | — |
| `~/.config/opencode/{skills,commands,agents,plugins}/` | — | ✓ |
| `~/.config/opencode/AGENTS.md` | — | ✓ |
| `~/.config/opencode/opencode.json` (deep-merged) | — | ✓ |
| `~/.gse-one` (1-line path registry) | ✓ | ✓ |

User content outside the GSE-ONE markers is preserved on reinstall and fully restored on uninstall. `opencode.json` deep-merge never overwrites your keys.

---

## 4. Upgrade

```bash
cd /path/to/gensem && git pull
cd gse-one && python3 gse_generate.py --verify
cd .. && python3 install.py --platform opencode --mode <your-mode> [--project-dir /path/to/your-project]
```

Reinstall is idempotent (surgical block replace + deep merge).

---

## 5. Uninstall

```bash
python3 install.py --uninstall --platform opencode --mode <your-mode> [--project-dir /path/to/your-project]
```

`AGENTS.md` loses its GSE block (file deleted if empty); `opencode.json` loses the GSE-added keys (file deleted if only `$schema` remains); `~/.gse-one` is removed.

---

## 6. Run opencode with a local model (Ollama / LM Studio)

opencode talks to any OpenAI-compatible endpoint, so Ollama and LM Studio both work out of the box. Use this if you want **privacy**, **zero API cost**, or **offline** operation.

### 6.1 Recommended coding models (April 2026)

opencode runs an agentic loop with tool calls. A model that can't reliably call tools will silently fail. **Context window ≥ 64 k tokens** is strongly recommended by the opencode docs (GSE-One loads the orchestrator body into every session via `AGENTS.md`).

The three tables below cover the three realistic sourcing options: run it **locally** on your machine, pull it from an **open-weight cloud endpoint** (when self-hosting isn't practical), or go through **OpenRouter** (one account, any model). All three tables are sorted descending by SWE-bench Verified.

**Features column legend:** `tools` = function/tool calling · `vision` = image input · `thinking` = explicit reasoning mode · `agentic` = optimized for multi-turn agent workflows · `websearch` = built-in search tool · `FIM` = fill-in-the-middle (inline completion) · `long-ctx` = context ≥ 500 k · `multi-agent` = runs parallel sub-agents.

#### 6.1.1 Recommended local coding models

Covers the full range from laptop (8 GB VRAM) to workstation (≥ 128 GB). All tags are available on Ollama; `ollama pull <tag>` fetches them. On Apple Silicon prefer the **MLX** runtime (via LM Studio) — 20–30 % faster than llama.cpp on 30 B+ models.

| Model (Ollama tag) | Org | Params | Min VRAM/RAM | SWE-bench V. | Context | GSE-One fit | Features | Best for / Notes |
|---|---|---|---|---|---|:---:|---|---|
| `qwen3.6:35b-a3b` | Alibaba | 35 B MoE (3 B active) | 20 GB (Q4) | **73.4 %** | 256 k | ★★★★★ | tools, vision, thinking, agentic | **New top local pick.** Frontier-class SWE score on mid-range hardware. Default for most GSE-One users. |
| `qwen3.5:27b` | Alibaba | 27 B dense | 17 GB (Q4) / 24 GB (Q6) | 72.4 % | 256 k | ★★★★★ | tools, thinking | Best dense model that fits 24 GB VRAM. No MoE overhead — predictable latency. |
| `qwen3.5:122b-a10b` | Alibaba | 122 B MoE (10 B active) | 81 GB (Q4) | 72.0 % | 256 k | ★★★★☆ | tools, thinking, agentic | **128 GB tier.** Highest local SWE score before you need cloud. |
| `qwen3.5:35b-a3b` | Alibaba | 35 B MoE (3 B active) | 20 GB (Q4) | 69.2 % | 256 k | ★★★★☆ | tools, thinking | Previous generation of the top pick — still excellent if your Ollama mirror hasn't synced 3.6. |
| `qwen3:235b-a22b` | Alibaba | 235 B MoE (22 B active) | 120 GB (Q4) | ~68 % | 262 k | ★★★★☆ | tools, thinking, agentic | **128 GB tier, very tight.** Keep context ≤ 32 k. |
| `qwen2.5-coder:72b` | Alibaba | 72 B dense | 75 GB (Q8) | ~65 % | 128 k | ★★★★☆ | tools | **128 GB tier.** Python-first coding specialist. |
| `llama3.3:70b` | Meta | 70 B dense | 32 GB (Q4) / 75 GB (Q8) | ~58 % | 128 k | ★★★★☆ | tools, multilingual | GPT-4-class generalist. Q8 version is a 128 GB-tier quality bump. |
| `deepseek-r1:70b` | DeepSeek | 70 B dense (distill) | 32 GB (Q4) / 75 GB (Q8) | ~60 % | 128 k | ★★★☆☆ | thinking | Reasoner — pair with a coder model for `/gse-review`, `/gse-design`. Not a primary coder. |
| `qwen3-coder` (Qwen3-Coder-Next) | Alibaba | 80 B MoE (3 B active) | 8 GB | SWE-Pro ~39 % | 262 k | ★★★☆☆ | tools, agentic, long-ctx | Cheapest decent agentic coder. Weaker on SWE-V than Qwen 3.5/3.6 — use as a fallback. |
| `qwen2.5-coder:32b` | Alibaba | 32 B dense | 24 GB (Q4) | ~55 % | 128 k | ★★★☆☆ | tools | Older but well-understood workhorse. |
| `mistral-large:123b` | Mistral | 123 B dense | 85 GB (Q5) | ~55 % | 128 k | ★★★☆☆ | tools | **128 GB tier.** Long-context generalist. |
| `llama4-scout` | Meta | 109 B MoE (17 B active) | 85 GB (Q6) | — | **10 M** | ★★★☆☆ | tools, vision, long-ctx | **128 GB tier.** Extreme context for whole-repo analysis. |
| `devstral-small:24b` | Mistral | 24 B dense | 16 GB (Q4) | ~55 % | 128 k | ★★★☆☆ | tools, agentic | Lightweight agentic option. Degrades on multi-file edits. |
| `gpt-oss:20b` | OpenAI (OSS) | 20 B dense | 16 GB (Q4) | ~55 % | 128 k | ★★★☆☆ | tools, thinking | Enable high-thinking mode for agentic reliability. |
| `codestral:22b` | Mistral | 22 B dense | 16 GB (Q4) | SWE-Pro ~2 % | 256 k | ★★☆☆☆ | FIM | **Autocomplete only** — not for full agentic flows. 86.6 % HumanEval. |

**Out of local reach even at 128 GB** (for reference): `qwen3-coder:480b-a35b` (~240 GB Q4, ≥ 180 GB RAM required), `deepseek-v3.2` / `deepseek-r1:671b` full (~400 GB). Use Table 6.1.2 instead.

#### 6.1.2 Frontier open-weight models (via a cloud endpoint)

Open-weight models too large to self-host on consumer hardware. opencode reaches them through any OpenAI-compatible endpoint (vendor API, Together.ai, Groq, DeepInfra, SiliconFlow, etc.). "Min VRAM/RAM" below is the figure to self-host at Q4; you'll almost always want the hosted API.

| Model | Org | Params | Min VRAM/RAM | SWE-bench V. | Context | GSE-One fit | Features | Best for / Notes |
|---|---|---|---|---|---|:---:|---|---|
| **MiniMax M2.5** | MiniMax | undisclosed MoE | cloud-only | **80.2 %** | 192 k | ★★★★★ | tools, agentic, thinking | Current open-weight leader on SWE-bench Verified. |
| **MiMo-V2-Pro** | Xiaomi | 1 T MoE (42 B active) | ~500 GB | 78.0 % | **1 M** | ★★★★★ | tools, vision, agentic, long-ctx | Agent-first design with huge context. |
| **GLM-5** | Z.AI (Zhipu) | undisclosed large MoE | cloud-only | 77.8 % | 128 k | ★★★★★ | tools, agentic, thinking | Top scorer on SWE-bench Pro and Terminal Bench among open weights. |
| **Kimi K2.5** | Moonshot AI | ~1 T MoE | ~500 GB | 76.8 % | 256 k | ★★★★☆ | tools, agentic | 85 % LiveCodeBench; strong front-end / competitive programming. |
| **Qwen3.5-397B-A17B** | Alibaba | 397 B MoE (17 B active) | 222 GB (Q4) | 76.4 % | 256 k | ★★★★☆ | tools, thinking, agentic | Largest MoE in Qwen3.5 lineup. |
| **MiMo-V2-Omni** | Xiaomi | large MoE (undisclosed) | cloud-only | 74.8 % | 256 k | ★★★★☆ | tools, vision, audio, agentic | Omnimodal — voice/image inputs in addition to text. |
| **Step-3.5-Flash** | StepFun | undisclosed | cloud-only | 74.4 % | 128 k | ★★★★☆ | tools, agentic | Balanced all-rounder; cheaper/faster than 1 T-class models. |
| **GLM-4.7** | Z.AI (Zhipu) | undisclosed | cloud-only | 73.8 % | 128 k | ★★★★☆ | tools, thinking, agentic | "Cleanest all-around coding profile" per community reviews; 94.2 HumanEval. |
| **MiMo-V2-Flash** | Xiaomi | 309 B MoE (15 B active) | 180 GB (Q4) | 73.4 % | 256 k | ★★★★☆ | tools, thinking, agentic | Cheapest to host in the 300 B class; strong on SWE-Multilingual. |
| **DeepSeek V3.2** | DeepSeek | 671 B MoE (37 B active) | 370 GB (Q4) | 73.1 % | 128 k | ★★★★★ | tools, thinking | **Workhorse:** 90 % of frontier quality for a tiny fraction of cost. Default for `/gse-produce`. |
| **Qwen3-Coder-480B-A35B** | Alibaba | 480 B MoE (35 B active) | 240 GB (Q4) | SWE-Pro 38.7 % | 256 k | ★★★☆☆ | tools, agentic | Best **pure** open coding specialist; pair with a stronger SWE-V reviewer. |
| **DeepSeek R1** (full) | DeepSeek | 671 B MoE (37 B active) | 400 GB (Q4) | 49.2 % | 128 k | ★★★☆☆ | thinking, agentic | Reviewer model: chain-of-thought catches issues coder models miss. |

**How to wire opencode** — add a provider block to `opencode.json` with the `@ai-sdk/openai-compatible` adapter, and point `baseURL` at the host of your choice (e.g. `https://api.deepseek.com/v1`, `https://api.together.xyz/v1`, `https://api.moonshot.cn/v1`). Put the API key in `options.apiKey` (prefer `{env:VAR}`).

#### 6.1.3 Best SWE / coding models on OpenRouter

[OpenRouter](https://openrouter.ai) gives you a single API key, a single endpoint, and `/models` in opencode for switching. Prices reflect April 2026. `Min VRAM/RAM` below shows what's needed *to self-host* the underlying weights — irrelevant for day-to-day OpenRouter use.

**Config snippet** — add to `opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openrouter": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenRouter",
      "options": {
        "baseURL": "https://openrouter.ai/api/v1",
        "apiKey": "{env:OPENROUTER_API_KEY}"
      },
      "models": {
        "anthropic/claude-opus-4.7":       { "name": "Claude Opus 4.7" },
        "anthropic/claude-opus-4.6":       { "name": "Claude Opus 4.6" },
        "google/gemini-3.1-pro-preview":   { "name": "Gemini 3.1 Pro" },
        "minimax/minimax-m2.5":            { "name": "MiniMax M2.5" },
        "openai/gpt-5.2":                  { "name": "GPT-5.2" },
        "anthropic/claude-sonnet-4.6":     { "name": "Claude Sonnet 4.6" },
        "qwen/qwen3.6-plus":               { "name": "Qwen3.6 Plus" },
        "z-ai/glm-5":                      { "name": "GLM-5 (Z.AI)" },
        "moonshotai/kimi-k2.5":            { "name": "Kimi K2.5" },
        "x-ai/grok-4.20":                  { "name": "Grok 4.20" },
        "xiaomi/mimo-v2-flash":            { "name": "MiMo-V2-Flash" },
        "anthropic/claude-haiku-4.5":      { "name": "Claude Haiku 4.5" },
        "deepseek/deepseek-v3.2":          { "name": "DeepSeek V3.2" },
        "mistralai/devstral-medium":       { "name": "Devstral Medium" },
        "mistralai/codestral-2508":        { "name": "Codestral 25.08 (FIM)" }
      }
    }
  }
}
```

Then `export OPENROUTER_API_KEY=sk-or-…` before launching opencode.

| OpenRouter ID | Org | Params | Min VRAM/RAM | SWE-bench V. | Context | GSE-One fit | Features | Best for / Notes |
|---|---|---|---|---|---|:---:|---|---|
| `anthropic/claude-opus-4.7` | Anthropic | undisclosed | cloud-only | **87.6 %** | 1 M | ★★★★★ | tools, vision, thinking, agentic | **Highest SWE-V of any model here.** Default for `/gse-review`, `/gse-design`. $5 / $25 per M. |
| `anthropic/claude-opus-4.6` | Anthropic | undisclosed | cloud-only | 80.8 % | 1 M | ★★★★★ | tools, vision, thinking, agentic | Previous Opus — use if 4.7 unavailable. $5 / $25. |
| `google/gemini-3.1-pro-preview` | Google | undisclosed | cloud-only | 80.6 % | ~1 M | ★★★★★ | tools, vision, thinking, websearch | Google's frontier; built-in websearch helps `/gse-collect`. |
| `minimax/minimax-m2.5` | MiniMax | undisclosed MoE | cloud-only | 80.2 % | 197 k | ★★★★★ | tools, agentic, thinking | **Best open-weight / price ratio.** $0.12 / $0.99. |
| `openai/gpt-5.2` | OpenAI | undisclosed | cloud-only | 80.0 % | 400 k | ★★★★★ | tools, vision, thinking, websearch, agentic | Strong all-rounder; 400 k context. $1.75 / $14. |
| `anthropic/claude-sonnet-4.6` | Anthropic | undisclosed | cloud-only | 79.6 % | 1 M | ★★★★★ | tools, vision, thinking, agentic | Best Claude quality/price. Default coder for full GSE-One cycle. $3 / $15. |
| `qwen/qwen3.6-plus` | Alibaba | undisclosed MoE | cloud-only | 78.8 % | 1 M | ★★★★☆ | tools, vision, thinking | Hybrid linear + sparse MoE; aggressively priced. $0.325 / $1.95. |
| `z-ai/glm-5` | Z.AI (Zhipu) | undisclosed large | cloud-only | 77.8 % | 80 k | ★★★★☆ | tools, agentic, thinking | Top open-weight on SWE-Pro. $0.72 / $2.30. Short context is the main tradeoff. |
| `moonshotai/kimi-k2.5` | Moonshot AI | ~1 T MoE | cloud-only | 76.8 % | 256 k | ★★★★☆ | tools, agentic | Front-end specialist; 85 % LiveCodeBench. |
| `x-ai/grok-4.20` | xAI | undisclosed | cloud-only | 76.7 % | **2 M** | ★★★★☆ | tools, vision, multi-agent, long-ctx | 2 M context; runs 4 parallel sub-agents. $2 / $6. |
| `google/gemini-3-pro-preview` | Google | undisclosed | cloud-only | 76.2 % | ~1 M | ★★★★☆ | tools, vision, thinking, websearch | Previous-gen Gemini Pro; solid fallback when 3.1 rate-limited. |
| `xiaomi/mimo-v2-flash` | Xiaomi | 309 B MoE (15 B active) | 180 GB (self-host) | 73.4 % | 256 k | ★★★★☆ | tools, thinking, agentic | **Cheapest in the table.** $0.09 / $0.29. |
| `anthropic/claude-haiku-4.5` | Anthropic | undisclosed | cloud-only | 73.3 % | 200 k | ★★★★☆ | tools, vision, agentic | Near-frontier at Haiku price. Ideal for `/gse-status`, `/gse-go`, routine `/gse-produce`. $1 / $5. |
| `deepseek/deepseek-v3.2` | DeepSeek | 671 B MoE (37 B active) | 370 GB (self-host) | 73.1 % | 164 k | ★★★★★ | tools, thinking | **Best cost/quality** on the entire table. $0.26 / $0.42. Default for `/gse-produce`. |
| `mistralai/devstral-medium` | Mistral | undisclosed | cloud-only | 61.6 % | 128 k | ★★★★☆ | tools, agentic | Dedicated agentic coder; beats Gemini 2.5 Pro and GPT-4.1 on SWE-bench. $0.40 / $2. |

> **Legend — GSE-One fit stars:** ★★★★★ excellent across all 23 activities (default pick) · ★★★★☆ strong, minor tradeoff (e.g. shorter context, one weaker activity) · ★★★☆☆ works for a subset of activities (pair with a complementary model) · ★★☆☆☆ niche only — not recommended as primary · ★☆☆☆☆ avoid for GSE-One. Ratings weight **tool-calling reliability**, **context ≥ 128 k**, **SWE-bench Verified**, and **multi-step reasoning** — the four capabilities GSE-One relies on for its full lifecycle.

**Also worth knowing on OpenRouter (below the top 15):** `mistralai/devstral-2512` (~60 % SWE-V, open Apache-2.0, 256 k), `mistralai/mistral-large-2512` (~65 %), `mistralai/codestral-2508` (SWE-Pro ~2 % — FIM specialist, not agentic), `qwen/qwen3-coder` (Apache-2.0, often available on a free tier with rate limits), `mistralai/devstral-small` (cheapest agentic).

**Picking for GSE-One (cross-table):**

- **Absolute top quality, cost no object:** `anthropic/claude-opus-4.7` (87.6 %) or `openai/gpt-5.3-codex` if it appears on OpenRouter (85 %, not yet listed at the time of writing).
- **Best balance for the full 23-activity lifecycle:** `anthropic/claude-sonnet-4.6` or `minimax/minimax-m2.5`.
- **Cheapest frontier quality:** `deepseek/deepseek-v3.2` or `xiaomi/mimo-v2-flash`.
- **All local, privacy-first:** `qwen3.6:35b-a3b` (20 GB VRAM, 73.4 % SWE-V) — no data leaves your machine.
- **Per-activity split (advanced):** cheap local coder for `/gse-produce` (e.g. `qwen3.5:27b`) + cloud reviewer for `/gse-review` (e.g. `claude-opus-4.7`). Switch with opencode's `variant_cycle` keybind.

Scores above come from vendor reports, [Scale SWE-Bench Pro Leaderboard](https://labs.scale.com/leaderboard/swe_bench_pro_public), [SWE-bench.com](https://www.swebench.com/), [BenchLM](https://benchlm.ai/benchmarks/sweVerified) and [LLM-Stats](https://llm-stats.com/benchmarks/swe-bench-verified) as of April 2026; numbers shift monthly — recheck the leaderboards before committing to a stack.

### 6.2 Option A — Ollama

```bash
# Install Ollama (macOS example)
brew install ollama
ollama serve &                       # background server on :11434

# Pull one of the recommended models
ollama pull qwen2.5-coder:32b        # or qwen3-coder, llama3.3:70b, etc.
```

Then add an Ollama provider to your opencode config. In **Mode A** edit `<project>/opencode.json`, in **Mode B** edit `~/.config/opencode/opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": { "baseURL": "http://localhost:11434/v1" },
      "models": {
        "qwen2.5-coder:32b": { "name": "Qwen 2.5 Coder 32B" }
      }
    }
  }
}
```

Launch opencode and type `/models` → pick **Qwen 2.5 Coder 32B**. To make it the default, add `"model": "ollama/qwen2.5-coder:32b"` at the top level of `opencode.json`.

> **Shortcut:** if you're on Ollama ≥ 0.5, `ollama launch opencode` passes a ready-made config via `OPENCODE_CONFIG_CONTENT` and deep-merges with your existing `opencode.json`.

### 6.3 Option B — LM Studio

1. Install LM Studio: https://lmstudio.ai
2. Download a recommended model from the Models tab (Qwen Coder, DeepSeek R1, etc.).
3. Open the **Developer** tab → **Start Server** (default port `1234`). Ensure the model is loaded.

Add the provider to `opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "lmstudio": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "LM Studio (local)",
      "options": { "baseURL": "http://127.0.0.1:1234/v1" },
      "models": {
        "qwen2.5-coder-32b-instruct": { "name": "Qwen 2.5 Coder 32B (LM Studio)" }
      }
    }
  }
}
```

Replace the model ID with whatever LM Studio reports for your loaded model (see its "Local Server" panel). In opencode: `/models` → LM Studio → pick it. No real API key is required; if prompted, enter any non-empty string.

### 6.4 Tuning for GSE-One agentic flow

- **Context ≥ 64k.** GSE-One loads the orchestrator body (~400 lines of methodology) into every session via `AGENTS.md`. Smaller contexts truncate it.
- **Temperature low.** `0.0–0.3` for deterministic tool calls. Most local engines respect `options.temperature` in the provider block.
- **Tool calling must be on.** Ollama exposes it by default for compatible models; LM Studio exposes it when you tick "Function Calling" in the server panel.
- **Watch VRAM.** The orchestrator + 1-2 open files + a long conversation can push past 32 GB on the 70B models. If the model starts hallucinating, check you're not being silently evicted to disk swap.
- **`websearch` needs a key when running local.** opencode's built-in `websearch` tool is only active when you use opencode's own cloud provider, **or** when you export `OPENCODE_ENABLE_EXA=1` plus an [Exa](https://exa.ai) API key (`EXA_API_KEY`). With Ollama or LM Studio alone, `websearch` is silently unavailable. `webfetch` (direct HTTP) works in all cases, so GSE-One activities that need to read a specific URL still run. Example shell setup:
  ```bash
  export OPENCODE_ENABLE_EXA=1
  export EXA_API_KEY=xxx   # from https://exa.ai
  ```

---

## 7. Troubleshooting

- **`/gse-*` commands missing** — check the `commands/` dir exists at the install target. Restart opencode.
- **Model ignores GSE-One methodology** — `AGENTS.md` lost its GSE block; reinstall. Or context window too small (try ≥ 64k).
- **"Skill skipped: missing name/description"** — regenerate: `cd gse-one && python3 gse_generate.py --verify`.
- **Guardrails don't fire on `git commit` on main** — `plugins/gse-guardrails.ts` missing or opencode version doesn't support `tool.execute.before`. Upgrade opencode.
- **Local model makes tool calls but never finishes the loop** — model is too weak for agentic work. Swap for a larger variant or one from §6.1.
- **`.claude/skills/` + `.opencode/skills/` coexist** — opencode loads both → duplicate commands. Installer warns at install time; remove one of the two.

---

## 8. References

- [README.md](README.md) — what GSE-One is, all three platforms, quickstart
- [gse-one-spec.md](gse-one-spec.md) — full methodology & 23-command reference
- [CHANGELOG.md](CHANGELOG.md)

**Model research sources (April 2026):**
- [opencode — Providers](https://opencode.ai/docs/providers/)
- [opencode — Models](https://opencode.ai/docs/models/)
- [opencode — Tools](https://opencode.ai/docs/tools/)
- [Ollama × opencode integration](https://docs.ollama.com/integrations/opencode)
- [Best Local AI Coding Models 2026](https://localaimaster.com/models/best-local-ai-coding-models)
- [Best LLMs for opencode — Tested Locally](https://dev.to/rosgluk/best-llms-for-opencode-tested-locally-499l)
- [OpenCode CLI Guide 2026 — Local LLMs](https://yuv.ai/learn/opencode-cli)
- [Best Local LLMs to Run On Every Apple Silicon Mac in 2026](https://apxml.com/posts/best-local-llms-apple-silicon-mac)
- [DeepSeek Models Guide — R1, V3, and Coder](https://insiderllm.com/guides/deepseek-models-guide/)
- [GPU Requirements Guide for DeepSeek Models](https://apxml.com/posts/system-requirements-deepseek-models)
- [Best AI for Coding 2026 — Real Benchmarks (MorphLLM)](https://www.morphllm.com/best-ai-model-for-coding)
- [Scale SWE-Bench Pro Leaderboard](https://labs.scale.com/leaderboard/swe_bench_pro_public)
- [SWE-bench Leaderboards](https://www.swebench.com/)
- [Best Open Source LLM 2026 (BenchLM)](https://benchlm.ai/blog/posts/best-open-source-llm)
- [Open Source LLM Leaderboard 2026 (Vellum)](https://www.vellum.ai/open-llm-leaderboard)
- [SWE-bench.com leaderboards](https://www.swebench.com/)
- [LLM-Stats — SWE-bench Verified](https://llm-stats.com/benchmarks/swe-bench-verified)
- [BenchLM — SWE-bench Verified rankings 2026](https://benchlm.ai/benchmarks/sweVerified)
- [OpenRouter — Best AI Models for Coding](https://openrouter.ai/collections/programming)
- [OpenRouter — Mistral models](https://openrouter.ai/mistralai)
- [OpenRouter rankings (April 2026)](https://www.digitalapplied.com/blog/openrouter-rankings-april-2026-top-ai-models-data)
- [Codestral 25.01 benchmarks review](https://www.index.dev/blog/mistral-ai-coding-challenges-tests)
- [Codestral Guide: Specs, Benchmarks & Local Deployment (2026)](https://ucstrategies.com/news/codestral-guide-specs-benchmarks-local-deployment-2026/)
