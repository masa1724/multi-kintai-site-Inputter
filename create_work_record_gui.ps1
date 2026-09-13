Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"

$script:OutputPath = Join-Path $PSScriptRoot "work_records.yaml"
$script:DefaultPath = Join-Path $PSScriptRoot "work_record_defaults.json"
$script:PresetPath = Join-Path $PSScriptRoot "work_record_presets.json"

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

function Copy-Values {
  param([object]$Values)
  $copy = @{}
  foreach ($key in $defaults.Keys) {
    $copy[$key] = [string]$Values[$key]
  }
  return $copy
}

function Load-Presets {
  if (-not (Test-Path $script:PresetPath)) { return @{} }
  $json = Get-Content -LiteralPath $script:PresetPath -Raw -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($json)) { return @{} }
  $saved = $json | ConvertFrom-Json
  $result = @{}
  foreach ($entry in $saved.PSObject.Properties) {
    $values = @{}
    foreach ($key in $defaults.Keys) {
      if ($key -ne "target_date") {
        $property = $entry.Value.PSObject.Properties[$key]
        $values[$key] = if ($null -eq $property) { "" } else { [string]$property.Value }
      }
    }
    $result[$entry.Name] = $values
  }
  return $result
}

function Save-Presets {
  $json = $script:Presets | ConvertTo-Json -Depth 5
  [System.IO.File]::WriteAllText(
    $script:PresetPath,
    "$json$([Environment]::NewLine)",
    (New-Object System.Text.UTF8Encoding($false))
  )
}

function Refresh-PresetList {
  $selected = [string]$presetCombo.SelectedItem
  $presetCombo.Items.Clear()
  foreach ($name in ($script:Presets.Keys | Sort-Object)) {
    [void]$presetCombo.Items.Add($name)
  }
  if ($presetCombo.Items.Contains($selected)) { $presetCombo.SelectedItem = $selected }
}

function Save-SelectedDay {
  if ($script:SelectedDay -ge 0) {
    $script:WeekValues[$script:SelectedDay] = Copy-Values (Get-CurrentValues)
  }
}

function Show-SelectedDay {
  param([int]$Index)
  Save-SelectedDay
  $script:SelectedDay = $Index
  Set-FormValues $script:WeekValues[$Index]
  $dayLabel.Text = "編集中: $($script:WeekValues[$Index].target_date)"
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

function Save-WorkRecords {
  param([object[]]$Records)

  if ($Records.Count -eq 0) { throw "登録する日を1日以上選択してください。" }
  $recordYaml = @($Records | ForEach-Object { New-WorkRecordYaml $_ }) -join [Environment]::NewLine
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
$script:Presets = Load-Presets
$script:SelectedDay = -1
$script:WeekValues = @()

$form = New-Object System.Windows.Forms.Form
$form.Text = "勤怠入力（1週間）"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(600, 850)
$form.MinimumSize = New-Object System.Drawing.Size(600, 650)

$panel = New-Object System.Windows.Forms.Panel
$panel.Dock = "Fill"
$panel.AutoScroll = $true
$form.Controls.Add($panel)

$fields = @{}
$y = 252

$weekLabel = New-Object System.Windows.Forms.Label
$weekLabel.Text = "週の開始日（月曜）"
$weekLabel.Location = New-Object System.Drawing.Point(16, 16)
$weekLabel.Size = New-Object System.Drawing.Size(150, 24)
$panel.Controls.Add($weekLabel)

$weekPicker = New-Object System.Windows.Forms.DateTimePicker
$weekPicker.Format = "Custom"
$weekPicker.CustomFormat = "yyyy-MM-dd"
$weekPicker.Value = [datetime]::Today.AddDays(-(([int][datetime]::Today.DayOfWeek + 6) % 7))
$weekPicker.Location = New-Object System.Drawing.Point(176, 16)
$weekPicker.Size = New-Object System.Drawing.Size(230, 24)
$panel.Controls.Add($weekPicker)

$newWeekButton = New-Object System.Windows.Forms.Button
$newWeekButton.Text = "週を表示"
$newWeekButton.Location = New-Object System.Drawing.Point(414, 14)
$newWeekButton.Size = New-Object System.Drawing.Size(90, 28)
$panel.Controls.Add($newWeekButton)

$weekHint = New-Object System.Windows.Forms.Label
$weekHint.Text = "登録する日にチェックし、選択して内容を編集してください。"
$weekHint.Location = New-Object System.Drawing.Point(16, 48)
$weekHint.Size = New-Object System.Drawing.Size(540, 24)
$panel.Controls.Add($weekHint)

$dayList = New-Object System.Windows.Forms.CheckedListBox
$dayList.CheckOnClick = $true
$dayList.Location = New-Object System.Drawing.Point(16, 76)
$dayList.Size = New-Object System.Drawing.Size(220, 116)
$panel.Controls.Add($dayList)

$dayLabel = New-Object System.Windows.Forms.Label
$dayLabel.Location = New-Object System.Drawing.Point(250, 76)
$dayLabel.Size = New-Object System.Drawing.Size(280, 24)
$panel.Controls.Add($dayLabel)

$presetCombo = New-Object System.Windows.Forms.ComboBox
$presetCombo.DropDownStyle = "DropDownList"
$presetCombo.Location = New-Object System.Drawing.Point(250, 106)
$presetCombo.Size = New-Object System.Drawing.Size(190, 24)
$panel.Controls.Add($presetCombo)

$applyPresetButton = New-Object System.Windows.Forms.Button
$applyPresetButton.Text = "適用"
$applyPresetButton.Location = New-Object System.Drawing.Point(448, 104)
$applyPresetButton.Size = New-Object System.Drawing.Size(58, 28)
$panel.Controls.Add($applyPresetButton)

$presetName = New-Object System.Windows.Forms.TextBox
$presetName.Location = New-Object System.Drawing.Point(250, 142)
$presetName.Size = New-Object System.Drawing.Size(190, 24)
$panel.Controls.Add($presetName)

$savePresetButton = New-Object System.Windows.Forms.Button
$savePresetButton.Text = "よく使う入力に保存"
$savePresetButton.Location = New-Object System.Drawing.Point(448, 140)
$savePresetButton.Size = New-Object System.Drawing.Size(120, 28)
$panel.Controls.Add($savePresetButton)

$presetHint = New-Object System.Windows.Forms.Label
$presetHint.Text = "左の日付を除いた1日分の入力を名前付きで保存します。"
$presetHint.Location = New-Object System.Drawing.Point(250, 174)
$presetHint.Size = New-Object System.Drawing.Size(320, 40)
$panel.Controls.Add($presetHint)

$todayLabel = New-Object System.Windows.Forms.Label
$todayLabel.Text = [datetime]::Today.ToString("yyyy-MM-dd (ddd)", [Globalization.CultureInfo]::GetCultureInfo("ja-JP"))
$todayLabel.Location = New-Object System.Drawing.Point(336, 222)
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
    $datePicker.Enabled = $false
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
$saveButton.Text = "登録"
$saveButton.Location = New-Object System.Drawing.Point -ArgumentList 392, ($y + 8)
$saveButton.Size = New-Object System.Drawing.Size(54, 32)
$panel.Controls.Add($saveButton)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = "閉じる"
$cancelButton.Location = New-Object System.Drawing.Point -ArgumentList 452, ($y + 8)
$cancelButton.Size = New-Object System.Drawing.Size(54, 32)
$panel.Controls.Add($cancelButton)

function Initialize-Week {
  $selectedDate = $weekPicker.Value.Date
  $monday = $selectedDate.AddDays(-(([int]$selectedDate.DayOfWeek + 6) % 7))
  $weekPicker.Value = $monday
  $script:SelectedDay = -1
  $script:WeekValues = @()
  $dayList.Items.Clear()
  for ($i = 0; $i -lt 7; $i++) {
    $date = $monday.AddDays($i)
    $values = Copy-Values $script:ActiveDefaults
    $values.target_date = $date.ToString("yyyy-MM-dd")
    $script:WeekValues += ,$values
    $label = $date.ToString("MM/dd (ddd)", [Globalization.CultureInfo]::GetCultureInfo("ja-JP"))
    [void]$dayList.Items.Add($label, ($i -lt 5))
  }
  $dayList.SelectedIndex = 0
  Show-SelectedDay 0
}

$dayList.Add_SelectedIndexChanged({
    if ($dayList.SelectedIndex -ge 0 -and $dayList.SelectedIndex -ne $script:SelectedDay) {
      Show-SelectedDay $dayList.SelectedIndex
    }
  })

$newWeekButton.Add_Click({
    $answer = [System.Windows.Forms.MessageBox]::Show(
      "現在の週の未登録入力は破棄されます。別の週を表示しますか？",
      "週の切り替え",
      [System.Windows.Forms.MessageBoxButtons]::YesNo,
      [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($answer -eq [System.Windows.Forms.DialogResult]::Yes) { Initialize-Week }
  })

$applyPresetButton.Add_Click({
    $name = [string]$presetCombo.SelectedItem
    if ([string]::IsNullOrWhiteSpace($name)) { return }
    $date = $script:WeekValues[$script:SelectedDay].target_date
    $values = Copy-Values $script:Presets[$name]
    $values.target_date = $date
    $script:WeekValues[$script:SelectedDay] = $values
    Set-FormValues $values
  })

$savePresetButton.Add_Click({
    try {
      $name = $presetName.Text.Trim()
      if ([string]::IsNullOrWhiteSpace($name)) { throw "保存名を入力してください。" }
      if ($script:Presets.ContainsKey($name)) {
        $answer = [System.Windows.Forms.MessageBox]::Show(
          "「$name」を上書きしますか？", "よく使う入力",
          [System.Windows.Forms.MessageBoxButtons]::YesNo,
          [System.Windows.Forms.MessageBoxIcon]::Question
        )
        if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) { return }
      }
      $values = Copy-Values (Get-CurrentValues)
      [void]$values.Remove("target_date")
      $script:Presets[$name] = $values
      Save-Presets
      Refresh-PresetList
      $presetCombo.SelectedItem = $name
      [System.Windows.Forms.MessageBox]::Show("1日分の入力を保存しました。", "よく使う入力") | Out-Null
    }
    catch {
      [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, "保存エラー") | Out-Null
    }
  })

Refresh-PresetList
Initialize-Week

$cancelButton.Add_Click({
    $form.Close()
  })

$resetButton.Add_Click({
    $date = $script:WeekValues[$script:SelectedDay].target_date
    $values = Copy-Values $script:ActiveDefaults
    $values.target_date = $date
    Set-FormValues $values
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
      Save-SelectedDay
      $records = @()
      for ($i = 0; $i -lt 7; $i++) {
        if ($dayList.GetItemChecked($i)) { $records += ,$script:WeekValues[$i] }
      }
      if ($records.Count -eq 0) { throw "登録する日を1日以上選択してください。" }
      $dates = @($records | ForEach-Object { $_.target_date }) -join ", "
      $answer = [System.Windows.Forms.MessageBox]::Show(
        "次の日付をHRMOSとSARへ登録しますか？`n$dates",
        "一括登録の確認",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
      )
      if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) { return }
      Save-WorkRecords $records
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
