/** Behavioral tests of the generated adapters; no model, credentials, or network. */
import { afterEach, beforeEach, describe, expect, test } from "bun:test"
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { execFileSync } from "node:child_process"
import v1 from "../plugin/opencode/plugins/gse-guardrails"
import v2 from "../plugin/opencode/compat/gse-guardrails-v2"

for (const version of [1, 2]) describe(`OpenCode ${version}`, () => {
  let root: string, project: string, before: any, after: any
  let originalHome: string | undefined
  const git = (...args: string[]) => execFileSync("git", args, { cwd: project, stdio: "pipe" })
  const config = (value: string) => writeFileSync(join(project, ".gse/config.yaml"), value)
  const run = (command: string) => before(command)

  beforeEach(async () => {
    root = mkdtempSync(join(tmpdir(), "gse-opencode-"))
    project = join(root, "workdir")
    mkdirSync(join(project, ".gse"), { recursive: true })
    originalHome = process.env.HOME
    process.env.HOME = root // Never read the developer's machine registry.
    git("init", "-b", "main")
    if (version === 1) {
      const hooks = await v1({ directory: project } as any)
      before = (command: string) => hooks["tool.execute.before"]!(
        { tool: "bash" } as any, { args: { command, workdir: project } },
      )
      after = async (event: any) => {
        const result = { output: event.result.content ?? "" }
        await hooks["tool.execute.after"]!(
          { tool: event.tool === "shell" ? "bash" : event.tool, args: event.input } as any, result as any,
        )
        event.result.content = result.output
      }
    } else {
      const registrations: Record<string, any> = {}
      await v2.setup({
        location: { directory: project },
        shell: { hook: async (name: string, fn: any) => { registrations[`shell.${name}`] = fn } },
        tool: { hook: async (name: string, fn: any) => { registrations[`tool.${name}`] = fn } },
      })
      expect(Object.keys(registrations).sort()).toEqual(["shell.create.before", "tool.execute.after"])
      before = (command: string) => registrations["shell.create.before"]({ command, cwd: project })
      after = registrations["tool.execute.after"]
    }
  })
  afterEach(() => {
    if (originalHome === undefined) delete process.env.HOME
    else process.env.HOME = originalHome
    rmSync(root, { recursive: true, force: true })
  })

  test("blocks force push forms and honors the project toggle", async () => {
    for (const command of ["git push -4f", "git push -f4", "git push -fu", "git push -uf", "git push -vf", "git push -f", "git push --force", "git push --force-with-lease", "git push origin +HEAD:main"]) {
      await expect(run(command)).rejects.toThrow("EMERGENCY GUARDRAIL")
    }
    await run("git status --short")
    await run("git push origin feature")
    await run("git push -ofoo")
    await run("git push -vofoo")
    config("hooks:\n  block_force_push: false\n")
    await run("git push --force")
  })

  test("allows initialization, protects main, and respects branch/config exceptions", async () => {
    await run("git commit -m initial")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture")
    await expect(run("git commit -m blocked")).rejects.toThrow("Direct commit to main")
    for (const setting of ["hooks:\n  protect_main: false\n", "git:\n  strategy: none\n"]) {
      config(setting)
      await run("git commit -m allowed")
    }
    config("")
    for (const command of ["git -c user.name=Test commit -m blocked", "git -c user.name=Test -c user.email=t@t commit -m blocked", "git --no-pager commit -m blocked", "git status\ngit commit -m blocked", "  git commit -m blocked", "(git commit -m blocked)"]) {
      await expect(run(command)).rejects.toThrow("Direct commit to main")
    }
    git("checkout", "-b", "feature")
    await run("git commit -m allowed")
  })

  test("appends a model-visible warning using relative and absolute workdir", async () => {
    writeFileSync(join(project, ".gse/status.yaml"), "review_findings_open: 3\n")
    for (const workdir of [".", project]) {
      const event = { status: "completed", tool: "shell", input: { command: "git push origin feature", workdir }, result: { content: "original", metadata: { keep: true } } }
      await after(event)
      expect(event.result.content).toBe("original\nWARNING: 3 open review findings")
      expect(event.result.metadata).toEqual({ keep: true })
      config("hooks:\n  review_findings_on_push: false\n")
      event.result.content = "original"
      await after(event)
      expect(event.result.content).toBe("original")
      config("")
    }
  })

  test("ignores missing/zero findings and unrelated commands", async () => {
    const event = { status: "completed", tool: "shell", input: { command: "git push", workdir: project }, result: { content: "original" } }
    await after(event)
    expect(event.result.content).toBe("original")
    writeFileSync(join(project, ".gse/status.yaml"), "review_findings_open: 0\n")
    await after(event)
    expect(event.result.content).toBe("original")
    writeFileSync(join(project, ".gse/status.yaml"), "review_findings_open: 3\n")
    event.input.command = "git status"
    await after(event)
    expect(event.result.content).toBe("original")
  })

  test("subdirectory workdir keeps project config and status authoritative", async () => {
    const child = join(project, "src")
    mkdirSync(join(child, ".gse"), { recursive: true })
    writeFileSync(join(child, ".gse/config.yaml"), "hooks:\n  block_force_push: false\n")
    let guard: any, post: any
    if (version === 1) {
      const h = await v1({ directory: project } as any)
      guard = (command: string) => h["tool.execute.before"]!({ tool: "bash" } as any, { args: { command, workdir: child } })
      post = async () => { const o = { output: "original" }; await h["tool.execute.after"]!({ tool: "bash", args: { command: "git push", workdir: child } } as any, o as any); return o.output }
    } else {
      const h: any = {}
      await v2.setup({ location: { directory: project }, shell: { hook: async (_: string, f: any) => { h.before = f } }, tool: { hook: async (_: string, f: any) => { h.after = f } } })
      guard = (command: string) => h.before({ command, cwd: child })
      post = async () => { const e = { status: "completed", tool: "shell", input: { command: "git push", workdir: child }, result: { content: "original" } }; await h.after(e); return e.result.content }
    }
    await expect(guard("git push --force")).rejects.toThrow("EMERGENCY GUARDRAIL")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture")
    config("hooks:\n  protect_main: false\n")
    await guard("git commit -m allowed")
    writeFileSync(join(project, ".gse/status.yaml"), "review_findings_open: 3\n")
    expect(await post()).toContain("WARNING: 3 open review findings")
  })

  test("allows initialization command in a directory without Git metadata", async () => {
    rmSync(join(project, ".git"), { recursive: true })
    await run("git init && git commit --allow-empty -m initial")
  })

  test("refreshes dashboard in plugin directory and records failure without blocking edits", async () => {
    mkdirSync(join(project, "assets/tools"), { recursive: true })
    writeFileSync(join(project, ".gse/registry"), join(project, "assets"))
    const script = join(project, "assets/tools/dashboard.py")
    writeFileSync(script, "from pathlib import Path\nPath('dashboard-ran').write_text('ok')\n")
    for (const tool of ["edit", "write", "apply_patch"]) {
      await after({ status: "completed", tool, input: {}, result: {} })
      expect(readFileSync(join(project, "dashboard-ran"), "utf8")).toBe("ok")
      rmSync(join(project, "dashboard-ran"))
    }
    // Machine registry fallback is kept for machine and sandbox installs.
    rmSync(join(project, ".gse/registry"))
    writeFileSync(join(root, ".gse-one"), join(project, "assets"))
    await after({ status: "completed", tool: "write", input: {}, result: {} })
    expect(existsSync(join(project, "dashboard-ran"))).toBe(true)
    writeFileSync(script, 'raise RuntimeError("fixture failure")\n')
    await after({ status: "completed", tool: "write", input: {}, result: {} })
    expect(readFileSync(join(project, ".gse/.dashboard-error.yaml"), "utf8")).toContain("fixture failure")
  })

  if (version === 2) {
    test("preserves structured content, metadata, and output", async () => {
      writeFileSync(join(project, ".gse/status.yaml"), "review_findings_open: 3\n")
      for (const content of [undefined, [{ type: "text", text: "original" }, { type: "file", uri: "file:///fixture", mime: "text/plain" }]]) {
        const event = { status: "completed", tool: "shell", input: { command: "git push", workdir: project }, result: { content, output: { keep: true }, metadata: { keep: true } } }
        await after(event)
        expect(event.result.content).toEqual([...(content ?? []), { type: "text", text: "WARNING: 3 open review findings" }])
        expect(event.result.output).toEqual({ keep: true })
        expect(event.result.metadata).toEqual({ keep: true })
      }
    })
    test("ignores failed tool executions", async () => {
      mkdirSync(join(project, "assets/tools"), { recursive: true })
      writeFileSync(join(project, ".gse/registry"), "assets")
      writeFileSync(join(project, "assets/tools/dashboard.py"), 'raise RuntimeError("must not run")\n')
      writeFileSync(join(project, ".gse/status.yaml"), "review_findings_open: 3\n")
      await after({ status: "error", tool: "shell", input: { command: "git push", workdir: project }, error: "fixture" })
      await after({ status: "error", tool: "write", error: "fixture" })
      expect(existsSync(join(project, ".gse/.dashboard-error.yaml"))).toBe(false)
    })
  }
})
