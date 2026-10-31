# Weekly on madis-pc (scheduled task "GridFit watch (Edge)", docs/freshness.md): the watch's JavaScript pages,
# then the datasheet harvester's Edge recipes (tools/specs/harvest.py --edge: SMA, Kostal, SolaX download pages).
# Runs in a clone of its own, reset to origin/main every time, so nothing in it survives a run (cache/ is
# git-ignored and stays, so a sheet is fetched once). Commits only the Edge files (data/watch/*-edge.json, the
# Edge sources' seen/ lists, data/specs/harvest-edge.json and the Edge brands' drafts) and pushes; the Monday
# Actions run folds them into docs/watch-report.md and docs/harvest-report.md. One block per run in the log
# next to the clone.
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$log = "$repo.log"
$python = "C:\Users\madis\AppData\Local\Programs\Python\Python313\python.exe"
function Say($m) { Add-Content -Path $log -Value $m -Encoding utf8 }
Say "=== $(Get-Date -Format s) gridfit watch --edge ==="
$code = 0
try {
    git -C $repo fetch --quiet origin 2>&1 | ForEach-Object { Say "$_" }
    git -C $repo checkout --quiet -B main origin/main 2>&1 | ForEach-Object { Say "$_" }
    git -C $repo reset --quiet --hard origin/main 2>&1 | ForEach-Object { Say "$_" }
    Push-Location $repo
    & $python tools\watch\run.py --edge 2>&1 | ForEach-Object { Say "$_" }
    if ($LASTEXITCODE -ne 0) { throw "run.py exit $LASTEXITCODE" }
    # the harvester's Edge recipes; a failing route is in its manifest, a crash must not lose the watch's commit
    try { & $python tools\specs\harvest.py --edge 2>&1 | ForEach-Object { Say "$_" } } catch { Say "harvest --edge FAILED: $_" }
    $drafts = (Get-Content tools\specs\harvest.yaml | Select-String -Pattern "^  - id: ([a-z0-9-]+)" -Context 0,3 | ForEach-Object {
        if ($_.Context.PostContext -match "mode: edge") { "data/specs/_drafts/$($_.Matches[0].Groups[1].Value).yaml" } } | Where-Object { Test-Path $_ })
    $edge = (Get-Content tools\watch\sources.yaml | Select-String -Pattern "kind: edge" | ForEach-Object {
        if ($_ -match "id: ([a-z0-9-]+)") { "data/watch/seen/$($Matches[1]).txt" } })
    git add data/watch/state-edge.json data/watch/codes-edge.json data/watch/candidates-edge.json @edge 2>&1 | ForEach-Object { Say "$_" }
    if (Test-Path data\specs\harvest-edge.json) { git add data/specs/harvest-edge.json @drafts 2>&1 | ForEach-Object { Say "$_" } }
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git -c user.name="gridfit-bot" -c user.email="gridfit-bot@users.noreply.github.com" commit --quiet -m "watch + harvest: Edge pages $(Get-Date -Format yyyy-MM-dd)" 2>&1 | ForEach-Object { Say "$_" }
        git push --quiet origin main 2>&1 | ForEach-Object { Say "$_" }
        if ($LASTEXITCODE -ne 0) { throw "push failed" }
    } else { Say "nothing changed" }
} catch {
    Say "FAILED: $_"
    $code = 1
} finally {
    Pop-Location -ErrorAction SilentlyContinue
    Say "=== exit $code ==="
}
exit $code
