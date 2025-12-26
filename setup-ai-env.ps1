<#  setup-ai-env.ps1
    One-shot Windows setup + project scaffolding for:
    - Claude Code (native installer on Windows / install.sh in WSL)
    - OpenAI Codex CLI (@openai/codex)
    - Google Gemini CLI (@google/gemini-cli)
    - Minimal best-practice project files: .claude/*, CLAUDE.md, AGENTS.md, docs/*
    - Optional WSL bootstrap
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$ProjectPath,

  [ValidateSet("WSL","Native")]
  [string]$Mode = "WSL",

  [string]$WslDistro = "Ubuntu",

  [switch]$InstallWSL,
  [switch]$ResetWslDistro,         # DANGEROUS: unregisters distro (data loss)
  [switch]$SkipInstalls,           # Only generate project scaffolding/config
  [switch]$WithMcpFilesystem        # Create .mcp.json (filesystem MCP server template)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section([string]$Title) {
  Write-Host ""
  Write-Host "==================== $Title ====================" -ForegroundColor Cyan
}

function Assert-Admin([string]$Why) {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    throw "Need Administrator PowerShell for: $Why. Re-run PowerShell as Admin."
  }
}

function Test-Cmd([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}

function Write-File([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  Ensure-Dir $dir
  Set-Content -Path $Path -Value $Content -Encoding UTF8
}

function Ensure-Winget() {
  if (-not (Test-Cmd "winget")) {
    throw "winget not found. Install 'App Installer' from Microsoft Store, then re-run."
  }
}

function Winget-Install([string]$Id, [string]$Label) {
  Write-Host "Installing: $Label ($Id)"
  & winget install --id $Id -e --source winget --accept-package-agreements --accept-source-agreements | Out-Null
}

function Run-WSL([string]$BashCmd) {
  # Use bash -lc to load profile and keep it simple
  & wsl.exe -d $WslDistro -- bash -lc $BashCmd
}

function Assert-ProjectPath() {
  $resolved = (Resolve-Path $ProjectPath).Path
  $script:ProjectPath = $resolved
  if (-not (Test-Path $script:ProjectPath)) { throw "ProjectPath not found: $script:ProjectPath" }
}

function Install-Native-Tools() {
  Write-Section "Native installs (Windows)"
  Ensure-Winget

  # Essentials
  if (-not (Test-Cmd "git")) { Winget-Install "Git.Git" "Git for Windows" }
  if (-not (Test-Cmd "node")) { Winget-Install "OpenJS.NodeJS.LTS" "Node.js LTS" }

  # Claude Code (native installer recommended)
  if (-not (Test-Cmd "claude")) {
    Write-Host "Installing Claude Code (native installer)..."
    # Official installer via irm (PowerShell)
    & powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
  }

  # npm CLIs
  if (-not (Test-Cmd "npm")) { throw "npm missing even after Node install. Restart terminal and re-run." }

  if (-not (Test-Cmd "codex")) {
    Write-Host "Installing Codex CLI..."
    & npm i -g @openai/codex | Out-Null
  }
  if (-not (Test-Cmd "gemini")) {
    Write-Host "Installing Gemini CLI..."
    & npm i -g @google/gemini-cli | Out-Null
  }

  # Configure CLAUDE_CODE_GIT_BASH_PATH for native + Git Bash integration (optional but helpful)
  $gitBash = "C:\Program Files\Git\bin\bash.exe"
  if (Test-Path $gitBash) {
    [Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", $gitBash, "User")
  }
}

function Install-WSL-And-Tools() {
  Write-Section "WSL installs"
  Ensure-Winget
  Assert-Admin "WSL installation / distro management"

  if ($ResetWslDistro) {
    Write-Host "RESET requested: Unregistering WSL distro '$WslDistro' (DATA LOSS)." -ForegroundColor Yellow
    Write-Host "Type EXACTLY: RESET-$WslDistro to confirm" -ForegroundColor Yellow
    $confirm = Read-Host
    if ($confirm -ne "RESET-$WslDistro") { throw "Reset cancelled." }
    & wsl.exe --unregister $WslDistro
  }

  if ($InstallWSL) {
    # Ensure WSL feature + distro
    Write-Host "Installing WSL + distro '$WslDistro' (may require reboot / first-run user setup)..."
    & wsl.exe --install -d $WslDistro
    Write-Host "If this is first install: reboot if asked, launch '$WslDistro' once to create Linux user, then re-run script." -ForegroundColor Yellow
    return
  }

  # Verify distro exists
  $distros = & wsl.exe -l -q
  if ($distros -notcontains $WslDistro) {
    throw "WSL distro '$WslDistro' not found. Re-run with -InstallWSL."
  }

  # Basic Linux deps + nvm + Node LTS + npm tools
  Write-Host "Installing linux deps, nvm, node LTS, and CLIs (claude/codex/gemini) inside WSL..."
  Run-WSL @"
set -e
sudo apt-get update -y
sudo apt-get install -y curl git build-essential ca-certificates
# nvm
export NVM_DIR="\$HOME/.nvm"
if [ ! -d "\$NVM_DIR" ]; then
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
. "\$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
npm -v

# Claude Code (native installer recommended on WSL)
if ! command -v claude >/dev/null 2>&1; then
  (curl -fsSL https://claude.ai/install.sh | bash) || npm install -g @anthropic-ai/claude-code
fi

# Codex CLI
if ! command -v codex >/dev/null 2>&1; then
  npm install -g @openai/codex
fi

# Gemini CLI
if ! command -v gemini >/dev/null 2>&1; then
  npm install -g @google/gemini-cli
fi

echo "WSL tools installed OK."
"@
}

function Generate-Project-Scaffold() {
  Write-Section "Generating project scaffold"
  Assert-ProjectPath

  $claudeDir = Join-Path $ProjectPath ".claude"
  $cmdDir    = Join-Path $claudeDir "commands"
  $docsDir   = Join-Path $ProjectPath "docs"
  $toolsDir  = Join-Path $ProjectPath "tools"

  Ensure-Dir $cmdDir
  Ensure-Dir $docsDir
  Ensure-Dir $toolsDir

  # Minimal permissions: deny secrets; allow common harmless bash commands (tune later)
  $settingsJson = @'
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(**/.env)",
      "Read(**/.env.*)",
      "Read(**/*.pem)",
      "Read(**/*.key)",
      "Read(**/id_rsa*)",
      "Read(**/credentials*)",
      "Edit(**/.git/**)"
    ],
    "allow": [
      "Read(*)",
      "Bash(git status)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git show*)",
      "Bash(git branch*)",
      "Bash(git checkout*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git restore*)",
      "Bash(git reset*)",
      "Bash(node -v)",
      "Bash(npm -v)",
      "Bash(npm test*)",
      "Bash(npm run*)",
      "Bash(pnpm -v)",
      "Bash(pnpm run*)",
      "Bash(python --version)",
      "Bash(py --version)",
      "Bash(pip --version)",
      "Bash(codex*)",
      "Bash(gemini*)"
    ]
  },
  "env": {}
}
'@
  Write-File (Join-Path $claudeDir "settings.json") $settingsJson

  # CLAUDE.md (project memory / guardrails)
  $claudeMd = @"
# Project Operating Rules (Claude)

## Product boundary
- Purpose: Build Windows desktop automation tools and scripts.
- Do NOT: spam, stealth abuse, bypass platform security, or create malware.

## Repo rules
- Prefer smallest MVP first; keep changes reversible.
- Before writing code: produce a short plan + acceptance criteria.
- Always add a quick smoke test command (even if minimal).

## Secrets
- Do not read .env / credentials / private keys. If asked, stop and request redaction.

## Working loop (token-efficient)
1) Summarize the task in 6–10 lines.
2) List constraints + unknowns.
3) Propose a 3-step plan.
4) Execute in small diffs; run tests after each stage.
"@
  Write-File (Join-Path $ProjectPath "CLAUDE.md") $claudeMd

  # AGENTS.md (Codex uses /init to generate; we provide a ready baseline)
  $agentsMd = @"
# AGENTS.md (Codex)

## Mission
Implement changes as small, reviewable diffs. Prefer running local commands to verify.

## Process
- First: restate goal + assumptions
- Then: propose plan (MVP -> hardening)
- Implement: smallest diff that passes smoke test
- Finish: run /review (or equivalent) and summarize

## Guardrails
- No secrets exfiltration, no destructive commands without explicit confirmation.
"@
  Write-File (Join-Path $ProjectPath "AGENTS.md") $agentsMd

  # Router tool: one terminal entrypoint
  $aiwPs1 = @'
[CmdletBinding()]
param(
  [ValidateSet("claude","codex","gemini","doctor","where")]
  [string]$Tool = "where",

  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

function Has($n){ return [bool](Get-Command $n -ErrorAction SilentlyContinue) }

switch ($Tool) {
  "where" {
    "claude: " + (Get-Command claude  -ErrorAction SilentlyContinue | Select-Object -Expand Source -ErrorAction SilentlyContinue)
    "codex : " + (Get-Command codex   -ErrorAction SilentlyContinue | Select-Object -Expand Source -ErrorAction SilentlyContinue)
    "gemini: " + (Get-Command gemini  -ErrorAction SilentlyContinue | Select-Object -Expand Source -ErrorAction SilentlyContinue)
    break
  }
  "doctor" {
    if (Has "claude") { & claude doctor }
    else { throw "claude not found" }
    break
  }
  "claude" {
    if (Has "claude") { & claude @Args }
    else { throw "claude not found" }
    break
  }
  "codex" {
    if (Has "codex") { & codex @Args }
    else { throw "codex not found" }
    break
  }
  "gemini" {
    if (-not (Has "gemini")) { throw "gemini not found" }
    if ($Args.Count -eq 0) {
      & gemini
    } else {
      # Non-interactive prompt mode example: gemini -p "..."
      & gemini @Args
    }
    break
  }
}
'@
  Write-File (Join-Path $toolsDir "aiw.ps1") $aiwPs1

  # Custom slash commands (Claude Code)
  Write-File (Join-Path $cmdDir "intake.md") @'
# /intake
Turn the idea into an MVP spec.

Input: $ARGUMENTS

Output:
- docs/01_problem.md (problem, users, constraints)
- docs/02_mvp.md (MVP scope, non-goals, acceptance criteria)
- docs/03_plan.md (3 phases, each with test/checklist)
Keep it short and testable.
'@

  Write-File (Join-Path $cmdDir "delegate-gemini.md") @'
# /delegate-gemini
Prepare a Gemini CLI prompt for fast research (then I will run it).

Task: $ARGUMENTS

Output:
1) A single concise "gemini -p" command (or steps for interactive mode)
2) What to paste back into this Claude session
Do not include secrets.
'@

  Write-File (Join-Path $cmdDir "delegate-codex.md") @'
# /delegate-codex
Prepare a Codex task brief for implementation (then I will run codex).

Task: $ARGUMENTS

Output:
- Goal (1–2 lines)
- File targets / commands to run
- Acceptance checks
- A short "hand-off" block I can paste into Codex
'@

  Write-File (Join-Path $cmdDir "ship-check.md") @'
# /ship-check
Run a pre-ship checklist for this repo.

Goal: $ARGUMENTS

Output:
- What commands to run locally (build/test/lint)
- What files to review
- Risk hotspots
- A minimal release note (5 lines)
'@

  # Docs: workflow + recommended minimal plugin/MCP steps
  Write-File (Join-Path $docsDir "WORKFLOW.md") @"
# Windows AI Dev Workflow (Claude + Codex + Gemini)

## Division of labor (token-saving)
- Gemini: fast research + examples, short outputs.
- Claude: architecture + plan + guardrails + review.
- Codex: heavy implementation + refactors + local runs.

## Suggested loop
1) Claude: /intake <idea>
2) Gemini: /delegate-gemini <what to look up> -> run: tools\aiw.ps1 gemini -p "..."
3) Claude: integrate findings -> update docs/03_plan.md
4) Codex: /delegate-codex <implementation> -> run codex in repo
5) Claude: /ship-check <release> -> final review
"@

  Write-File (Join-Path $docsDir "PLUGINS_MINIMAL.md") @"
# Claude Code Plugins (minimal, non-overconfigured)

Use /plugin to manage plugins and marketplaces.
Recommended approach: start with ONLY what removes repetitive work (docs, commits, review).

Suggested first step:
- Add ONE marketplace
- Install ONE plugin
- Run for 1 week, then prune

(See Claude Code docs: Plugins + Plugin marketplaces.)
"@

  if ($WithMcpFilesystem) {
    # Minimal .mcp.json template (project-local)
    # NOTE: MCP ecosystem varies; this is a template only.
    Write-File (Join-Path $ProjectPath ".mcp.json") @'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "."
      ]
    }
  }
}
'@
  }

  Write-Host "Scaffold created in: $ProjectPath"
}

# ------------------- MAIN -------------------
Write-Section "Setup starting"
Assert-ProjectPath

if (-not $SkipInstalls) {
  if ($Mode -eq "Native") {
    Install-Native-Tools
  } else {
    Install-WSL-And-Tools
  }
} else {
  Write-Host "SkipInstalls set: no tool installs will be performed."
}

Generate-Project-Scaffold

Write-Section "Next steps (manual logins)"
Write-Host "1) Claude Code:   cd `"$ProjectPath`" ; claude ; then try: /intake <your idea>"
Write-Host "2) Codex CLI:     cd `"$ProjectPath`" ; codex   (first run prompts ChatGPT sign-in or API key)"
Write-Host "3) Gemini CLI:    gemini  (choose 'Login with Google')"
Write-Host "4) Health check:  .\tools\aiw.ps1 doctor"
Write-Host "Done."
