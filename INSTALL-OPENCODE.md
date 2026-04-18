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

Pick one mode. **Mode A** is simplest for a single project; **Mode B** gives every project access to GSE-One.

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

### 6.1 Recommended local coding models (April 2026)

opencode runs an agentic loop with tool calls. A model that can't reliably call tools will silently fail. Pick from this short list — all have been observed to work for opencode-style workflows. **Context window ≥ 64k tokens** is strongly recommended by the opencode docs.

#### 6.1.1 Commodity hardware (8–32 GB)

| Model (Ollama tag) | Params | Min VRAM/RAM | Notes |
|---|---|---|---|
| `qwen3-coder` (a.k.a. Qwen3-Coder-Next) | 80B MoE (3B active) | 8 GB | Best efficiency/quality ratio in 2026; designed for agent tool-calling. |
| `qwen2.5-coder:32b` | 32B dense | 24 GB | Python-first, strong code completion; the default "big local" option. |
| `llama3.3:70b` | 70B dense | 32 GB (Apple Silicon 48 GB+) | GPT-4-class generalist; slower but very strong on full-file edits. |
| `deepseek-r1:14b` | 14B dense | 16 GB | Chain-of-thought; excellent for debugging and code review. |
| `gpt-oss:20b` | 20B dense | 16 GB | OpenAI open-source; enable high-thinking mode for agent reliability. |
| `devstral-small-2:24b` | 24B dense | 16 GB | Good fallback when VRAM is tight; lighter than Qwen Coder 32B. |

**What to avoid for opencode:** Qwen 3 14B (plain), Devstral Small 2 in agent mode, GPT-OSS 20B in default (non-thinking) mode — reports of tool-call failures and instruction drift. Pick a larger or MoE variant if you have the VRAM.

Ollama tags evolve; run `ollama search coder` to see what's current.

#### 6.1.2 High-RAM workstations (≥ 128 GB)

With 128 GB of unified memory (Apple Silicon M3/M4 Max/Ultra) or a PC with 128 GB DDR5 + a capable GPU, you can run the frontier-class open models at quality-preserving quantization. On Apple Silicon, prefer the **MLX** runtime (LM Studio has a toggle; with Ollama stick to its default): it's consistently 20–30 % faster than llama.cpp on large models.

| Model (Ollama tag) | Total / Active | Recommended quant | RAM footprint | Notes |
|---|---|---|---|---|
| `qwen2.5-coder:72b` | 72B dense | Q8 | ~75 GB | **Best coding specialist at this tier.** Solid tool-calling, Python-first. |
| `llama3.3:70b` at Q8 | 70B dense | Q8 | ~75 GB | Bumping the 32 GB-tier pick to Q8 meaningfully improves complex reasoning and multi-file edits. |
| `deepseek-r1:70b` (distill) | 70B dense | Q8 | ~75 GB | R1-style chain-of-thought at 70B; pair with a coder model for best review/debug results. |
| `mistral-large:123b` | 123B dense | Q5 | ~85 GB | 128k context, strong generalist, well-behaved on tool calls. |
| `llama4-scout` | 109B MoE (17B active) | Q6 | ~85 GB | 10M-token context, multimodal, fast thanks to MoE — leave ~30 GB headroom for context. |
| `qwen3:235b-a22b` | 235B MoE (22B active) | Q4 | ~120 GB | Frontier-class general model; tight on 128 GB — keep context ≤ 32k and close other heavy apps. |

**Still out of reach at 128 GB** (for reference — don't try these without ≥ 180 GB):
- `qwen3-coder:480b-a35b` (Qwen3-Coder-480B) — ~240 GB at Q4, the current best open coding model but needs a multi-GPU rig or a 256 GB Mac Studio.
- `deepseek-v3` / `deepseek-r1:671b` (full 671B MoE) — ~400 GB at Q4; same story.

**Tips for 128 GB setups:**
- Budget 15–25 % of RAM for the KV cache (context) — a 32k context on a 70B model can add 6–10 GB on top of the weights.
- Running two models side-by-side (e.g. Qwen Coder for code + DeepSeek R1 for review) only works up to the combined footprint; unload one with `ollama stop <tag>` or LM Studio's "Eject" button before loading the other if you hit OOM.
- Expect 5–15 tok/s on an M3 Ultra 128 GB with a 70B model at Q8, 3–8 tok/s with a 120 B+ model.

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
