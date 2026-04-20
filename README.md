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
- Python 3.11 at `C:\Python311\python.exe`
- [`sk-wwise-mcp`](https://github.com/sokolkreshnik/sk-wwise-mcp) installed at `~/sk-wwise-mcp` (requires Wwise 2025.x)

## Setup

### 1. Enable WAAPI in Wwise

**Wwise Launcher → Wwise → Settings → Enable Wwise Authoring API**

### 2. Register the right-click command

Run `register.bat` (or `python register.py`) while Wwise is open.  
This registers `Auto-Assign Switches by Name` as a Wwise command.

> Re-run after every Wwise restart — command registration is session-only.

### 3. Assign a keyboard shortcut

In Wwise: **Edit → Keyboard Shortcuts** → search `AutoAssign` → assign your preferred shortcut (e.g. `Ctrl+Shift+A`).

## Usage

1. Select a Switch Container in Wwise
2. Press your assigned shortcut (or invoke the command from Keyboard Shortcuts)
3. Review the assignment preview in the dialog
4. Click **Yes** to apply

## Files

| File | Description |
|------|-------------|
| `register.py` | Registers the Wwise command via WAAPI |
| `register.bat` | Double-click shortcut to run `register.py` |
| `auto_assign.py` | Worker — called by Wwise when the command is triggered |
| `debug_register.py` | Diagnostic tool for troubleshooting registration |

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
- Python 3.11 (`C:\Python311\python.exe`)
- [`sk-wwise-mcp`](https://github.com/sokolkreshnik/sk-wwise-mcp) (`~/sk-wwise-mcp` 경로에 설치, Wwise 2025.x 전용)

### 설치 방법

#### 1. Wwise WAAPI 활성화

**Wwise Launcher → Wwise → Settings → Enable Wwise Authoring API**

#### 2. 커맨드 등록

Wwise가 열려있는 상태에서 `register.bat` 더블클릭 (또는 `python register.py` 실행).  
Wwise에 `Auto-Assign Switches by Name` 커맨드가 등록됩니다.

> Wwise를 재시작할 때마다 다시 실행해야 합니다 (커맨드 등록은 세션 단위).

#### 3. 키보드 단축키 지정

Wwise: **Edit → Keyboard Shortcuts** → `AutoAssign` 검색 → 원하는 단축키 지정 (예: `Ctrl+Shift+A`)

### 사용 방법

1. Wwise에서 Switch Container 선택
2. 지정한 단축키 입력
3. Assignment 미리보기 다이얼로그 확인
4. **Yes** 클릭하여 적용

### 파일 설명

| 파일 | 설명 |
|------|------|
| `register.py` | WAAPI로 Wwise 커맨드 등록 |
| `register.bat` | `register.py`를 더블클릭으로 실행하는 배치 파일 |
| `auto_assign.py` | 커맨드 실행 시 Wwise가 호출하는 워커 스크립트 |
| `debug_register.py` | 등록 문제 진단용 디버그 도구 |
