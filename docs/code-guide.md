# Hakka MCP 程式碼導讀與待辦事項

這份文件說明怎麼讀懂 Hakka MCP 的程式碼：先看什麼、資料怎麼流動、每個模組負責什麼、要改東西時該動哪裡。最後一節是接下來的待辦事項。

程式碼規模：`src/` 4 個模組、`tests/` 5 個檔案，合計約 1,400 行；37 個測試。

## 1. 一句話說明

Claude（Code 或 Cowork）在任務開始時呼叫 `route(client, task_type, session_id, rationale)`。伺服器從 catalog 找出對應的 config，回傳其中每個 skill 的全文，同時把這次使用和當時的預估節省量寫進資料庫。管理者再用 `get_usage_stats` 或 `hakka-mcp report` 查看統計。

## 2. 建議閱讀順序

照這個順序讀，每一步只需要前面讀過的東西。

| 順序 | 讀什麼 | 為什麼 | 花多久 |
|---|---|---|---|
| 1 | `README.md` | 從使用者和管理者的角度看系統怎麼用 | 5 分鐘 |
| 2 | `openspec/specs/*/spec.md` | 系統**應該**做什麼。每個 scenario 都是一條可以測試的行為 | 15 分鐘 |
| 3 | `catalog/` 資料夾（隨便打開一個 config 和一個 skill） | 你平常唯一要編輯的地方 | 5 分鐘 |
| 4 | `src/hakka_mcp/catalog.py` 前 165 行 | 核心型別：`Client`、`Technique`、`APPLICABILITY`、`Estimate`、`Config`、`Catalog` | 10 分鐘 |
| 5 | `src/hakka_mcp/server.py` | 一次 `route` 呼叫從頭到尾經過哪些地方 | 10 分鐘 |
| 6 | `src/hakka_mcp/ledger.py` | 資料怎麼存、統計怎麼算 | 10 分鐘 |
| 7 | `src/hakka_mcp/cli.py` | 管理者的指令 | 5 分鐘 |
| 8 | `tests/conftest.py`，再挑一個 `tests/test_*.py` | 測試怎麼起一個真的伺服器 | 10 分鐘 |
| 9 | `openspec/changes/archive/2026-10-24-initial-hakka-mcp/architecture.md` | 為什麼長成這樣、否決過哪些方案 | 10 分鐘 |

`openspec/graph.md` 是自動產生的模組總覽：誰 import 誰、各模組有哪些公開符號。迷路時可以先看這份。

## 3. 架構圖

```text
                 ┌──────────── catalog/ (YAML, SKILL.md, JSON) ────────────┐
                 │  configs/<client>/<task-type>.yaml                      │
                 │  skills/<id>/SKILL.md   templates/status/<task>.json    │
                 │  pricing.yaml                                            │
                 └──────────────────────────┬──────────────────────────────┘
                                            │ 啟動時讀一次，整份驗證
                                            ▼
 Claude Code ─┐   HTTPS + Bearer key   ┌──────────────┐   resolve()   ┌────────────┐
 Cowork ──────┼──────────────────────► │  server.py   │ ────────────► │ catalog.py │
              │                        │  (轉接層)     │               │  Catalog   │
              │  ◄──── skill 全文 ──── │ route        │               └────────────┘
              │                        │ get_usage_   │   record()    ┌────────────┐
 管理者 ───────┘                        │   stats      │ ────────────► │ ledger.py  │──► SQLite
   │                                    └──────────────┘ authenticate()│  Ledger    │   (之後換 Postgres)
   │  hakka-mcp check / serve / keys / report                          └────────────┘
   └──────────────► cli.py ───────────────────────────────────────────────▲
```

**分工規則**
- `catalog.py` 和 `ledger.py` 是兩個「深模組」，規則都在這兩個地方。
- `server.py` 和 `cli.py` 只是轉接層：把外部輸入轉成 domain 型別，呼叫核心模組，再把結果轉成輸出格式。這兩層不放規則。
- 只有 `Ledger` 會碰資料庫，只有 `Catalog` 會讀 `catalog/` 資料夾。

## 4. 一次 `route` 呼叫的完整路徑

以 `route(client="cowork", task_type="cowork-daily-data", ...)` 為例：

1. **HTTP 進來**。SDK 的 `BearerAuthBackend` 取出 `Authorization: Bearer <key>`，交給 `_KeyVerifier.verify_token`（`server.py:68`）。
2. **驗證 key**。`Ledger.authenticate`（`ledger.py:175`）把 key 做 SHA-256，查 `api_keys` 表。找不到或已撤銷就回 `None`，SDK 回 **401**，請求不會進到 tool。
   - 這一步用 `anyio.to_thread` 執行，不會卡住 event loop。
3. **參數驗證**。`route` 的 `client` 型別是 `Client` enum，`task_type` 是啟動時從 `catalog.task_types()` 產生的 `TaskType` enum（`server.py:98` 的 `build_app` 裡面）。不在 enum 裡的值會被 SDK 直接拒絕，不會寫入紀錄。
4. **取得使用者**。`_principal()`（`server.py:80`）從 SDK 的 context 拿出 key 對應的 `user_id`。**模型沒辦法自己指定 user_id**。
5. **查 config**。`Catalog.resolve`（`catalog.py:148`）用 `"<client>/<task_type>"` 查表。查不到就退回 `"<client>/default"`，並標記 `fallback=True`。
6. **寫紀錄**。`Ledger.record`（`ledger.py:115`）寫一筆 `usage_events`，同時存下**當下的** config 版本、百分比、token 數、美元和 provenance。rationale 和 session_id 截到 200 字。
7. **回傳**。`RouteResult` 包含 config id、版本、是否 fallback、每個 skill 的全文和是否為 draft，以及 `Config.status_template(override)`（`catalog.py:86`）算出的 `status.json` 格式。

## 5. 各模組重點

### `catalog.py`：規則都在這裡

| 符號 | 位置 | 重點 |
|---|---|---|
| `APPLICABILITY` | `catalog.py:38` | 技術 × client 適用表，**全系統只有這一份**。要讓某個技術在 Cowork 也能用，只改這裡 |
| `Estimate` | `catalog.py:55` | 每個 session 的預估節省量。`usd` 在載入時用 `pricing.yaml` 算好 |
| `Config.status_template()` | `catalog.py:86` | 「呼叫者給的格式優先」這條規則，每次回傳一份新的副本 |
| `Catalog.load()` | `catalog.py:120` | 讀取並驗證整個資料夾，**一次列出所有問題**，有任何問題就拋出 `CatalogError` |
| `_load_config()` | `catalog.py:231` | 單一 config 的驗證：skill 是否存在、是否為 draft、是否違反適用表、版本號、預估值、skill-state 的格式檔 |

設計上的重點：`Catalog` 載入後就不會再改變。後面的程式都信任它的型別，不會重複檢查。

### `ledger.py`：資料庫只有它能碰

| 符號 | 位置 | 重點 |
|---|---|---|
| `_events`、`_keys` | `ledger.py:74`、`:94` | 兩張表的 schema，用 SQLAlchemy Core 定義，所以換 Postgres 只要改連線網址 |
| `record()` | `ledger.py:115` | 把預估值**複製**進紀錄，之後校正 config 不會改到歷史數字 |
| `stats()` | `ledger.py:139` | 讀出所有紀錄，在 Python 裡分組。去重的單位是 `(user_id, session_id, config_id)` |
| `_GROUP_COLUMNS` | `ledger.py:197` | 分組方式對應到哪個欄位，新增分組方式就加在這裡 |
| `_Tally` | `ledger.py:205` | 單一分組的累計器：人數、呼叫次數、去重後的 session、依 provenance 分開的 token 和美元 |
| `issue_key()` | `ledger.py:158` | 產生 `hk_` 開頭的 256-bit 隨機 key，只存雜湊值；同一個使用者重發會取代舊的 key |

`stats(current=...)` 會用 catalog 最新的預估值重算，但不會改資料庫，所以可以放心反覆執行。

### `server.py`：MCP 轉接層

- `build_app()`（`server.py:98`）組出整個 ASGI app：設定 auth、建立 `TaskType` enum、註冊兩個 tool、設定 host 白名單，使用 stateless HTTP 加 JSON 回應。
- 檔案開頭的註解說明為什麼**不能**加 `from __future__ import annotations`：SDK 要看到真的型別物件才能產生 tool 的 input schema。
- `INSTRUCTIONS`（`server.py:30`）是給模型看的使用說明，會告訴模型何時呼叫 `route`，以及 rationale 裡不能寫什麼。

### `cli.py`：管理者指令

`check`、`serve`、`keys issue/list/revoke`、`report`。預設值可以用 `HAKKA_CATALOG`、`HAKKA_DB`、`HAKKA_PUBLIC_URL` 環境變數覆蓋。

## 6. 測試怎麼讀

- **每個 scenario 對應一個測試**，測試名稱就是 `test_<scenario 名稱的 snake_case>`。例如 spec 裡的「Revoked key rejected」對應 `tests/test_access.py` 的 `test_revoked_key_rejected`。從 spec 就能直接找到對應的測試，反過來也一樣。
- `tests/conftest.py` 有三個重要的 fixture：
  - `catalog_files`：在暫存資料夾寫出一份最小但合法的 catalog，測試再往上加 config 或 skill
  - `serve`：在隨機 port 用 uvicorn 起一個**真的** HTTP 伺服器
  - `mcp_session`：發一把 key，再用**真的** MCP client 連進去呼叫 tool
- 所以 routing 和 access 的測試走的是完整的 HTTP 和 MCP 協定，跟 Claude Code 實際連線的路徑一樣。
- 檢查 spec 和測試有沒有對齊：
  ```text
  .venv/bin/python -I .claude/skills/archive-yr/scripts/openspec_archive.py check openspec/changes/archive/2026-10-24-initial-hakka-mcp --tests tests
  ```

## 7. 常見修改要動哪裡

| 我想要… | 改哪裡 | 要不要改程式 |
|---|---|---|
| 新增一個情境（task type） | 加一個 `catalog/configs/<client>/<task-type>.yaml` | 不用。tool 的 enum 會自動更新 |
| 新增一個 skill | 加 `catalog/skills/<id>/SKILL.md`，frontmatter 寫 `technique`、`status`、`source` | 不用（technique 已經存在的話） |
| 新增一種技術（例如 programmatic tool calling） | 在 `Technique` 加一個值，在 `APPLICABILITY` 加一列（`catalog.py:26`、`:38`），再寫 skill | 要，兩行 |
| 讓某個技術開放給 Cowork | `APPLICABILITY`（`catalog.py:38`） | 要，一行 |
| 換成實測數字 | config 的 `expected_saving`，`provenance` 改成 `measured`，`version` 加 1 | 不用 |
| 換計價方式 | `catalog/pricing.yaml` | 不用 |
| 核准一個 draft skill | 把 SKILL.md 的 `status: draft` 改成 `approved` | 不用 |
| 新增統計的分組方式 | `GroupBy` 和 `_GROUP_COLUMNS`（`ledger.py:49`、`:197`） | 要 |
| 換成 Postgres | `--db postgresql://...`，並在 `requirements.txt` 加上 driver | 幾乎不用 |
| 換成 SSO | 把 `_KeyVerifier`（`server.py:68`）換成驗證 SSO token 的實作 | 要，只改這一處 |

改完 catalog 後一律先跑 `hakka-mcp check --allow-drafts`，它會一次列出所有問題。

## 8. 在本機跑起來

```text
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -e .
.venv/bin/python -m pytest -q                          # 37 passed
.venv/bin/hakka-mcp check --allow-drafts
.venv/bin/hakka-mcp keys issue me --admin --db sqlite:///local.db
.venv/bin/hakka-mcp serve --allow-drafts --db sqlite:///local.db --port 8000
claude mcp add --transport http hakka http://127.0.0.1:8000/mcp --header "Authorization: Bearer <key>"
```

## 9. 接下來的待辦事項

### P0：正式推廣前一定要做

| # | 事項 | 說明 | 負責人 |
|---|---|---|---|
| 1 | 審核 5 個 draft skill | `catalog/skills/` 的 pass-by-reference、code-graph、skill-state、model-routing、caveman。審完改成 `approved`，之後就能拿掉 `--allow-drafts` | 你 |
| 2 | 實測 Cowork 的連線方式 | 確認 Cowork 的 custom connector 能不能帶固定的 bearer key。如果一定要 OAuth，就得補一個簡單的 OAuth 入口，這會影響 `server.py` 的 auth 設定 | 你（實測），我（如果要改） |
| 3 | 決定正式的計價 | `catalog/pricing.yaml` 目前是牌價 $3 / $15 每百萬 token，換成公司的實際費率 | 你 |
| 4 | 部署 | 準備對外的 HTTPS 網址和 reverse proxy，在 proxy 上設定每把 key 的限速，再用 Docker 部署 | 你 / 基礎架構團隊 |
| 5 | `dev` → `main` 的 PR | 你自己在 GitHub 開；需要的話我可以寫 PR 說明 | 你 |

### P1：數字要可信

| # | 事項 | 說明 |
|---|---|---|
| 6 | 用 hakka-vibe 的實驗跑出實測數字 | 目前 config 的節省量全部是 `estimate` 佔位值。跑完把對應 config 改成 `measured`，`version` 加 1 |
| 7 | 把「推送 skill 本身的成本」算進去 | 例如 `cowork-daily-data` 一次回傳約 7 KB 的 skill 文字，大約 1,800 個 input token（推論，沒實測）。淨節省量要扣掉這部分 |
| 8 | 校正各情境的 skill 組合 | 例如 `cowork-poc` 刻意不放 caveman（給第一次用的人看）。上線後依照實際使用情況調整 |
| 9 | 讓 rationale 能被看到 | 目前判斷依據只存在 DB 裡。可以加進 `report`，方便檢查 Claude 的情境判斷準不準 |

### P2：擴充與強化

| # | 事項 | 說明 |
|---|---|---|
| 10 | 細化 task type | 第二版再談，目前有 6 種加 2 個 default |
| 11 | 新技術：programmatic tool calling 等 | 照第 7 節「新增一種技術」的步驟 |
| 12 | 換成 Postgres | 改連線網址；同時把 `stats()` 改成 SQL 統計（審查待處理 S9） |
| 13 | SSO 與授權 | 換掉 `_KeyVerifier` |
| 14 | 固定 Docker image digest 和套件 hash | 審查待處理 X3 |
| 15 | 決定要不要開放「全公司總數」tool | 讓所有人都看得到總節省量，有助推廣（proposal 的待確認問題） |
| 16 | 網頁儀表板 | 第一版不做 |

### 參考文件

- 規格：`openspec/specs/`
- 設計與決策：`openspec/changes/archive/2026-10-24-initial-hakka-mcp/`（proposal、architecture、status）
- 審查報告：`openspec/reviews/initial-hakka-mcp.md`
- 流程回顧：`docs/yr-coding-skills-retrospective.md`
