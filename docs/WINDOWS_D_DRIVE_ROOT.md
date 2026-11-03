# Portable D: requirement

Use **D:\GrokTradingCouncil** for this fresh project's checkout, environment, project
temp/cache, database, logs, evidence and backups. `scripts/launch.ps1` compares the
actual D: volume UniqueId with the owner's verified expected ID, checks root/junctions
and writeability, then starts only the demo or an explicit public read-only scan.
It never formats, migrates or substitutes C:. Existing unrelated data is untouched.

Inspect `Get-Volume -DriveLetter D | Format-List DriveLetter,FileSystemLabel,UniqueId,HealthStatus`
on the owner's PC before supplying the expected ID. Do not guess it. Do not weaken
PowerShell policy automatically if execution is blocked; use the owner's normal
reviewed local script process. The Windows script has been source-reviewed here,
not executed. Physical volume identity and durability are still UNVERIFIED.

The Python interpreter and OS may have their own installation/system storage. The
project-owned files remain under D:. Grok's cloud computer and Codex cloud scratch
are separate. Neither is a synchronized copy of the physical portable drive.
