package main

import (
	"os"
	"path/filepath"
	"testing"

	"gopkg.in/yaml.v3"
)

func TestSavePresetOmitsDateAndLoadsAgain(t *testing.T) {
	root := t.TempDir()
	app := &App{root: root}
	if err := app.SavePreset("通常勤務", Record{
		"target_date":  "2026-09-14",
		"work_segment": "OFFICE",
		"start_time":   "09:00",
	}); err != nil {
		t.Fatal(err)
	}
	data, err := app.LoadData()
	if err != nil {
		t.Fatal(err)
	}
	if got := data.Presets["通常勤務"]["target_date"]; got != "" {
		t.Fatalf("preset retained target date: %q", got)
	}
	if got := data.Presets["通常勤務"]["start_time"]; got != "09:00" {
		t.Fatalf("wrong start time: %q", got)
	}
	if _, err := os.Stat(filepath.Join(root, "work_record_presets.json")); err != nil {
		t.Fatal(err)
	}
}

func TestRegisterRecordsRejectsDuplicateDatesBeforeWriting(t *testing.T) {
	root := t.TempDir()
	app := &App{root: root}
	record := Record{"target_date": "2026-09-14"}
	if _, err := app.RegisterRecords([]Record{record, record}); err == nil {
		t.Fatal("expected duplicate date error")
	}
	if _, err := os.Stat(filepath.Join(root, "work_records.yaml")); !os.IsNotExist(err) {
		t.Fatalf("unexpected YAML output: %v", err)
	}
}

func TestUpdatePresetRenamesAndPreservesOtherPresets(t *testing.T) {
	app := &App{root: t.TempDir()}
	if err := app.SavePreset("通常勤務", Record{"start_time": "09:00"}); err != nil {
		t.Fatal(err)
	}
	if err := app.SavePreset("在宅", Record{"start_time": "10:00"}); err != nil {
		t.Fatal(err)
	}
	if err := app.UpdatePreset("通常勤務", "早番", Record{"target_date": "2026-09-14", "start_time": "08:00"}); err != nil {
		t.Fatal(err)
	}
	data, err := app.LoadData()
	if err != nil {
		t.Fatal(err)
	}
	if _, exists := data.Presets["通常勤務"]; exists {
		t.Fatal("old preset name remains")
	}
	if data.Presets["早番"]["start_time"] != "08:00" || data.Presets["早番"]["target_date"] != "" {
		t.Fatal("renamed preset has wrong values")
	}
	if data.Presets["在宅"]["start_time"] != "10:00" {
		t.Fatal("another preset was changed")
	}
	if err := app.UpdatePreset("早番", "在宅", Record{}); err == nil {
		t.Fatal("expected a name collision error")
	}
}

func TestMarshalRecordsUsesRequestedFieldOrder(t *testing.T) {
	record := Record{
		"target_date": "2026-09-07", "work_segment": "OFFICE",
		"start_time": "09:30", "end_time": "22:00",
		"break1_start": "12:00", "break1_end": "13:00",
		"break2_start": "19:00", "break2_end": "19:30",
		"expense": "506", "sar_department_code": "A0320",
		"sar_project_code": "1592511", "sar_process": "IT",
		"sar_notes": "IT1のレビュー、各種依頼対応",
	}
	content, err := marshalRecords([]Record{record})
	if err != nil {
		t.Fatal(err)
	}
	want := "records:\n\n" +
		"- target_date: 2026-09-07\n" +
		"  work_segment: OFFICE\n" +
		"  start_time: \"09:30\"\n" +
		"  end_time: \"22:00\"\n" +
		"  break1_start: \"12:00\"\n" +
		"  break1_end: \"13:00\"\n" +
		"  break2_start: \"19:00\"\n" +
		"  break2_end: \"19:30\"\n" +
		"  expense: \"506\"\n" +
		"  original_start: \"\"\n" +
		"  original_end: \"\"\n" +
		"  notes: \"\"\n" +
		"  sar_department_code: \"A0320\"\n" +
		"  sar_project_code: \"1592511\"\n" +
		"  sar_process: \"IT\"\n" +
		"  sar_notes: \"IT1のレビュー、各種依頼対応\"\n"
	if string(content) != want {
		t.Fatalf("unexpected YAML:\n%s", content)
	}
	var parsed struct {
		Records []Record `yaml:"records"`
	}
	if err := yaml.Unmarshal(content, &parsed); err != nil {
		t.Fatal(err)
	}
	if len(parsed.Records) != 1 || parsed.Records[0]["sar_notes"] != record["sar_notes"] {
		t.Fatalf("YAML did not round-trip: %#v", parsed.Records)
	}
}
