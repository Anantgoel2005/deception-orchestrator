$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$assetDirectory = Join-Path $repositoryRoot "docs\assets"
$frameDirectory = Join-Path $assetDirectory "demo"
$outputPath = Join-Path $assetDirectory "demo-walkthrough.gif"

$frames = @(
    (Join-Path $frameDirectory "01-dashboard.png"),
    (Join-Path $frameDirectory "02-demo-lab.png"),
    (Join-Path $assetDirectory "investigation.png"),
    (Join-Path $frameDirectory "03-alerts.png"),
    (Join-Path $frameDirectory "04-settings.png")
)

foreach ($frame in $frames) {
    if (-not (Test-Path -LiteralPath $frame)) {
        throw "Missing demo frame: $frame"
    }
}

ffmpeg -hide_banner -loglevel error -y `
    -loop 1 -t 2.4 -i $frames[0] `
    -loop 1 -t 2.4 -i $frames[1] `
    -loop 1 -t 2.4 -i $frames[2] `
    -loop 1 -t 2.4 -i $frames[3] `
    -loop 1 -t 2.4 -i $frames[4] `
    -filter_complex "[0:v]scale=960:540,format=rgba[v0];[1:v]scale=960:540,format=rgba[v1];[2:v]scale=960:540,format=rgba[v2];[3:v]scale=960:540,format=rgba[v3];[4:v]scale=960:540,format=rgba[v4];[v0][v1]xfade=transition=fade:duration=0.5:offset=1.9[x1];[x1][v2]xfade=transition=fade:duration=0.5:offset=3.8[x2];[x2][v3]xfade=transition=fade:duration=0.5:offset=5.7[x3];[x3][v4]xfade=transition=fade:duration=0.5:offset=7.6[x4];[x4]fps=8,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer[out]" `
    -map "[out]" $outputPath

if ($LASTEXITCODE -ne 0) {
    throw "ffmpeg failed to build the demo walkthrough."
}

Write-Host "Created $outputPath"
