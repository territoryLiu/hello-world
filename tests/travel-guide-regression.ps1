param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Assert-Match {
  param(
    [string]$Content,
    [string]$Pattern,
    [string]$Label
  )

  if ($Content -notmatch $Pattern) {
    throw "Missing $Label ($Pattern)"
  }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ($Root -eq ".") {
  $Root = Split-Path -Parent $scriptRoot
} elseif (-not [System.IO.Path]::IsPathRooted($Root)) {
  $Root = Join-Path $scriptRoot $Root
}
$Root = [System.IO.Path]::GetFullPath($Root)

$playbookPath = Join-Path $Root "travel-planning-playbook.md"
$desktopPath = Join-Path $Root "trips/jilin-yanji-changbaishan/desktop/index.html"
$mobilePath = Join-Path $Root "trips/jilin-yanji-changbaishan/mobile/index.html"
$sourceNotePath = Join-Path $Root "trips/jilin-yanji-changbaishan/notes/sources.md"
$imagePlanPath = Join-Path $Root "trips/jilin-yanji-changbaishan/notes/image-plan.md"
$contentPath = Join-Path $Root "trips/jilin-yanji-changbaishan/assets/guide-content.js"

foreach ($pathInfo in @(
  @{ Path = $playbookPath; Label = "playbook" },
  @{ Path = $desktopPath; Label = "desktop index" },
  @{ Path = $mobilePath; Label = "mobile index" },
  @{ Path = $sourceNotePath; Label = "sources note" },
  @{ Path = $imagePlanPath; Label = "image plan note" },
  @{ Path = $contentPath; Label = "shared guide content" }
)) {
  if (-not (Test-Path $pathInfo.Path)) {
    throw "Missing $($pathInfo.Label): $($pathInfo.Path)"
  }
}

$playbookContent = Get-Content -Raw -Encoding UTF8 $playbookPath

$headings = @(
  "## 开始前必须确认的信息",
  "## 调研执行顺序",
  "## 行程方案生成规则",
  "## HTML 内容顺序规范",
  "## 图位方案规范",
  "## 交付检查清单"
)

foreach ($heading in $headings) {
  # Force method invocation in argument position (PowerShell 5.1 can otherwise pass the method group).
  Assert-Match -Content $playbookContent -Pattern ([regex]::Escape($heading)) -Label $heading
}

$desktopContent = Get-Content -Raw -Encoding UTF8 $desktopPath
$mobileContent = Get-Content -Raw -Encoding UTF8 $mobilePath
$sharedContent = Get-Content -Raw -Encoding UTF8 $contentPath

$contentMap = @{
  desktop = $desktopContent
  mobile = $mobileContent
}

$requiredSectionIds = @(
  "overview"
  "recommended"
  "options"
  "attractions"
  "food"
  "season"
  "packing"
  "transport"
  "sources"
)

foreach ($name in $contentMap.Keys) {
  $currentContent = $contentMap[$name]
  foreach ($id in $requiredSectionIds) {
    $pattern = [regex]::Escape("id=""$id""")
    $label = "$name section #$id"
    Assert-Match -Content $currentContent -Pattern $pattern -Label $label
  }
}

Assert-Match -Content $mobileContent -Pattern 'data-page="' -Label "mobile pagination markers"
Assert-Match -Content $sharedContent -Pattern 'const tripGuide =' -Label "shared guide content export"

Write-Host "travel guide regression checks passed"
