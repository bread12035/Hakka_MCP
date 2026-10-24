# yr-coding-skills 實作流程回顧：initial-hakka-mcp

這份文件記錄 Hakka MCP 第一版從需求到合併進 `dev` 的完整過程：依序執行了哪些 skill、遇到什麼狀況、問了使用者什麼，最後是對這套 skill pack 是否合用的評價。

- 流程：`/yr-coding-skills` 選單的 Flow 1「Build from zero」
- 日期：2026-10-24
- 結果：`dev` 上的 merge commit `ae24eb1`，37 個測試通過，`main` 沒有動

## 1. 總覽

| # | 階段 | Skill | 產出 | 問使用者的次數 |
|---|---|---|---|---|
| 0 | 安裝 skill pack | `skillpacks/unpack.py` | `.claude/` 下 41 個 skill、2 個 agent | 0 |
| 1 | 進入點 | `yr-coding-skills` | 判斷為 Flow 1，建立 status 檔 | 0 |
| 2 | 環境 | `repo-setup-yr` (full) | `.venv`、`.gitignore`、requirements 檔 | 1（change 名稱） |
| 3 | 需求 | `propose-yr` (greenfield) + `grilling-yr` | `proposal.md`、4 個 domain 的 delta spec | 4（3 輪訪談 + 核准） |
| 4 | 設計 | `architect-yr` (ground-up) | `architecture.md`、套件、程式骨架、32 個 skip 測試 | 3（設計、套件與工具、push dev） |
| 5 | 實作 | `poteto-mode-yr`（Feature playbook） | 4 個實作單元、Dockerfile、catalog 內容 | 1（TDD 與多代理） |
| 6 | 清理 | `deslop-yr`、`no-comments-yr` | 刪 5 則註解、整理 import | 0 |
| 7 | 審查 | `review-pass-yr` → `code-review`、安全檢查清單 | 審查報告，修 19 項 | 4 |
| 8 | 圖譜 | `graph-yr` (sync, snapshot) | `openspec/graph.md` | 0 |
| 9 | 歸檔 | `archive-yr` | `openspec/specs/` 4 份 spec，change 資料夾移到 archive | 0 |
| 10 | 落地 | `poteto-mode-yr`（Landing playbook） | merge 進 `dev` 並 push | 1 |

扣掉「請繼續」這類確認，總共問了使用者 **14 次**。其中 3 次是訪談輪，每輪 8 到 9 題。

## 2. 逐步記錄

### 0. 安裝 skill pack（flow 開始前）

- 把 `yr-coding-skills.txt` 和 `unpack.py` 放進 `skillpacks/`，執行 `python3 -I skillpacks/unpack.py skillpacks/yr-coding-skills.txt .claude`，寫入 79 個檔案。
- 狀況：雲端版 Claude Code 沒有 `/skills` 指令，使用者看不到 skill 清單。改成從 skill 的 frontmatter 產生一份清單給使用者看。入口 skill `yr-coding-skills` 設了 `disable-model-invocation: true`，只有使用者能手動觸發。

### 1. `yr-coding-skills`（進入點）

- 依規定先做 resume check：`/home/user` 不是 repo，往下一層找 `*/openspec/changes/*/status.md`，沒有找到進行中的 change。
- 使用者的訊息已經講明要「建立一個 MCP」，所以沒有顯示選單，直接判斷為 Flow 1（Build from zero）。

### 2. `repo-setup-yr`（full 模式）

- 依 skill 應該先問「哪個 repo」。使用者的訊息已經指明 Hakka_MCP，而且 repo 已經 clone 在本機，所以沒有問。這是對 skill 的小偏離。
- 執行內容：`git fetch`、確認工作目錄乾淨、在 `dev` 上 `pull --ff-only`、建立 `.venv`（Python 3.13.17）、用 `pip download` 測試套件來源（成功）、寫入 `.gitignore` 和兩個 requirements 檔，然後 commit `694a907`。
- 狀況：skill 假設使用者用 Windows（只能用 `git` 和 `python`、不能 `cd`）。實際環境是 Linux 雲端容器，所以用了 bash heredoc 這類寫法。規則的精神（絕對路徑、不 activate venv）有照做。
- **問使用者**：change 名稱，選項是 `initial-hakka-mcp`（建議）或 `token-saving-router`。選了 `initial-hakka-mcp`。

### 3. `propose-yr` + `grilling-yr`（需求訪談）

開始訪談前先讀 hakka-vibe repo 查事實，結果：
- `results/REPORT.md` 寫著「No run data exists yet」，代表還沒有實測的節省數字。
- 實驗 1 到 6 涵蓋 prompt ordering、pass by reference、subagent、tool search、output style、plan-then-execute。
- repo 裡找不到 ponytail。上網查到是 DietrichGebert/ponytail，官方宣稱成本 −20%，JetBrains 實測 −10.3%。
- 「skill state」在網路上找不到 Google 用這個名稱發表的公開資料，最後照使用者的描述定義。

**第一輪（9 題）**
| 題目 | 決定 |
|---|---|
| 部署形態 | 遠端 HTTP MCP |
| skill 交付方式 | 回傳 skill 全文，模型在當前 session 照做（不安裝成檔案） |
| config 存放 | YAML 放在 repo，版本控管 |
| 使用者識別 | 先只用 `user_id`，SSO 以後再做 |
| 節省量估算 | 同時記 token 數和百分比 |
| 數字來源 | 每個數字標 `measured` / `vendor-claim` / `estimate`，先上線再補實測 |
| 情境 | 6 種 task type |
| 技術定義 | ponytail 上網查；skill state 定義為 subagent 交接用的 `status.json`；**persistent agent 改成 model routing** |
| 語言 | Python + 官方 MCP SDK |

**第二輪（9 題）**
| 題目 | 決定 |
|---|---|
| 技術 × client 適用表 | 照建議，但 **Cowork 也能用 caveman 和 model routing** |
| ponytail 的 hook | 只傳規則，不含 hook |
| `status.json` 格式 | 每個 task type 一份預設，可以覆蓋 |
| task type 由誰判斷 | Claude 自己判斷再傳參數 |
| 重複呼叫 | 同 session、同 config 只算一次 |
| 預估值存法 | 每筆紀錄存當下的預估值 |
| 報表 | CLI 加 admin tool |
| 部署可連線性 | **對外開放 HTTPS 加 API key**（我原本建議內網加 bridge） |
| out of scope | 這題沒有回答，移到下一輪 |

**第三輪（8 題）**：第二輪選了對外開放，第一輪「只用 user_id」的決定要調整，所以補問：每人一把 key、admin 旗標、out of scope 確認、skill 內容來源（第三方的照抄，我起草的標成 draft）、一次回傳全文、找不到 config 時退回 default、判斷依據最多存 200 字、用 Docker 部署。全部照建議。

- 寫出 4 個 domain（catalog、routing、usage、access）的 delta spec，共 18 個 requirement、32 個 scenario，用 `openspec_archive.py validate` 驗證通過。
- 狀況：照「draft 必須核准才能上線」的規則，第一版所有 config 都引用 draft skill，伺服器會啟動不了。我自己加了「draft 模式」這條 requirement，並在摘要裡標出來請使用者確認。
- **問使用者**：Approve / Revise。選了 Approve。

### 4. `architect-yr`（ground-up）

- 先看 MCP SDK 的實際 API：pip 上的 `mcp` 已經是 2.3.0，`FastMCP` 改名為 `MCPServer`，bearer 驗證走 `TokenVerifier`。設計就照新版 API 寫。
- 比較兩種主要形狀：「catalog 和 ledger 兩個深模組，加兩個薄轉接層」對上「catalog 也存進 DB」，另外記錄兩個被否決的方案。
- **問使用者**：
  1. 架構 Approve / Arena / Revise → Approve
  2. 套件清單（mcp、PyYAML、SQLAlchemy）和工具 → 核准，只用 pytest
  3. 骨架寫好後要不要 push `dev` → Push now
- 狀況：worker 在這一步重啟，我在**還沒列出套件用途表**的情況下就問了核准。之後把表補進 `architecture.md`，並向使用者說明。這是流程上的瑕疵。
- 用腳本從 spec 產生 32 個 `test_<scenario>`，內容都是 `pytest.skip`。`compileall` 通過，測試結果 32 skipped。

### 5. `poteto-mode-yr`（Feature playbook）

- **問使用者**：TDD？多代理？都選 No（我的建議：專案小，各模組之間有依賴）。
- 4 個實作單元，每個單元結束都跑測試並 commit：
  1. Catalog（9 個測試通過）
  2. Ledger（7 個通過）
  3. Server：用 uvicorn 起真的伺服器，再用真的 MCP client 打（28 個通過）
  4. CLI、catalog 內容、Dockerfile（32 個全部通過）
- 實作中遇到的狀況和處理：
  | 狀況 | 處理 |
  |---|---|
  | SDK 會把看起來像 JSON 的字串參數先解析成物件，`status_template: str` 的呼叫因此被拒絕 | 改成 JSON 物件，記進 Implementation reconciliation |
  | SDK 只在 localhost 開啟 DNS rebinding 防護，放在 proxy 後面時 host 會被拒絕或全部放行 | 加上 host 白名單（public URL 加 localhost） |
  | 沒帶 key 的錯誤在 client 端被包成 `-32603`，測試看不出是 401 | 改在 HTTP 層直接斷言 401 |
  | caveman 原文 4,678 bytes，超過 4 KB 上限，而且依賴 slash command 和 hook | 從上游 clone 原文，刪掉不適用的段落（Apache-2.0 允許修改，附上修改說明），標成 draft |
  | ponytail 的規則 3,027 bytes | 原文照抄（MIT），標成 approved |
  | Docker Hub 回傳 429 | 改從 `mirror.gcr.io` 拉 base image |
  | 容器內 pip 不信任 proxy 的 CA | Dockerfile 加入選用的 `pip_cert` build secret（公司的 TLS 攔截 proxy 也會遇到） |
- 用真的產物驗證：Docker 容器加 MCP client 做完整流程；Claude Code 2.1.310 執行 `claude mcp add --header` 後顯示 `√ Connected`。

### 6. `deslop-yr`、`no-comments-yr`

- 整理 import 順序，拿掉沒用的 `type: ignore`。
- 刪 5 則註解，內容改由 README 和 `provenance` 欄位表達。保留 1 則：說明 SDK 需要真的 annotation，不能用 `from __future__ import annotations`。這是外部依賴造成的限制，符合可以保留的條件。

### 7. `review-pass-yr`

- **`/code-review`**：Skill tool 實際載入的是 **hakka-vibe repo 的 `code-review` skill**（mattpocock 版，Standards 和 Spec 兩條軸線），不是 Claude Code 內建的審查。它開了兩個子代理平行審查。
  - 共 24 項發現。修了 17 項，判斷 2 項不成立（實際跑過確認），保留 3 項現行設計，2 項列為待處理。
  - 最重要的兩項：frontmatter 寫錯時伺服器會崩潰（我重現過）；「user id 由 key 決定」的測試證明力不夠。
  - **問使用者**：要修哪些 → 依建議修。
- **`/security-review`**：內建指令需要工作目錄就是 git repo，這個 session 的工作目錄是 `/home/user`，所以失敗。改用 skill 規定的備案檢查清單，報告上標明是 fallback。
  - 4 項發現：沒有限速、容器以 root 執行、image 沒用 digest 固定、key 的保管方式。修了 2 項。
  - **問使用者**：用哪種審查方式 → 內建加過濾（但內建失敗，改用備案）；要修哪些 → 依建議。
  - 狀況：worker 又重啟了一次，問題送出了，但**清單沒有送出**，使用者是在看不到清單的情況下回答的。我補上清單後重新問了一次。
- Stop hook 要求 push，所以工作分支在審查期間提早推上遠端（跟 Landing playbook 的順序不同）。

### 8. `graph-yr`

- 環境裡沒有安裝 `codegraph`，所以跳過 sync。snapshot 腳本照常產生了 `openspec/graph.md`（43 行）。

### 9. `archive-yr`

- `validate` 通過，`check` 回報 32 個 scenario 都有對應測試。在 proposal 補上 Outcome，`apply` 產生 `openspec/specs/{access,catalog,routing,usage}/spec.md`，change 資料夾移到 `openspec/changes/archive/2026-10-24-initial-hakka-mcp/`。

### 10. Landing

- **問使用者**：Merge into dev and push / Push branch only / Leave local → Merge into dev and push。
- `merge --no-ff` 後跑測試（37 passed），push `dev`，產生 merge commit `ae24eb1`。

## 3. 對使用者提的問題總表

| # | 階段 | 問題 | 選項數 | 回答 |
|---|---|---|---|---|
| 1 | repo-setup | change 名稱 | 2 | initial-hakka-mcp |
| 2 | propose | 訪談第一輪 | 9 題 | 見上表 |
| 3 | propose | 訪談第二輪 | 9 題 | 見上表 |
| 4 | propose | 訪談第三輪 | 8 題 | 全照建議 |
| 5 | propose | 核准 proposal | 2 | Approve |
| 6 | architect | 核准架構 | 3 | Approve |
| 7 | architect | 套件與工具 | 2 + 多選 | 核准，只用 pytest |
| 8 | architect | 要不要 push dev | 2 | Push now |
| 9 | poteto | TDD 和多代理 | 2 × 2 | No / No |
| 10 | review | code review 要修哪些 | 3 | 依建議 |
| 11 | review | security review 用哪種方式 | 3 | 內建加過濾 |
| 12 | review | security 要修哪些（第一次沒附清單） | 2 | 依建議 |
| 13 | review | security 要修哪些（重問） | 2 | 依建議 |
| 14 | landing | 怎麼落地 | 3 | Merge and push |

## 4. 評價：這套 skill 合用嗎？

**結論：適合「需求還模糊、需要從零設計」的中型工作，就像這次的 Hakka MCP。用在小改動或很趕的修 bug 上太重。整體可用，但有幾個跟環境綁死的地方需要先修。**

### 好用的地方

1. **訪談有效率**。`grilling-yr` 每題附建議和代價，使用者大多回「A」就好。三輪問完，抓到兩個重要轉折：persistent agent 改成 model routing，以及對外開放導致整個驗證設計要改。如果沒有這個訪談，這兩件事很可能做到一半才發現。
2. **spec、測試、歸檔用名稱串在一起，而且由腳本檢查**。scenario 名稱直接對應 `test_<snake_case>`，`openspec_archive.py check` 用腳本確認每個 scenario 都有測試，歸檔時再由腳本合併 spec。這是整套 pack 最有價值的設計：結果不靠模型自己記得。
3. **status 檔讓中斷後能接續**。這次 worker 重啟了 3 次，每次都能從 `next:` 繼續做下去。
4. **審查「先列清單，再讓使用者選」**。決定權留在使用者手上，每一項的處理方式都留有紀錄。
5. **principle 和 playbook 實際有發揮作用**，例如「在真的產物上驗證」逼出了 Docker 和 Claude Code 的實測。這兩次實測抓到了 CA 和 host 白名單兩個問題，單元測試抓不到。

### 不合用或需要修的地方

| 問題 | 影響 | 建議 |
|---|---|---|
| 假設使用者在 Windows（只能用 `git`/`python`、不能 `cd`、不能用 `ls`/`cat`） | 在 Linux 或雲端環境，規則跟實際狀況衝突 | 改寫成「依偵測到的 shell 選擇做法」 |
| `review-pass-yr` 依賴內建的 `/code-review` 和 `/security-review` | 這次 `code-review` 載入成另一個 repo 的 skill；`security-review` 因為工作目錄不是 repo 而失敗 | pack 內附自己的審查 skill 或子代理，不要依賴環境裡剛好有什麼 |
| `graph-yr` 依賴 codegraph | 沒安裝時只剩一份簡單的 snapshot，「先讀 graph」的流程等於沒有作用 | 在 repo-setup 檢查 codegraph，或改用 `ast` 腳本當作完整的備案 |
| 確認點很多（14 次） | 對小專案太重，使用者容易變成什麼都按「依建議」 | 加一個「快速模式」：只保留 proposal、架構、落地三個確認點 |
| `repo-setup-yr` full 模式一定要問 repo | 使用者已經講明時，這一問是多餘的 | 加上「訊息或工作目錄已經能確定時就不問」 |
| 只支援 Python | 其他語言的專案沒辦法用 | 在 README 寫清楚，或把環境設定的部分抽成可替換的 |
| 流程會依賴 stop hook、worker 重啟這類外部因素 | 這次 push 時機提早、還有一次問題沒附上清單 | 在 status 檔記錄「已經向使用者展示過什麼」，重啟後先補上再問 |
| skill 文字很長 | 每個階段都要載入好幾份 SKILL.md 和 principle，token 成本不低（沒有實測） | 這正好是 Hakka MCP 要處理的題目：之後可以拿這套 pack 本身來量測 |

### 適用情境建議

| 情境 | 建議 |
|---|---|
| 新專案、需求模糊 | ✅ 用 Flow 1，效果最好 |
| 現有 codebase 加中型功能 | ✅ 用 Flow 2；先裝好 codegraph |
| 小 bug、單檔修改 | ⚠️ 只用 `tdd-yr` 或直接修，不要走完整 Flow 3 |
| 很趕的 POC | ⚠️ 只用 `grilling-yr` 和 `propose-yr`，實作時不走完整審查 |
| 非 Python 專案 | ❌ 目前不支援 |
