import {useEffect, useState} from 'react';
import {LoadData, RegisterRecords, SavePreset, UpdatePreset} from '../wailsjs/go/main/App';
import './App.css';

type RecordValues = {[key: string]: string};
type Day = {enabled: boolean; values: RecordValues};

const segments = [
  ['OFFICE', '出勤'], ['REMOTE', '在宅'], ['HOLIDAY', '公休'],
  ['SUBSTITUTE', '振休'], ['PAID_LEAVE', '有休'], ['SPECIAL_LEAVE', '特休'],
  ['ABSENCE', '欠勤'], ['SUBSTITUTE_WORK', '振出'],
  ['SUBSTITUTE_WORK_SUN', '振出(日曜)'], ['HALF_SUBSTITUTE_WORK', '半日振出'],
  ['HALF_SUBSTITUTE_WORK_SUN', '半日振出(日曜)'], ['TRAINING', '終日研修'],
  ['SUMMER_LEAVE', '夏季休暇'], ['HALF_OFFICE_REMOTE', '半日出社+在宅'],
  ['HALF_PAID_OFFICE', '半日有給+出社'], ['HALF_PAID_REMOTE', '半日有給+在宅'],
  ['HALF_SUBSTITUTE_OFFICE', '半日振休+出社'],
  ['HALF_SUBSTITUTE_REMOTE', '半日振休+在宅'],
  ['REMOTE_SUBSTITUTE', '在宅振出'], ['REMOTE_SUBSTITUTE_SUN', '在宅振出(日曜)'],
  ['HALF_HOLIDAY_REMOTE_SUB', '半日公休+在宅振出'],
  ['HALF_HOLIDAY_REMOTE_SUB_SUN', '半日公休+在宅振出(日曜)'],
];

const primaryFields: [string, string][] = [
  ['work_segment', '勤務区分'], ['start_time', '出勤'], ['end_time', '退勤'],
  ['break1_start', '休憩1開始'], ['break1_end', '休憩1終了'],
  ['break2_start', '休憩2開始'], ['break2_end', '休憩2終了'],
];

const detailFields: [string, string][] = [
  ['expense', '交通費'], ['original_start', '自社開始'],
  ['original_end', '自社終了'], ['notes', '備考'],
  ['sar_department_code', 'SAR部門'], ['sar_project_code', 'SAR PJ'],
  ['sar_process', 'SAR工程'], ['sar_notes', 'SAR備考'],
];

const allFields = [...primaryFields, ...detailFields];
const fieldWidths: {[key: string]: string} = {
  work_segment: '8%', start_time: '4%', end_time: '4%',
  break1_start: '4%', break1_end: '4%', break2_start: '4%', break2_end: '4%',
  expense: '4%', original_start: '4%', original_end: '4%', notes: '10%',
  sar_department_code: '5%', sar_project_code: '5%', sar_process: '5%', sar_notes: '10%',
};

function localDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function mondayOf(date: Date): Date {
  const result = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  result.setDate(result.getDate() - (result.getDay() + 6) % 7);
  return result;
}

function makeWeek(monday: Date, defaults: RecordValues): Day[] {
  return Array.from({length: 7}, (_, index) => {
    const date = new Date(monday);
    date.setDate(date.getDate() + index);
    return {enabled: index < 5, values: {...defaults, target_date: localDate(date)}};
  });
}

function RecordInput({fieldKey, value, onChange, label}: {
  fieldKey: string; value: string; onChange: (value: string) => void; label: string;
}) {
  if (fieldKey === 'work_segment') {
    return <select aria-label={label} value={value || 'OFFICE'} onChange={event => onChange(event.target.value)}>
      {segments.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
    </select>;
  }
  return <input aria-label={label} value={value || ''} onChange={event => onChange(event.target.value)}
    placeholder={fieldKey.includes('time') || fieldKey.endsWith('_start') || fieldKey.endsWith('_end') ? 'HH:mm' : ''} />;
}

function App() {
  const [defaults, setDefaults] = useState<RecordValues>({});
  const [presets, setPresets] = useState<{[name: string]: RecordValues}>({});
  const [weekStart, setWeekStart] = useState(localDate(mondayOf(new Date())));
  const [today, setToday] = useState(new Date());
  const [days, setDays] = useState<Day[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [editingPresetName, setEditingPresetName] = useState<string | null>(null);
  const [editingPresetTitle, setEditingPresetTitle] = useState('');
  const [editingPresetValues, setEditingPresetValues] = useState<RecordValues>({});

  useEffect(() => {
    LoadData().then(data => {
      setDefaults(data.defaults);
      setPresets(data.presets);
      setDays(makeWeek(mondayOf(new Date()), data.defaults));
    }).catch(error => setMessage(String(error)));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setToday(new Date()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  function updateDay(index: number, key: string, value: string) {
    setDays(current => current.map((day, i) => i === index
      ? {...day, values: {...day.values, [key]: value}} : day));
  }

  function changeWeek() {
    const date = new Date(`${weekStart}T00:00:00`);
    if (Number.isNaN(date.getTime())) { setMessage('週の開始日を確認してください'); return; }
    if (!window.confirm('現在の週の未登録入力を破棄して、別の週を表示しますか？')) { return; }
    const monday = mondayOf(date);
    setWeekStart(localDate(monday));
    setDays(makeWeek(monday, defaults));
    setMessage('週を切り替えました');
  }

  function applyPreset(index: number, name: string) {
    if (!presets[name]) { return; }
    setDays(current => current.map((day, i) => i === index
      ? {...day, values: {...defaults, ...presets[name], target_date: day.values.target_date}}
      : day));
  }

  async function savePreset(index: number) {
    const name = window.prompt('この1日分の入力を保存する名前');
    if (!name?.trim()) { return; }
    if (presets[name] && !window.confirm(`「${name}」を上書きしますか？`)) { return; }
    const values = {...days[index].values};
    delete values.target_date;
    try {
      await SavePreset(name, values);
      setPresets(current => ({...current, [name]: values}));
      setMessage(`「${name}」を保存しました`);
    } catch (error) { setMessage(String(error)); }
  }

  function openPresetEditor() {
    const first = Object.keys(presets).sort()[0];
    if (!first) { setMessage('よく使う入力はまだ保存されていません'); return; }
    setEditingPresetName(first);
    setEditingPresetTitle(first);
    setEditingPresetValues({...defaults, ...presets[first]});
  }

  function selectPresetForEditing(name: string) {
    setEditingPresetName(name);
    setEditingPresetTitle(name);
    setEditingPresetValues({...defaults, ...presets[name]});
  }

  async function saveEditedPreset() {
    if (!editingPresetName) { return; }
    try {
      const newName = editingPresetTitle.trim();
      await UpdatePreset(editingPresetName, newName, editingPresetValues);
      const values = {...editingPresetValues};
      delete values.target_date;
      setPresets(current => {
        const next = {...current};
        delete next[editingPresetName];
        next[newName] = values;
        return next;
      });
      setMessage(`「${newName}」を更新しました`);
      setEditingPresetName(null);
    } catch (error) {
      setMessage(String(error));
      window.alert(String(error));
    }
  }

  async function register() {
    const records = days.filter(day => day.enabled).map(day => day.values);
    if (!records.length) { setMessage('登録する日を選択してください'); return; }
    const dates = records.map(record => record.target_date).join(', ');
    if (!window.confirm(`${dates} をHRMOSとSARに登録しますか？`)) { return; }
    setBusy(true);
    setMessage('登録中です。完了までお待ちください。');
    try { setMessage(await RegisterRecords(records)); }
    catch (error) { setMessage(String(error)); }
    finally { setBusy(false); }
  }

  return <main>
    <header>
      <div><h1>勤怠入力</h1><p className="today">今日: {localDate(today)}（{'日月火水木金土'[today.getDay()]}）</p><p>1週間分を1日ずつ別行で編集できます。</p></div>
      <div className="toolbar">
        <button onClick={openPresetEditor} disabled={!Object.keys(presets).length || busy}>よく使う入力を編集</button>
        <label>週の開始日 <input type="date" value={weekStart} onChange={event => setWeekStart(event.target.value)} /></label>
        <button onClick={changeWeek} disabled={busy}>週を表示</button>
      </div>
    </header>
    <p className="hint">登録する日にチェックを入れてください。1日1行で、全項目を直接編集できます。</p>
    <div className="table-wrap"><table>
      <thead><tr><th className="check">登録</th><th className="date">日付</th><th className="preset">よく使う入力</th>
        {allFields.map(([key, label]) => <th key={key} style={{width: fieldWidths[key]}}>{label}</th>)}
      </tr></thead>
      <tbody>{days.map((day, index) => <tr key={day.values.target_date}>
        <td className="check"><input type="checkbox" aria-label={`${day.values.target_date} を登録`} checked={day.enabled} onChange={event => setDays(current => current.map((item, i) => i === index ? {...item, enabled: event.target.checked} : item))} /></td>
        <td className="date">{day.values.target_date}<small>{'日月火水木金土'[new Date(`${day.values.target_date}T00:00:00`).getDay()]}</small></td>
        <td className="preset"><div className="preset-cell"><select aria-label={`${day.values.target_date} よく使う入力`} value="" onChange={event => applyPreset(index, event.target.value)}><option value="">選択</option>{Object.keys(presets).sort().map(name => <option key={name}>{name}</option>)}</select><button onClick={() => savePreset(index)}>保存</button></div></td>
        {allFields.map(([key, label]) => <td key={key} className={key === 'work_segment' ? 'segment' : key === 'notes' || key === 'sar_notes' ? 'notes-cell' : 'compact-cell'}>
          <RecordInput fieldKey={key} value={day.values[key]} label={`${day.values.target_date} ${label}`} onChange={value => updateDay(index, key, value)} />
        </td>)}
      </tr>)}</tbody>
    </table></div>
    <footer><span role="status">{message}</span><button className="primary" onClick={register} disabled={busy || !days.length}>{busy ? '登録中…' : 'チェックした日を登録'}</button></footer>

    {editingPresetName !== null && <div className="modal-backdrop" role="presentation" onMouseDown={() => setEditingPresetName(null)}>
      <section className="modal preset-editor" role="dialog" aria-modal="true" aria-label="よく使う入力を編集" onMouseDown={event => event.stopPropagation()}>
        <div className="modal-head"><div><h2>よく使う入力を編集</h2><p>日付は保存対象に含まれません。</p></div><button onClick={() => setEditingPresetName(null)}>閉じる</button></div>
        <label className="preset-select">保存済みの入力 <select value={editingPresetName} onChange={event => selectPresetForEditing(event.target.value)}>{Object.keys(presets).sort().map(name => <option key={name}>{name}</option>)}</select></label>
        <label className="preset-select">タイトル <input value={editingPresetTitle} onChange={event => setEditingPresetTitle(event.target.value)} /></label>
        <div className="form-grid">{allFields.map(([key, label]) => <label key={key}>{label}
          <RecordInput fieldKey={key} value={editingPresetValues[key]} label={label} onChange={value => setEditingPresetValues(current => ({...current, [key]: value}))} />
        </label>)}</div>
        <div className="modal-actions"><button onClick={() => setEditingPresetName(null)}>キャンセル</button><button className="primary" onClick={saveEditedPreset}>変更を保存</button></div>
      </section>
    </div>}
  </main>;
}

export default App;
