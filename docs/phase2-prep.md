---
id: phase2-prep
title: 達成過程② 基盤試作 — 準備タスクと実施順
status: ready
updated: 2026-07-22
---

# 達成過程② 基盤試作（2026-09〜10）— 準備タスクと実施順

本書は Phase②「基盤試作」の着手チェックリストと実施順を定める。前提はすべて
[requirements.md](requirements.md) draft-v0.5 の決定記録 #7〜#14（2026-07-16 確定・未決ゼロ）。
工数目安は §8 の **5〜8人日**。10月の期中評価で示す中間成果は「検証環境で立つ統制インフラの
骨格＋機密データ検知の初動」。

## 1. 着手時の実機確認 — 2026-07-16 前倒しで4件すべて実施済み

| #   | 確認事項                                                             | 方法                                                                                  | 影響先                                                       |
| --- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 1   | Model Armor の VPC-SC restricted service 対応                        | `gcloud access-context-manager supported-services describe modelarmor.googleapis.com` | 決定 #12（対応していれば境界に含める）                       |
| 2   | `vertexai.allowedModels` の許可モデルリスト                          | その時点の最新安定版 Gemini モデルIDを Model Garden で確認                            | 決定 #11・FR-7 パラメータ                                    |
| 3   | provider issue #24092（publisher モデルの request-response logging） | GitHub issue / provider CHANGELOG                                                     | 決定 #9（解消済みなら `gcloud` 補完を Terraform 管理に移す） |
| 4   | Model Armor の GCP機能・Terraform リソースの再確認                   | requirements.md §3.5 の情報源を再訪                                                   | §3 全体（AI安全系は更新が速い）                              |

**結果（2026-07-16 実施）**:

1. `modelarmor.googleapis.com` は **VPC-SC 対応 GA・restricted VIP 利用可**（gcloud で実機確認）
   → 決定 #12 の条件成立、境界に含める。`logging`／`monitoring` も GA を実機で再確認済み —
   **境界サービス集合（aiplatform・dlp・bigquery・logging・monitoring・modelarmor）は全件確定**。
2. Model Garden の Gemini 安定版（preview を除くテキスト生成）: `gemini-3.5-flash`／
   `gemini-2.5-pro`／`gemini-2.5-flash`／`gemini-2.5-flash-lite`／`gemini-3.1-flash-lite`。
   3.x 系 Pro は preview のみ。**`vertexai.allowedModels` の初期値候補**:
   `publishers/google/models/gemini-3.5-flash:predict` と
   `publishers/google/models/gemini-2.5-pro:predict`（FR-7 の tfvars に採用。IaC 実装時に再取得して確定）。
3. issue #24092 は **open**（最終更新 2025-12-08、label: new-resource/forward-review）
   → 決定 #9 の `gcloud`/`null_resource` 補完を維持。IaC 実装時に再確認。
4. Model Armor の機能・Terraform リソースは同日（2026-07-16）に §3.5 の情報源で確認済み。

実行時の注記: 確認に使ったクォータプロジェクト `ea-yukihidemitsuoka2` で
`accesscontextmanager.googleapis.com` と `aiplatform.googleapis.com` を有効化した
（describe/list 実行のためで、リソースは作成していない）。

## 2. リポジトリのインスタンス化（決定 #10）— 2026-07-16 前倒しで実施済み

ai-dev-foundation テンプレートは適用済み（Initial commit）。インスタンス化の実施状況:

1. **完了（2026-07-16）**: プレースホルダ置換（mission.md・CLAUDE.md §1・architecture.md
   スタック表・README・CODEOWNERS・issue config）。
2. **完了（2026-07-22）**: `terraform-gcp-template` から `infra/envs` 前提の Makefile と
   `infra/envs/dev` 雛形を取り込み、暫定的な `terraform/` 前提の配線を置き換えた。
3. **完了（2026-07-16）**: `make setup`（pre-commit フックの導入）。
4. **決定（2026-07-16・ユーザー承認）**: ブランチ保護は**保護なしで運用**する —
   private 個人リポではブランチ保護 API が GitHub Pro を要求するため（403確認）。
   GR-010 フックと PR 規律で代替し、本番化・外販の段階で再検討する。
   merge 方式は **squash のみ**に設定済み（`squash_merge_commit_title=PR_TITLE` —
   Conventional Commits による SemVer 自動化が機能する）。
5. **決定（2026-07-16・ADR-0005）**: テンプレート親を **terraform-gcp-template** に変更
   （多段継承）。`.github/inheritance/manifest.json` + `lock.json` で宣言・検証済み。
   Terraform レイヤの実ファイル反映はレビュー済みPRで完了。継承lockの最終更新は、全継承対象の
   収束確認後に実施する。

### 2.1 Terraform レイヤのmaterialize — 2026-07-22 実施済み

親 `terraform-gcp-template` との差分をレビューし、次を取り込んだ。今後の更新は
`python3 scripts/template_inheritance.py plan` の差分を確認してから反映する。

- `infra/envs/<env>/`（Terraform ルート構成の雛形）
- 親のTerraform配線Makefile（`infra/` 前提・`plan ENV=<env>`）
- `.github/governance/profiles/terraform-gcp.json`（required check名は `iac-scan`）
- 親から継承するワークフロー契約テストとnetwork module pinテスト
- 利用先固有のプロファイル所有区分を検証するgovernance test

`iac.yml` のjob名とプロファイルのrequired check名は、どちらも `iac-scan` に統一済み。
network moduleはVPC Flow Logsを有効化した `v0.5.0` に固定し、Trivy `GCP-0076` の再発を
pinテストと `iac-scan` で検出する。

## 3. 構築の実施順（依存とロックアウト回避を考慮）

VPC-SC 境界は最後に enforce する（先に張ると自分の構築作業が境界違反で止まるため。
まず dry-run で違反ログを観察してから enforce に切り替える）。

| 順  | 作業                                                                                                                             | 対応FR / モジュール（決定 #13）  |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 1   | 2プロジェクト作成・API有効化・SA分離・IAM最小権限（basic roles なし）                                                            | FR-1（workspace 直下の環境定義） |
| 2   | Org Policy subset の適用（決定 #11 の5 constraint）                                                                              | FR-1／`ai-org-policies`          |
| 3   | Model Armor テンプレート＋プロジェクトレベル floor setting（決定 #7）                                                            | FR-2／`model-armor-guard`        |
| 4   | 疑似機密データで検知の初動確認 →（**ここまでが期中評価の中間成果**）                                                             | FR-5 の一部                      |
| 5   | request-response logging（Gemini 直呼び・`gcloud` 補完＝決定 #9）＋ Data Access 監査＋ sink → BQ ＋ log-based metric ＋ アラート | FR-3／`vertex-audit-pipeline`    |
| 6   | VPC-SC 境界を dry-run で適用 → 違反ログ確認 → enforce（決定 #12）                                                                | FR-1／`vpc-sc-perimeter`         |

モジュールは terraform-gcp-modules の規約（1モジュール1ディレクトリ・
`main/variables/outputs/versions/README`・入力 validation・provider 宣言なし・SemVer タグ）で
実装し、本ワークスペースからタグ固定参照で取り込む。apply は gcp-cicd-workflows の
`tf-plan`/`tf-apply`（WIF/OIDC）。

## 4. 検証シナリオの準備（FR-5、③で通しに使う）

- **疑似機密データ**: Sensitive Data Protection の infoType に確実にヒットする値
  （偽のクレジットカード番号・マイナンバー形式・メールアドレス等。実データは使わない — GR-002 相当）。
- **疑似プロンプト集**: (a) 機密データ入り、(b) プロンプトインジェクション/ジェイルブレイク、
  (c) 悪性URLを含む応答を誘発するもの、(d) 正常系（誤検知率の確認用）、
  (e) **SDP のトークン上限 130,000 を超える長文**（`EXECUTION_SKIPPED` の挙動確認 — §9 のリスク）。
- **期待結果表**: プロンプト × フィルタ → 検知/遮断/ログ/アラートの期待値を先に定義し、
  再実行で同一結果になることを確認する（§5 非機能）。

## 5. 決定済み事項の再掲（②で迷わないための要点）

- 検証環境は **2プロジェクト**（ワークロード／ログ集約・監視、決定 #8）。単一 VPC-SC 境界に両方入れる（決定 #12）。
- Gemini は **直呼び（`generateContent`）**。logging 設定のみ `gcloud`/`null_resource` 補完（決定 #9）。
- Model Armor は **プロジェクトレベル floor setting＋テンプレート**（決定 #7）。
- 担当境界は requirements.md §2.5 を作業前提とし、**リリース段階のレビューで確認**（決定 #14）。
- gcp-foundations は読み取り専用のタグ固定参照（決定 #14）。
