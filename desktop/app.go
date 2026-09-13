package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

type Record map[string]string

type InitialData struct {
	Defaults Record            `json:"defaults"`
	Presets  map[string]Record `json:"presets"`
}

type App struct {
	ctx  context.Context
	root string
}

func NewApp() *App { return &App{} }

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.root, _ = findProjectRoot()
}

func findProjectRoot() (string, error) {
	starts := []string{}
	if cwd, err := os.Getwd(); err == nil {
		starts = append(starts, cwd)
	}
	if exe, err := os.Executable(); err == nil {
		starts = append(starts, filepath.Dir(exe))
	}
	for _, start := range starts {
		for dir := start; ; dir = filepath.Dir(dir) {
			if _, err := os.Stat(filepath.Join(dir, "src", "main.py")); err == nil {
				return dir, nil
			}
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
		}
	}
	return "", errors.New("プロジェクトの src/main.py が見つかりません")
}

func (a *App) projectRoot() (string, error) {
	if a.root != "" {
		return a.root, nil
	}
	return findProjectRoot()
}

func (a *App) LoadData() (InitialData, error) {
	root, err := a.projectRoot()
	if err != nil {
		return InitialData{}, err
	}
	data := InitialData{Defaults: defaultRecord(), Presets: map[string]Record{}}
	if err := readJSON(filepath.Join(root, "work_record_defaults.json"), &data.Defaults); err != nil {
		return data, err
	}
	if err := readJSON(filepath.Join(root, "work_record_presets.json"), &data.Presets); err != nil {
		return data, err
	}
	return data, nil
}

func defaultRecord() Record {
	return Record{
		"work_segment": "OFFICE", "start_time": "09:00", "end_time": "17:30",
		"break1_start": "12:00", "break1_end": "13:00", "break2_start": "",
		"break2_end": "", "expense": "0", "original_start": "", "original_end": "",
		"notes": "", "sar_department_code": "", "sar_project_code": "",
		"sar_process": "", "sar_notes": "",
	}
}

func readJSON(path string, target interface{}) error {
	content, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if len(strings.TrimSpace(string(content))) == 0 {
		return nil
	}
	return json.Unmarshal(content, target)
}

func (a *App) SavePreset(name string, values Record) error {
	name = strings.TrimSpace(name)
	if name == "" {
		return errors.New("保存名を入力してください")
	}
	root, err := a.projectRoot()
	if err != nil {
		return err
	}
	path := filepath.Join(root, "work_record_presets.json")
	presets := map[string]Record{}
	if err := readJSON(path, &presets); err != nil {
		return err
	}
	copy := Record{}
	for key, value := range values {
		if key != "target_date" {
			copy[key] = value
		}
	}
	presets[name] = copy
	content, err := json.MarshalIndent(presets, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(content, '\n'), 0600)
}

func (a *App) UpdatePreset(oldName, newName string, values Record) error {
	newName = strings.TrimSpace(newName)
	if newName == "" {
		return errors.New("保存名を入力してください")
	}
	root, err := a.projectRoot()
	if err != nil {
		return err
	}
	path := filepath.Join(root, "work_record_presets.json")
	presets := map[string]Record{}
	if err := readJSON(path, &presets); err != nil {
		return err
	}
	if _, exists := presets[oldName]; !exists {
		return fmt.Errorf("変更元の入力が見つかりません: %s", oldName)
	}
	if newName != oldName {
		if _, exists := presets[newName]; exists {
			return fmt.Errorf("同じ名前の入力が既にあります: %s", newName)
		}
	}
	copy := Record{}
	for key, value := range values {
		if key != "target_date" {
			copy[key] = value
		}
	}
	delete(presets, oldName)
	presets[newName] = copy
	content, err := json.MarshalIndent(presets, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(content, '\n'), 0600)
}

var datePattern = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`)
var segmentPattern = regexp.MustCompile(`^[A-Z_]+$`)

var recordFieldOrder = []string{
	"target_date", "work_segment", "start_time", "end_time",
	"break1_start", "break1_end", "break2_start", "break2_end",
	"expense", "original_start", "original_end", "notes",
	"sar_department_code", "sar_project_code", "sar_process", "sar_notes",
}

func marshalRecords(records []Record) ([]byte, error) {
	var output strings.Builder
	output.WriteString("records:\n")
	for _, record := range records {
		if !datePattern.MatchString(record["target_date"]) {
			return nil, fmt.Errorf("日付の形式が不正です: %s", record["target_date"])
		}
		if !segmentPattern.MatchString(record["work_segment"]) {
			return nil, fmt.Errorf("勤務区分が不正です: %s", record["work_segment"])
		}
		output.WriteString("\n")
		for index, key := range recordFieldOrder {
			prefix := "  "
			if index == 0 {
				prefix = "- "
			}
			value := record[key]
			if key != "target_date" && key != "work_segment" {
				quoted, err := json.Marshal(value)
				if err != nil {
					return nil, err
				}
				value = string(quoted)
			}
			fmt.Fprintf(&output, "%s%s: %s\n", prefix, key, value)
		}
	}
	return []byte(output.String()), nil
}

func (a *App) RegisterRecords(records []Record) (string, error) {
	if len(records) < 1 || len(records) > 7 {
		return "", errors.New("登録日は1〜7日を指定してください")
	}
	root, err := a.projectRoot()
	if err != nil {
		return "", err
	}
	seen := map[string]bool{}
	for _, record := range records {
		date := record["target_date"]
		if !datePattern.MatchString(date) {
			return "", fmt.Errorf("日付の形式が不正です: %s", date)
		}
		if _, err := time.Parse("2006-01-02", date); err != nil {
			return "", err
		}
		if seen[date] {
			return "", fmt.Errorf("日付が重複しています: %s", date)
		}
		seen[date] = true
	}
	python := filepath.Join(root, ".venv", "Scripts", "python.exe")
	if _, err := os.Stat(python); err != nil {
		return "", errors.New(".venv の Python が見つかりません")
	}
	if _, err := os.Stat(filepath.Join(root, "env.ps1")); err != nil {
		return "", errors.New("env.ps1 が見つかりません")
	}
	content, err := marshalRecords(records)
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(filepath.Join(root, "work_records.yaml"), content, 0600); err != nil {
		return "", err
	}
	command := exec.CommandContext(a.ctx, "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
		". './env.ps1'; & './.venv/Scripts/python.exe' './src/main.py' --input './work_records.yaml'")
	command.Dir = root
	output, err := command.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("勤怠登録に失敗しました: %w\n%s", err, string(output))
	}
	return "登録が完了しました", nil
}
