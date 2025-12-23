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
