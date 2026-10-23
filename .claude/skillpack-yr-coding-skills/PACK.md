# yr-coding-skills（第二版）

我自己的 coding skills 包。一個入口 `/yr-coding-skills`，四條流程，子 skills 沿用原名並加 `-yr`。核心是 pstack（poteto-mode、architect），需求用 OpenSpec 風格的 proposal，程式圖用 codegraph。

## 安裝（Windows，裝在使用者層）

需要 Python 3。在 PowerShell：

```
python unpack.py --replace yr-coding-skills.txt $HOME\.claude
```

`--replace` 會先依 MANIFEST 移除舊版再安裝，所以第一版的 `grill-with-docs-yr`、`domain-modeling-yr` 會一起清掉。第一版如果裝在專案層，請對那個專案的 `.claude` 資料夾再執行一次 `python unpack.py --remove yr-coding-skills <路徑>`，避免專案層的舊版蓋過使用者層的新版。

重新開啟 VS Code 的 Claude Code，輸入 `/skills` 確認，然後輸入 `/yr-coding-skills`。

其他指令：`--list`（列出包內檔案）、`--force`（覆蓋已存在的 skill）、`--remove yr-coding-skills <路徑>`（移除）。

## 入口選單

1. 從 0 開始建構（ground-up）
2. 現有 codebase 新增功能
3. Debug
4. Refactor
5. 列出現有子 skills 與功能

## 流程

| 流程 | 步驟 |
|---|---|
| 1 ground-up | repo-setup（clone 或 pull、dev、venv）→ propose（greenfield）→ architect（ground-up：套件、工具、skeleton）→ 設計 push 到 dev → feat 分支 → poteto-mode（Feature）→ review → graph → archive → Landing |
| 2 add feature | repo-setup（light）→ 你描述需求 → feat 分支 → graph read → propose（feature）→ poteto-mode（Feature，跨模組時 architect design-only）→ review → graph → archive → Landing |
| 3 debug | repo-setup（light）→ 你描述 bug → fix 分支 → graph read → poteto-mode（Bug fix，**找到原因後停下等你核准**）→ review → graph → archive → Landing |
| 4 refactor | repo-setup（light）→ 你描述問題 → refactor 分支 → graph read → poteto-mode（Refactoring：先確認行為契約，跨模組時 architect design-only，可用 arena）→ review → graph → archive → Landing |

poteto-mode-yr 開工前會問兩件事：要不要 TDD、要不要 sub-agents。預設都不用，答案存在 `status.md`。

## 檔案放哪裡

```
openspec/
  specs/<domain>/spec.md            目前系統的需求與情境
  changes/<name>/                   進行中的變更
    proposal.md  specs/<domain>/spec.md  architecture.md  status.md
  changes/archive/<日期>-<name>/    做完的變更
  reviews/<name>.md                 審查報告
  graph.md                          可讀的程式結構快照（由腳本產生）
.codegraph/                         codegraph 的即時索引（不進 git）
```

文件與 commit 一律英文，對話用繁體中文。

## 與第一版的差異

- **需求**：`propose-yr` 取代 `grill-with-docs-yr`。只有 proposal 和 delta spec，沒有 design.md、tasks.md、GLOSSARY、ADR。訪談方式仍用 `grilling-yr`（選項加建議方案）。
- **spec 合併**：`archive-yr` 附一支 Python 腳本，做 ADDED / MODIFIED / REMOVED 的合併並搬進 archive，不需要 OpenSpec CLI 或 npm。也會檢查每個情境有沒有對應測試（`test_<情境名稱的 snake_case>`）。
- **分支**：一律以 `dev` 為基準，工作在 `feat/`、`fix/`、`refactor/` 分支。不碰 master。最後 Landing 合併進 dev 並 push，要不要 PR 到 master 由你手動做（可以產出 PR 文字）。
- **審查**：只有 `/code-review` 和 `/security-review`，沒有 `/simplify`。先列問題，你選要修哪些。`/security-review` 預設比對 master，所以 skill 會先比較範圍，再讓你選擇。
- **graph**：`graph-yr` 用 codegraph 做即時索引和查詢，另外用腳本產生 `openspec/graph.md`（只支援 Python，不依賴 codegraph），codegraph 的補充放在檔案的 notes 區塊。沒有 codegraph 時自動略過。
- **architect-yr**：附 `references/micro-service-architecture.md`，是事件驅動 micro-service 的參考架構（分層、ack/nack 對照表、一事件一 thread、layer test）。proposal 描述這類 service 時會讀它，可採用、調整或拒絕。既有程式只寫 `architecture.md`，不寫 skeleton。新專案才會核准並安裝套件、選工具（pytest、ruff、mypy）、寫 skeleton 和每個情境一個 skip 的測試。
- **poteto-mode-yr**：新增 Landing playbook，移除 Opening a PR。Bug fix 加核准點，Refactoring 加行為契約確認。
- **優先順序**：poteto-mode-yr 的 playbook 和 `architecture.md` 衝突時，以 playbook 為準，並同步更新 `architecture.md`。playbook 只管流程；程式結構放在 `architect-yr`。
- Landing 時如果 spec 檔案和 `dev` 衝突，可用 `archive-yr` 腳本的 `remerge` 重新套用 delta。
- 入口有 `status.md` 續跑機制：中斷後再執行 `/yr-coding-skills` 會偵測到並問你要不要繼續。

## 注意事項

- 這個包的環境設定假設專案是 Python（venv + requirements.txt）。
- pip proxy：VS Code 的設定不一定被 Claude Code 的 shell 讀到。`repo-setup-yr` 會先測試安裝，失敗就停下來，不會猜 URL。
- `codegraph` 的 CLI 指令我只讀過原始碼，沒有實際執行。skill 會先看 `codegraph --help`，以實際輸出為準。skill 永遠不會執行 `codegraph install`。
- `/code-review` 對分支的比對範圍文件沒寫清楚。`review-pass-yr` 會檢查它回報的檔案是否在 `dev...HEAD` 內，不在的標記為範圍外。
- 沒有 SessionStart hook，也不改 `CLAUDE.md`。路由只靠入口 skill。

## 授權

來源皆為 MIT：mattpocock/skills（grilling、tdd 等）、poteto（Lauren Tan）pstack 的社群 Claude Code 移植版（michael-denyer/pstack-claude），以及 cursor-team-kit（deslop）。目錄結構參考 OpenSpec（MIT），本包不含 OpenSpec 的程式碼。授權與 NOTICE 在 `LICENSE-*` 與 `NOTICE-*` 檔。本包中入口、`repo-setup-yr`、`propose-yr`、`graph-yr`、`archive-yr`、`review-pass-yr`、`architect-yr`、`poteto-mode-yr` 與 playbooks 為改寫或新寫。
