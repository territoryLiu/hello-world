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

$tripPath = Join-Path $Root "吉林延吉长白山trip.html"
$tripContent = Get-Content -Raw $tripPath

foreach ($id in @("wear", "best", "plans", "tips", "sources")) {
  Assert-Match -Content $tripContent -Pattern "id=`"$id`"" -Label "anchor #$id"
}

Assert-Match -Content $tripContent -Pattern "--bg-warm:" -Label "warm background token"
Assert-Match -Content $tripContent -Pattern 'class="hero-summary' -Label "hero summary rail"
Assert-Match -Content $tripContent -Pattern 'class="section-intro"' -Label "section intro wrapper"
Assert-Match -Content $tripContent -Pattern 'class="dark-panel"' -Label "dark emphasis panel"
Write-Host "trip.html structure checks passed"

$storyPath = Join-Path $Root "吉林延吉长白山trip-专题版.html"

if (-not (Test-Path $storyPath)) {
  throw "Missing 吉林延吉长白山trip-专题版.html"
}

$storyContent = Get-Content -Raw $storyPath

foreach ($id in @("summary", "timeline", "packing", "booking", "guide", "tips", "sources")) {
  Assert-Match -Content $storyContent -Pattern "id=`"$id`"" -Label "story anchor #$id"
}

foreach ($marker in @("专题速览", "路线时间轴", "订票顺序", "完整展开攻略", "信息来源")) {
  Assert-Match -Content $storyContent -Pattern $marker -Label $marker
}

Assert-Match -Content $storyContent -Pattern 'class="hero-summary' -Label "story hero summary rail"
Assert-Match -Content $storyContent -Pattern 'class="dark-panel"' -Label "story dark emphasis panel"
Write-Host "story edition checks passed"

foreach ($item in @(
  @{ Name = "trip"; Content = $tripContent },
  @{ Name = "story"; Content = $storyContent }
)) {
  Assert-Match -Content $item.Content -Pattern "@media \(max-width:960px\)" -Label "$($item.Name) mobile breakpoint"
  Assert-Match -Content $item.Content -Pattern "grid-template-columns:1fr" -Label "$($item.Name) single-column fallback"
}
Write-Host "responsive checks passed"

foreach ($item in @(
  @{ Name = "trip"; Content = $tripContent },
  @{ Name = "story"; Content = $storyContent }
)) {
  Assert-Match -Content $item.Content -Pattern "截至 2026 年 4 月 10 日最近可查" -Label "$($item.Name) recent transport date"
  Assert-Match -Content $item.Content -Pattern "交通班次与价格参考" -Label "$($item.Name) transport heading"
  Assert-Match -Content $item.Content -Pattern "高铁 / 动车" -Label "$($item.Name) rail marker"
  Assert-Match -Content $item.Content -Pattern "飞机" -Label "$($item.Name) flight marker"
  Assert-Match -Content $item.Content -Pattern "公交 / 地铁 / 打车" -Label "$($item.Name) local transit marker"
}

$playbookPath = Join-Path $Root "travel-planning-playbook.md"
$playbookContent = Get-Content -Raw $playbookPath
Assert-Match -Content $playbookContent -Pattern "交通信息写法" -Label "playbook transport writing section"
Assert-Match -Content $playbookContent -Pattern "最近可查日期" -Label "playbook recent-query guidance"
Assert-Match -Content $playbookContent -Pattern "预估价格" -Label "playbook estimated-price guidance"
Write-Host "transport content checks passed"
