Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"

$script:OutputPath = Join-Path $PSScriptRoot "work_records.yaml"
$script:DefaultPath = Join-Path $PSScriptRoot "work_record_defaults.json"

$defaults = [ordered]@{
  target_date         = "2026-04-21"
  work_segment        = "OFFICE"
  start_time          = "09:00"
  end_time            = "17:30"
  break1_start        = "12:00"
  break1_end          = "13:00"
  break2_start        = ""
  break2_end          = ""
  expense             = "0"
  original_start      = ""
  original_end        = ""
  notes               = ""
  sar_department_code = ""
  sar_project_code    = ""
  sar_process         = ""
  sar_notes           = ""
}

$timeFields = @(
  "start_time",
  "end_time",
  "break1_start",
  "break1_end",
  "break2_start",
  "break2_end",
  "original_start",
  "original_end"
)

$optionalTimeFields = @(
  "break1_start",
  "break1_end",
  "break2_start",
  "break2_end",
  "original_start",
  "original_end"
)

. "$PSScriptRoot\workSegments.ps1"

function Format-WorkSegmentItem {
  param([hashtable]$Segment)
  return "$($Segment.Key) - $($Segment.Label)"
}

function Get-WorkSegmentValue {
  param([string]$SelectedItem)
  return ($SelectedItem -split " - ", 2)[0]
}

function Load-DefaultValues {
  $values = [ordered]@{}
  foreach ($key in $defaults.Keys) {
    $values[$key] = $defaults[$key]
  }
  $values["target_date"] = [datetime]::Today.ToString("yyyy-MM-dd")

  if (-not (Test-Path $script:DefaultPath)) {
    return $values
  }

  $json = Get-Content -Path $script:DefaultPath -Raw -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($json)) {
    return $values
  }

  $saved = $json | ConvertFrom-Json
  foreach ($key in $defaults.Keys) {
    if ($saved.PSObject.Properties.Name -contains $key) {
      $values[$key] = [string]$saved.$key
    }
  }
  $values["target_date"] = [datetime]::Today.ToString("yyyy-MM-dd")

  return $values
}

function Save-DefaultValues {
  param([hashtable]$Values)

  $ordered = [ordered]@{}
  foreach ($key in $defaults.Keys) {
    $ordered[$key] = [string]$Values[$key]
  }

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  $json = $ordered | ConvertTo-Json -Depth 3
  [System.IO.File]::WriteAllText($script:DefaultPath, "$json$([Environment]::NewLine)", $utf8NoBom)
}

function Parse-DateValue {
  param([string]$Value)

  $parsed = [datetime]::MinValue
  if ([datetime]::TryParseExact(
      $Value,
      "yyyy-MM-dd",
      [Globalization.CultureInfo]::InvariantCulture,
      [Globalization.DateTimeStyles]::None,
      [ref]$parsed
    )) {
    return $parsed
  }

  return [datetime]::Today
}

function Parse-TimeValue {
  param([string]$Value)

  $parsed = [datetime]::MinValue
  if ([datetime]::TryParseExact(
      $Value,
      "HH:mm",
      [Globalization.CultureInfo]::InvariantCulture,
      [Globalization.DateTimeStyles]::None,
      [ref]$parsed
    )) {
    return [datetime]::Today.AddHours($parsed.Hour).AddMinutes($parsed.Minute)
  }

  return [datetime]::Today
}

function Set-FieldValue {
  param(
    [string]$Key,
    [object]$Control,
    [string]$Value
  )

  if ($Key -eq "target_date") {
    $Control.Value = Parse-DateValue $Value
    return
  }

  if ($Key -eq "work_segment") {
    $segment = $workSegments | Where-Object { $_.Key -eq $Value } | Select-Object -First 1
    if ($null -eq $segment) {
      $Control.SelectedIndex = 0
    }
    else {
      $Control.SelectedItem = Format-WorkSegmentItem $segment
    }
    return
  }

  if ($timeFields -contains $Key) {
    if ($optionalTimeFields -contains $Key) {
      $Control.Checked = -not [string]::IsNullOrWhiteSpace($Value)
    }
    $Control.Value = Parse-TimeValue $Value
    return
  }

  $Control.Text = $Value
}

function Get-FieldValue {
  param(
    [string]$Key,
    [object]$Control
  )

  if ($Key -eq "target_date") {
    return $Control.Value.ToString("yyyy-MM-dd")
  }

  if ($Key -eq "work_segment") {
    return Get-WorkSegmentValue $Control.SelectedItem
  }

  if ($timeFields -contains $Key) {
    if (($optionalTimeFields -contains $Key) -and (-not $Control.Checked)) {
      return ""
    }

    return $Control.Value.ToString("HH:mm")
  }

  return $Control.Text
}

function Get-CurrentValues {
  $values = @{}
  foreach ($key in $defaults.Keys) {
    $values[$key] = Get-FieldValue $key $fields[$key]
  }

  return $values
}

function Set-FormValues {
  param([object]$Values)

  foreach ($key in $defaults.Keys) {
    Set-FieldValue $key $fields[$key] ([string]$Values[$key])
  }
}

function ConvertTo-YamlDoubleQuoted {
  param([string]$Value)

  if ($null -eq $Value) {
    return '""'
  }

  $escaped = $Value.Replace('\', '\\').Replace('"', '\"')
  return '"' + $escaped + '"'
}

function New-WorkRecordYaml {
  param([hashtable]$Values)

  $lines = @(
    "  - target_date: $($Values.target_date)",
    "    work_segment: $($Values.work_segment)",
    "    start_time: $(ConvertTo-YamlDoubleQuoted $Values.start_time)",
    "    end_time: $(ConvertTo-YamlDoubleQuoted $Values.end_time)",
    "    break1_start: $(ConvertTo-YamlDoubleQuoted $Values.break1_start)",
    "    break1_end: $(ConvertTo-YamlDoubleQuoted $Values.break1_end)",
    "    break2_start: $(ConvertTo-YamlDoubleQuoted $Values.break2_start)",
    "    break2_end: $(ConvertTo-YamlDoubleQuoted $Values.break2_end)",
    "    expense: $(ConvertTo-YamlDoubleQuoted $Values.expense)",
    "    original_start: $(ConvertTo-YamlDoubleQuoted $Values.original_start)",
    "    original_end: $(ConvertTo-YamlDoubleQuoted $Values.original_end)",
    "    notes: $(ConvertTo-YamlDoubleQuoted $Values.notes)",
    "    sar_department_code: $(ConvertTo-YamlDoubleQuoted $Values.sar_department_code)",
    "    sar_project_code: $(ConvertTo-YamlDoubleQuoted $Values.sar_project_code)",
    "    sar_process: $(ConvertTo-YamlDoubleQuoted $Values.sar_process)",
    "    sar_notes: $(ConvertTo-YamlDoubleQuoted $Values.sar_notes)"
  )

  return ($lines -join [Environment]::NewLine)
}

function Add-WorkRecord {
  param([hashtable]$Values)

  $date = [datetime]::MinValue
  if (-not [datetime]::TryParseExact(
      $Values.target_date,
      "yyyy-MM-dd",
      [Globalization.CultureInfo]::InvariantCulture,
      [Globalization.DateTimeStyles]::None,
      [ref]$date
    )) {
    throw "target_date は YYYY-MM-DD 形式で入力してください。"
  }

  if ([string]::IsNullOrWhiteSpace($Values.work_segment)) {
    throw "work_segment は必須です。"
  }

  $recordYaml = New-WorkRecordYaml $Values
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  $newContent = "records:$([Environment]::NewLine)$recordYaml$([Environment]::NewLine)"
  [System.IO.File]::WriteAllText($script:OutputPath, $newContent, $utf8NoBom)
}

function Invoke-KintaiRegistration {
    . "$PSScriptRoot\env.ps1"

    $pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonPath)) {
        $pythonPath = "python"
    }

    Push-Location $PSScriptRoot
    try {
        & $pythonPath src/main.py --input work_records.yaml
        if ($LASTEXITCODE -ne 0) {
            throw "勤怠登録コマンドが失敗しました。終了コード: $LASTEXITCODE"
        }
  }
  finally {
    Pop-Location
  }
}

[System.Windows.Forms.Application]::EnableVisualStyles()

$script:ActiveDefaults = Load-DefaultValues

$form = New-Object System.Windows.Forms.Form
$form.Text = "work_records.yaml 1レコード作成"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(560, 750)
$form.MinimumSize = New-Object System.Drawing.Size(560, 750)

$panel = New-Object System.Windows.Forms.Panel
$panel.Dock = "Fill"
$panel.AutoScroll = $false
$form.Controls.Add($panel)

$fields = @{}
$y = 16

$todayLabel = New-Object System.Windows.Forms.Label
$todayLabel.Text = [datetime]::Today.ToString("yyyy-MM-dd (ddd)", [Globalization.CultureInfo]::GetCultureInfo("ja-JP"))
$todayLabel.Location = New-Object System.Drawing.Point(336, 16)
$todayLabel.Size = New-Object System.Drawing.Size(170, 24)
$todayLabel.TextAlign = "MiddleRight"
$panel.Controls.Add($todayLabel)

foreach ($key in $defaults.Keys) {
  $label = New-Object System.Windows.Forms.Label
  $label.Text = $key
  $label.Location = New-Object System.Drawing.Point(16, $y)
  $label.Size = New-Object System.Drawing.Size(150, 24)
  $label.TextAlign = "MiddleLeft"
  $panel.Controls.Add($label)

  if ($key -eq "work_segment") {
    $comboBox = New-Object System.Windows.Forms.ComboBox
    $comboBox.DropDownStyle = "DropDownList"
    $comboBox.Location = New-Object System.Drawing.Point(176, $y)
    $comboBox.Size = New-Object System.Drawing.Size(330, 24)

    foreach ($segment in $workSegments) {
      [void]$comboBox.Items.Add((Format-WorkSegmentItem $segment))
    }

    $panel.Controls.Add($comboBox)
    $fields[$key] = $comboBox
    Set-FieldValue $key $comboBox ([string]$script:ActiveDefaults[$key])
    $y += 34
    continue
  }

  if ($key -eq "target_date") {
    $datePicker = New-Object System.Windows.Forms.DateTimePicker
    $datePicker.Format = "Custom"
    $datePicker.CustomFormat = "yyyy-MM-dd"
    $datePicker.Location = New-Object System.Drawing.Point(176, $y)
    $datePicker.Size = New-Object System.Drawing.Size(330, 24)

    $panel.Controls.Add($datePicker)
    $fields[$key] = $datePicker
    Set-FieldValue $key $datePicker ([string]$script:ActiveDefaults[$key])
    $y += 34
    continue
  }

  if ($timeFields -contains $key) {
    $timePicker = New-Object System.Windows.Forms.DateTimePicker
    $timePicker.Format = "Custom"
    $timePicker.CustomFormat = "HH:mm"
    $timePicker.ShowUpDown = $true
    $timePicker.Location = New-Object System.Drawing.Point(176, $y)
    $timePicker.Size = New-Object System.Drawing.Size(330, 24)
    if ($optionalTimeFields -contains $key) {
      $timePicker.ShowCheckBox = $true
    }

    $panel.Controls.Add($timePicker)
    $fields[$key] = $timePicker
    Set-FieldValue $key $timePicker ([string]$script:ActiveDefaults[$key])
    $y += 34
    continue
  }

  $textBox = New-Object System.Windows.Forms.TextBox
  $textBox.Text = $script:ActiveDefaults[$key]
  $textBox.Location = New-Object System.Drawing.Point(176, $y)
  $textBox.Size = New-Object System.Drawing.Size(330, 24)
  if ($key -in @("notes", "sar_notes")) {
    $textBox.Multiline = $true
    $textBox.ScrollBars = "Vertical"
    $textBox.Size = New-Object System.Drawing.Size(330, 52)
    $panel.Controls.Add($textBox)
    $fields[$key] = $textBox
    $y += 64
    continue
  }

  $panel.Controls.Add($textBox)
  $fields[$key] = $textBox
  $y += 34
}

$resetButton = New-Object System.Windows.Forms.Button
$resetButton.Text = "リセット"
$resetButton.Location = New-Object System.Drawing.Point -ArgumentList 176, ($y + 8)
$resetButton.Size = New-Object System.Drawing.Size(80, 32)
$panel.Controls.Add($resetButton)

$updateDefaultButton = New-Object System.Windows.Forms.Button
$updateDefaultButton.Text = "デフォルト更新"
$updateDefaultButton.Location = New-Object System.Drawing.Point -ArgumentList 264, ($y + 8)
$updateDefaultButton.Size = New-Object System.Drawing.Size(120, 32)
$panel.Controls.Add($updateDefaultButton)

$saveButton = New-Object System.Windows.Forms.Button
$saveButton.Text = "保存"
$saveButton.Location = New-Object System.Drawing.Point -ArgumentList 392, ($y + 8)
$saveButton.Size = New-Object System.Drawing.Size(54, 32)
$panel.Controls.Add($saveButton)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = "閉じる"
$cancelButton.Location = New-Object System.Drawing.Point -ArgumentList 452, ($y + 8)
$cancelButton.Size = New-Object System.Drawing.Size(54, 32)
$panel.Controls.Add($cancelButton)

$cancelButton.Add_Click({
    $form.Close()
  })

$resetButton.Add_Click({
    Set-FormValues $script:ActiveDefaults
  })

$updateDefaultButton.Add_Click({
    try {
      $script:ActiveDefaults = Get-CurrentValues
      Save-DefaultValues $script:ActiveDefaults
      [System.Windows.Forms.MessageBox]::Show(
        "現在の入力値をデフォルト値として保存しました。`n$script:DefaultPath",
        "デフォルト更新",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
      ) | Out-Null
    }
    catch {
      [System.Windows.Forms.MessageBox]::Show(
        $_.Exception.Message,
        "デフォルト更新エラー",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
      ) | Out-Null
    }
  })

$saveButton.Add_Click({
    try {
      $saveButton.Enabled = $false
      $values = Get-CurrentValues

      Add-WorkRecord $values
      Invoke-KintaiRegistration
    }
    catch {
      [System.Windows.Forms.MessageBox]::Show(
        $_.Exception.Message,
        "保存エラー",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
      ) | Out-Null
    }
    finally {
      $saveButton.Enabled = $true
    }
  })

[void]$form.ShowDialog()
