# secure-ai-controls (目標3: 安全なAI環境構築 — 作業ワークスペース)

社内Gemini/Vertex 利用を統制下に置くGCP環境の**統制インフラ IaC ＋ 監査ログ監視基盤**を、検証環境（クライアントゼロ＝実顧客を持たない自社検証環境）で構築・実証するための、個人目標3の作業用ディレクトリ。

- 対象期間: 2026-04 〜 2027-03 / Phase① 要件整理・方式比較 = 7〜8月（着手時期）
- 現状: **テンプレート適用済み・インスタンス化済み**（2026-07-16 前倒し）。**テンプレート親を terraform-gcp-template に変更**（ADR-0005・多段継承 `ai-dev-foundation → terraform-gcp-template → 本リポ`。`.github/inheritance/manifest.json` で宣言、materialization はツール完成待ち）。IaC コードはまだ無い（②で作成）。

## 中身

| パス                                                                       | 内容                                                                                                                         |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| [docs/requirements.md](docs/requirements.md)                               | **要件定義書 draft-v0.3**（2026-07-16）。3つの統制要件とGCP機能の対応づけ・機能要件FR・受け入れ基準・工数・決定記録/未決事項 |
| [docs/requirements/goal-statement.md](docs/requirements/goal-statement.md) | 提出済みの個人目標（変更不可・原文のまま）。3つの統制要件・達成基準・達成過程の正本                                          |
| [docs/phase2-prep.md](docs/phase2-prep.md)                                 | **②基盤試作の準備**（2026-07-16）。着手時の実機確認・リポ化手順・構築の実施順・検証シナリオ準備                              |

## 次の一歩

要件定義書 draft-v0.1 は作成済み（Phase① 初稿、GCP機能は 2026-07 の公式ドキュメント確認に基づく）。敵対的ファクトチェック実施済み（主要クレームは公式ソースと整合、修正1点＝request-response logging の TF対応を精緻化）。2026-07-16 に未決事項 #1〜#7 を**すべて確定**し **draft-v0.5** に更新（決定記録 #7〜#14）: Model Armor＝API v1・無料枠200万トークン/月・プロジェクトレベル floor setting、検証環境＝2プロジェクト構成、logging 経路＝Gemini 直呼び＋`gcloud` 補完、Org Policy subset＝5 constraint 採用、VPC-SC＝単一境界、モジュール＝4分割（model-armor-guard / vertex-audit-pipeline / vpc-sc-perimeter / ai-org-policies）、リポ化＝②着手時 scaffold、担当境界＝事前の分科会合意なし・リリース時レビュー。

- Phase①の判断は完了。②の実機確認4件も 2026-07-16 に前倒しで完了（結果は [docs/phase2-prep.md](docs/phase2-prep.md) §1 — modelarmor 含む VPC-SC 全6サービス GA 確認、許可モデル初期値、issue #24092 は open）。次は②基盤試作の IaC 実装（9〜10月、前倒し可）。
- ②基盤試作の着手時に、適用済みテンプレートをインスタンス化する（プレースホルダ置換・Makefile 実装・pre-commit/governance 有効化 — [docs/phase2-prep.md](docs/phase2-prep.md) §2）。

## 関連リポ

- 本リポジトリは 2026-07-16 に `Yukihide-Mitsuoka/secure-ai-controls`（public）から `ea-Mitsuoka/secure-ai-controls`（private）へ移設（履歴保持）。
- `gcp-foundations`（ea-Mitsuoka＝本リポジトリと同アカウント）: 組織階層・Shared VPC・**VPC-SC・組織ポリシー・IAM・ログ/アラートの生成**を実装済み。AI固有の統制（Vertex/Model Armor/Sensitive Data Protection）は未実装。本目標の基盤の候補。
- `terraform-gcp-modules`（Yukihide-Mitsuoka・public）: 統制モジュールの追加先（決定記録 #13 の4モジュール）。public のためアカウントをまたいでもタグ固定の git source で参照可能。
- `secure-ga4-bq-template`: 目標1（別担当・本ディレクトリからは触れない）。設計方針（決定論的な統制＋最小権限＋モジュール化＋検証環境での実証）を採用する。
