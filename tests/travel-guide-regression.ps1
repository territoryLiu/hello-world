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

$playbookPath = Join-Path $Root "travel-planning-playbook.md"
$desktopPath = Join-Path $Root "trips/jilin-yanji-changbaishan/desktop/index.html"
$mobilePath = Join-Path $Root "trips/jilin-yanji-changbaishan/mobile/index.html"
$sourceNotePath = Join-Path $Root "trips/jilin-yanji-changbaishan/notes/sources.md"
$imagePlanPath = Join-Path $Root "trips/jilin-yanji-changbaishan/notes/image-plan.md"
$contentPath = Join-Path $Root "trips/jilin-yanji-changbaishan/assets/guide-content.js"

foreach ($pathInfo in @(
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

$playbookContent = Get-Content -Raw $playbookPath

foreach ($heading in @(
  "## 寮€濮嬪墠蹇呴』纭鐨勪俊鎭?",
  "## 璋冪爺鎵ц椤哄簭",
  "## 琛岀▼鏂规鐢熸垚瑙勫垯",
  "## HTML 鍐呭椤哄簭瑙勮寖",
  "## 鍥句綅鏂规瑙勮寖",
  "## 浜や粯妫€鏌ユ竻鍗?"
)) {
  Assert-Match -Content $playbookContent -Pattern [regex]::Escape($heading) -Label $heading
}

$desktopContent = Get-Content -Raw $desktopPath
$mobileContent = Get-Content -Raw $mobilePath
$sharedContent = Get-Content -Raw $contentPath

foreach ($contentInfo in @(
  @{ Name = "desktop"; Content = $desktopContent },
  @{ Name = "mobile"; Content = $mobileContent }
)) {
  foreach ($id in @("overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources")) {
    Assert-Match -Content $contentInfo.Content -Pattern "id=`"$id`"" -Label "$($contentInfo.Name) section #$id"
  }
}

Assert-Match -Content $mobileContent -Pattern 'data-page="' -Label "mobile pagination markers"
Assert-Match -Content $sharedContent -Pattern 'const tripGuide =' -Label "shared guide content export"

Write-Host "travel guide regression checks passed"
