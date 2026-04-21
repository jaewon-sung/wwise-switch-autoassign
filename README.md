# WwiseSwitchAutoAssign

Automatically assigns children of a Wwise Switch Container to their matching Switch values based on name token matching.

## How It Works

The script splits both the Switch name and each child object's name by `_` into tokens, then checks whether all tokens of the Switch name appear in the child's token set (case-insensitive).

**Examples:**
- Switch: `Walk` / Child: `SFX_Walk_Loop` → `{walk} ⊆ {sfx, walk, loop}` → **Assigned**
- Switch: `a` / Child: `name_a_SFX` → `{a} ⊆ {name, a, sfx}` → **Assigned**
- Switch: `Walk_Fast` / Child: `SFX_Walk_Fast_01` → `{walk, fast} ⊆ {sfx, walk, fast, 01}` → **Assigned**
- Child matches multiple switches of equal token count → **Skipped (ambiguous)**

When multiple switches match the same child, the most specific one (most tokens) wins. Existing assignments are cleared before new ones are applied.

## Requirements

- Wwise 2025.x with WAAPI enabled
- Python 3.10+ in system PATH
- [`sk-wwise-mcp`](https://github.com/sokolkreshnik/sk-wwise-mcp) installed at `~/sk-wwise-mcp` (requires Wwise 2025.x)

## Setup

### 1. Enable WAAPI in Wwise

**Wwise Launcher → Wwise → Settings → Enable Wwise Authoring API**

This is a one-time setting.

### 2. Copy files to Wwise Add-ons

Copy the entire `WwiseSwitchAutoAssign` folder anywhere on your machine, then add the following entry to:

```
%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands\commands.json
```

```json
{
    "id": "WwiseSwitchAutoAssign.AutoAssignByName",
    "displayName": "Auto-Assign Switches by Name",
    "program": "C:\\path\\to\\WwiseSwitchAutoAssign\\run.bat",
    "args": "{objects}"
}
```

Replace `C:\\path\\to\\` with the actual folder path. After this, the command is registered automatically every time Wwise starts — no manual re-registration needed.

### 3. Assign a keyboard shortcut

In Wwise: **Edit → Keyboard Shortcuts** → search `AutoAssign` → assign your preferred shortcut (e.g. `Ctrl+Shift+A`).

This is a one-time setting. The shortcut persists across Wwise restarts.

## Usage

1. Select one or more Switch Containers in Wwise
2. Press the assigned shortcut
3. Review the combined assignment preview in the dialog
4. Click **Yes** to apply all at once

**Multiple selection is fully supported:**
- Switch Containers sharing the same Switch Group → each matched against the same switch list
- Switch Containers using different Switch Groups → each matched against its own switch list
- Non-Switch Container objects in the selection are automatically skipped

## Files

| File | Description |
|------|-------------|
| `auto_assign.py` | Worker — called by Wwise when the command is triggered |
| `run.bat` | Launcher — invokes `auto_assign.py` via Python |

---

> **한국어 설명은 아래에 있습니다.**

---

## 한국어 설명

Wwise Switch Container의 자식 오브젝트를 이름 토큰 매칭으로 Switch 값에 자동으로 assign하는 스크립트입니다.

### 동작 방식

Switch 이름과 자식 오브젝트 이름을 각각 `_`로 분리해 토큰화한 뒤, Switch의 모든 토큰이 자식 이름의 토큰에 포함되면 매칭으로 판단합니다 (대소문자 구분 없음).

**예시:**
- Switch: `Walk` / 자식: `SFX_Walk_Loop` → `{walk} ⊆ {sfx, walk, loop}` → **Assign**
- Switch: `a` / 자식: `name_a_SFX` → `{a} ⊆ {name, a, sfx}` → **Assign**
- Switch: `Walk_Fast` / 자식: `SFX_Walk_Fast_01` → `{walk, fast} ⊆ {sfx, walk, fast, 01}` → **Assign**
- 같은 토큰 수의 Switch가 여러 개 매칭 → **스킵 (ambiguous)**

여러 Switch가 매칭될 경우 토큰 수가 가장 많은 것(가장 구체적인 것)이 우선 선택됩니다. 적용 전에 기존 Assignment는 전부 초기화됩니다.

### 요구 사항

- Wwise 2025.x (WAAPI 활성화 필요)
- Python 3.10 이상 (시스템 PATH에 등록되어 있어야 함)
- [`sk-wwise-mcp`](https://github.com/sokolkreshnik/sk-wwise-mcp) (`~/sk-wwise-mcp` 경로에 설치, Wwise 2025.x 전용)

### 설치 방법

#### 1. Wwise WAAPI 활성화

**Wwise Launcher → Wwise → Settings → Enable Wwise Authoring API**

최초 1회만 설정하면 됩니다.

#### 2. Wwise Add-ons에 커맨드 등록

`WwiseSwitchAutoAssign` 폴더를 원하는 경로에 저장한 뒤, 아래 파일을 편집합니다:

```
%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands\commands.json
```

`commands` 배열에 아래 항목을 추가합니다:

```json
{
    "id": "WwiseSwitchAutoAssign.AutoAssignByName",
    "displayName": "Auto-Assign Switches by Name",
    "program": "C:\\실제\\폴더\\경로\\WwiseSwitchAutoAssign\\run.bat",
    "args": "{objects}"
}
```

`program` 경로를 실제 폴더 위치에 맞게 수정해주세요. 이후 Wwise를 시작할 때마다 커맨드가 자동으로 등록됩니다. 별도의 재등록 작업이 필요 없습니다.

#### 3. 키보드 단축키 지정

Wwise: **Edit → Keyboard Shortcuts** → `AutoAssign` 검색 → 원하는 단축키 지정 (예: `Ctrl+Shift+A`)

최초 1회만 설정하면 Wwise 재시작 후에도 단축키가 유지됩니다.

### 사용 방법

1. Wwise에서 Switch Container를 하나 또는 여러 개 선택
2. 지정한 단축키 입력
3. 전체 컨테이너 매칭 결과를 한 번에 미리보기로 확인
4. **Yes** 클릭하여 일괄 적용

**다중 선택 지원:**
- 같은 Switch Group을 사용하는 여러 컨테이너 → 각각 같은 Switch 목록으로 매칭
- 다른 Switch Group을 사용하는 여러 컨테이너 → 각자 자기 Switch Group 기준으로 매칭
- Switch Container가 아닌 오브젝트가 섞여 있으면 자동으로 스킵

### 파일 설명

| 파일 | 설명 |
|------|------|
| `auto_assign.py` | 커맨드 실행 시 Wwise가 호출하는 워커 스크립트 |
| `run.bat` | `auto_assign.py`를 Python으로 실행하는 런처 |
