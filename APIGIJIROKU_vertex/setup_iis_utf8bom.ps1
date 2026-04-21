# IIS 迺ｰ蠅・｢ｺ隱阪・繧ｻ繝・ヨ繧｢繝・・謾ｯ謠ｴ繧ｹ繧ｯ繝ｪ繝励ヨ

Write-Host "--- IIS for Streamlit Setup Check ---" -ForegroundColor Cyan

# 1. IIS 讖溯・縺ｮ遒ｺ隱・(WebSocket縺ｪ縺ｩ)
Write-Host "[1/2] Windows Server 讖溯・繧堤｢ｺ隱堺ｸｭ..."
$features = Get-WindowsFeature -Name Web-Server, Web-WebSockets, Web-CGI
foreach ($f in $features) {
    if ($f.Installed) {
        Write-Host "  [OK] $($f.DisplayName) 縺ｯ繧､繝ｳ繧ｹ繝医・繝ｫ貂医∩縺ｧ縺吶・ -ForegroundColor Green
    } else {
        Write-Host "  [!!] $($f.DisplayName) 縺梧悴繧､繝ｳ繧ｹ繝医・繝ｫ縺ｧ縺吶ゅし繝ｼ繝舌・繝槭ロ繝ｼ繧ｸ繝｣繝ｼ縺九ｉ霑ｽ蜉縺励※縺上□縺輔＞縲・ -ForegroundColor Yellow
    }
}

# 2. HttpPlatformHandler 縺ｮ遒ｺ隱・
Write-Host "[2/2] HttpPlatformHandler 繝｢繧ｸ繝･繝ｼ繝ｫ繧堤｢ｺ隱堺ｸｭ..."
$modulePath = "$env:SystemRoot\System32\inetsrv\httpPlatformHandler.dll"
if (Test-Path $modulePath) {
    Write-Host "  [OK] HttpPlatformHandler 縺ｯ繧､繝ｳ繧ｹ繝医・繝ｫ貂医∩縺ｧ縺吶・ -ForegroundColor Green
} else {
    Write-Host "  [!!] HttpPlatformHandler 縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縲・ -ForegroundColor Red
    Write-Host "  莉･荳九・URL繧医ｊ繝繧ｦ繝ｳ繝ｭ繝ｼ繝峨＠縺ｦ繧､繝ｳ繧ｹ繝医・繝ｫ縺励※縺上□縺輔＞ (IIS 蜷代￠)"
    Write-Host "  https://www.iis.net/downloads/microsoft/httpplatformhandler"
}

Write-Host "`n--- 險ｭ螳壹・繝偵Φ繝・---"
Write-Host "1. IIS 繝槭ロ繝ｼ繧ｸ繝｣繝ｼ縺ｧ [譁ｰ縺励＞Web繧ｵ繧､繝・ 繧剃ｽ懈・縺励※縺上□縺輔＞縲・
Write-Host "2. 迚ｩ逅・ヱ繧ｹ縺ｫ縺薙・繝・ぅ繝ｬ繧ｯ繝医Μ ($PWD) 繧呈欠螳壹＠縺ｦ縺上□縺輔＞縲・
Write-Host "3. 繧ｵ繧､繝医・ [繝舌う繝ｳ繝云 縺ｧ繝昴・繝育分蜿ｷ (萓・ 80) 繧定ｨｭ螳壹＠縺ｦ縺上□縺輔＞縲・
Write-Host "4. 繧ｵ繧､繝医ｒ驕ｸ謚槭＠縲ー繝上Φ繝峨Λ繝ｼ 繝槭ャ繝斐Φ繧ｰ] 縺ｫ 'httpPlatformHandler' 縺後≠繧九％縺ｨ繧堤｢ｺ隱阪＠縺ｦ縺上□縺輔＞縲・
Write-Host "---"
