param(
    [string]$InputPath = (Join-Path $PSScriptRoot '..\evidence\jira-three-arm-figure.json'),
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\JIRA-THREE-ARM.png')
)

$ErrorActionPreference = 'Stop'
$data = Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
$arms = @('B0', 'B1', 'B2')
$fields = @('coalition_reward', 'noncoalition_reward', 'joint_reward')
function Assert-Number($value, [string]$name) {
    if ($null -eq $value -or $value -isnot [ValueType] -or $value -is [bool] -or
        [double]::IsNaN([double]$value) -or [double]::IsInfinity([double]$value)) {
        throw "Missing or nonnumeric $name."
    }
}
if ($data.rows.Count -ne 3 -or ($data.rows.arm -join ',') -ne ($arms -join ',')) {
    throw 'Expected exactly one ordered B0/B1/B2 result; no filtering or missing-as-zero.'
}
if ($data.denominators.scheduled_arms -ne 3 -or $data.denominators.complete_arms -ne 3 -or
    $data.denominators.missing_arms -ne 0 -or $data.denominators.failed_arms -ne 0 -or
    $data.denominators.scheduled_execution_actions -ne 12 -or
    $data.denominators.valid_action_commits -ne 12 -or
    $data.design.coalition_size -ne 2 -or $data.design.outsider_size -ne 2) {
    throw 'Outcome denominators or group sizes do not match this completed pilot.'
}
$references = $data.joint_optimal_reference
foreach ($key in $fields) { Assert-Number $references.$key "joint-optimal $key" }
if ($references.joint_reward -ne ($references.coalition_reward + $references.noncoalition_reward)) {
    throw 'Joint-optimal reward accounting mismatch.'
}
foreach ($row in $data.rows) {
    foreach ($key in ($fields + @('valid_action_commits', 'tool_errors', 'fallback_assignments',
            'violations', 'exact_system_regret', 'coalition_advantage_mean'))) {
        Assert-Number $row.$key "$key in $($row.arm)"
    }
    if ($row.status -ne 'complete' -or $row.valid_action_commits -ne 4 -or
        $row.tool_errors -ne 0 -or $row.fallback_assignments -ne 0 -or $row.violations -ne 0) {
        throw 'This renderer supports only the completed pilot; do not omit failed or incomplete arms.'
    }
    if ([math]::Abs($row.joint_reward - $row.coalition_reward - $row.noncoalition_reward) -gt 1e-9 -or
        $row.exact_system_regret -ne ($references.joint_reward - $row.joint_reward) -or
        $row.coalition_advantage_mean -ne (($row.coalition_reward - $row.noncoalition_reward) / 2)) {
        throw "Reward, regret or advantage accounting mismatch in $($row.arm)."
    }
    foreach ($key in $fields) {
        if ($row.$key -ne $data.rows[0].$key) {
            throw 'The identical-outcome caption does not apply to unequal rewards.'
        }
        if ($row.$key -lt 0 -or $row.$key -gt 140 -or $references.$key -lt 0 -or $references.$key -gt 140) {
            throw 'Reward/reference outside the plotted axis.'
        }
    }
}

Add-Type -AssemblyName System.Drawing
$resources = [System.Collections.Generic.List[System.IDisposable]]::new()
function Keep($item) { $resources.Add($item); return $item }
function Brush([string]$hex) {
    Keep ([System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($hex)))
}

try {
    $bitmap = Keep ([System.Drawing.Bitmap]::new(1600, 1040))
    $g = Keep ([System.Drawing.Graphics]::FromImage($bitmap))
    $g.Clear([System.Drawing.Color]::White)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $title = Keep ([System.Drawing.Font]::new('Segoe UI', 34, [System.Drawing.FontStyle]::Bold,
            [System.Drawing.GraphicsUnit]::Pixel))
    $body = Keep ([System.Drawing.Font]::new('Segoe UI', 21, [System.Drawing.FontStyle]::Regular,
            [System.Drawing.GraphicsUnit]::Pixel))
    $small = Keep ([System.Drawing.Font]::new('Segoe UI', 19, [System.Drawing.FontStyle]::Regular,
            [System.Drawing.GraphicsUnit]::Pixel))
    $ink = Brush '#0b0b0b'
    $muted = Brush '#52514e'
    $grid = Keep ([System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml('#e4e3df'), 1))
    $reference = Keep ([System.Drawing.Pen]::new([System.Drawing.Color]::Black, 2))
    $reference.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
    $colors = @((Brush '#2a78d6'), (Brush '#eda100'), (Brush '#1baf7a'))
    $labels = @('Coalition reward', 'Outsider reward', 'Joint reward')
    function Text([string]$text, [float]$x, [float]$y, $font, $brush, [switch]$Center) {
        if ($Center) { $x -= $g.MeasureString($text, $font).Width / 2 }
        $g.DrawString($text, $font, $brush, $x, $y)
    }

    Text 'Identical rewards across three Jira arms' 80 40 $title $ink
    Text "$($data.model) | Four agents, four tasks | Environment seed $($data.environment_seed)" 80 100 $body $muted
    for ($i = 0; $i -lt 3; $i++) {
        $x = 80 + $i * 340
        $g.FillRectangle($colors[$i], [float]$x, 162, 24, 24)
        Text $labels[$i] ($x + 36) 158 $body $ink
    }
    Text 'Dashed ticks: rewards at joint-optimal assignments, not each group''s own maximum.' 80 208 $small $muted
    $left, $right, $top, $bottom = 130, 1510, 280, 800
    $scale = ($bottom - $top) / 140
    Text 'Reward' 65 245 $small $muted
    for ($tick = 0; $tick -le 140; $tick += 20) {
        $y = $bottom - $tick * $scale
        $g.DrawLine($grid, [float]$left, [float]$y, [float]$right, [float]$y)
        Text "$tick" 80 ($y - 13) $small $muted
    }
    for ($armIndex = 0; $armIndex -lt 3; $armIndex++) {
        $row = $data.rows[$armIndex]
        $center = 365 + $armIndex * 455
        for ($series = 0; $series -lt 3; $series++) {
            $key = $fields[$series]
            $value = [double]$row.$key
            $x = $center + ($series - 1) * 110 - 42
            $y = $bottom - $value * $scale
            $g.FillRectangle($colors[$series], [float]$x, [float]$y, 84, [float]($bottom - $y))
            Text "$value" ($x + 42) ($y - 32) $body $ink -Center
            $referenceY = $bottom - [double]$references.$key * $scale
            $g.DrawLine($reference, [float]($x - 7), [float]$referenceY,
                [float]($x + 91), [float]$referenceY)
        }
        Text $row.arm $center 820 $body $ink -Center
        Text $row.label $center 852 $small $muted -Center
    }
    Text "Joint-optimal reference: coalition $($references.coalition_reward) | outsiders $($references.noncoalition_reward) | joint $($references.joint_reward). Observed regret: $($data.rows[0].exact_system_regret) in every arm." 80 900 $small $ink
    Text 'One fixed instance; uncontrolled sampling. SDK extension, not replication or a general no-effect result.' 80 939 $small $muted
    Text 'No established harmful collusion chain. These runs are not validated collusion negatives.' 80 978 $small $ink
    $bitmap.Save([System.IO.Path]::GetFullPath($OutputPath), [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    for ($i = $resources.Count - 1; $i -ge 0; $i--) { $resources[$i].Dispose() }
}
