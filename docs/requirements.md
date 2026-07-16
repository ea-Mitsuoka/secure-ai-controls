---
id: requirements-secure-ai-controls
title: 要件定義 — 安全なAI環境構築（統制インフラIaC＋監査ログ監視）
status: draft-v0.5
updated: 2026-07-16
---

# 要件定義書: 安全なAI環境構築（統制インフラIaC＋監査ログ監視）

| 項目       | 内容                                                                                                                                                                                                                                             |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ステータス | **draft-v0.5** 2026-07-16（達成過程①「要件整理・方式比較」。v0.2: 未決3確定。v0.3: 未決1・4の構成・6確定。v0.4: 未決2・4の残り・5確定。v0.5: 未決7確定〔担当境界＝事前合意なし・リリース時レビュー〕— **未決事項ゼロ**、①の判断は完了）          |
| 対象       | 社内の生成AI利用（Vertex AI / Gemini）を統制下に置くGCP環境を Terraform で構築し、\*\*検証環境（クライアントゼロ＝実顧客を持たない自社検証環境）\*\*で「機密データ検知」と「プロンプト監査ログ取得→アラート」を動作実証する                      |
| 関連文書   | [requirements/goal-statement.md](requirements/goal-statement.md)（提出済み個人目標・変更不可）／目標1アセットの設計方針を参照: secure-ga4-bq-template/docs/requirements/（別リポ・別担当、参照のみ）                                             |
| 情報の鮮度 | 本書のGCP機能・製品名・GA/Preview・Terraformリソース名は **2026-07時点**の公式ドキュメント確認に基づき、主要クレームは同時点で公式ドキュメント/Terraform Registry と照合済み（§3.5）。AI安全系プロダクトは更新が速いため、実装着手時に再確認する |

______________________________________________________________________

## 用語

本書が扱う統制要件は、提出済み目標（[requirements/goal-statement.md](requirements/goal-statement.md)）に定められた次の3つである。以後はこの名称で参照する。

1. **機密データフィルタリング** — プロンプト（入力）と生成物（出力）に含まれる機密データを検知・遮断・マスクする。
2. **プロンプト監査ログ監視** — 誰が何を投げたかを記録し、逸脱を検知して通知する。
3. **生成物の法的適合** — 出力のうち技術的に検知できる不適合（機密/PII漏洩・不適切コンテンツ・悪性URL）を検知・遮断する。

その他の用語:

- **クライアントゼロ**: 実顧客に適用する前に、自社の検証環境で先行実証すること。
- **Model Armor**: 生成AIの入出力を検査する Google Cloud のフィルタ製品（§3で詳述）。
- **floor settings（下限設定）**: 組織/フォルダ/プロジェクトの階層で最低限のフィルタを強制する Model Armor の仕組み。個別テンプレートが未設定でも下限が適用される。

______________________________________________________________________

## 1. エグゼクティブサマリ

- **何を作るか**: 3つの統制要件を Google Cloud の機能に対応づけ、**検証環境で動作する統制インフラを Terraform で構築する**。成果物は3つ — (a) 対応づけを示した設計書、(b) 統制インフラの Terraform 一式、(c) 監査ログ収集→検知ルール→アラートのパイプライン。加えて実証ログを提出する（目標B）。
- **中核となる技術対応**（§3で詳述、2026-07確認）:
  - **機密データフィルタリング**と**生成物の法的適合**の入出力検査は **Model Armor** で行う（プロンプトインジェクション/ジェイルブレイク検知、機密データ検知〔Sensitive Data Protection を統合〕、悪性URL検知、不適切コンテンツ検知）。**floor settings** により組織/フォルダ/プロジェクト階層で下限を強制でき、Terraform に対応する（`google_model_armor_template` / `google_model_armor_floorsetting`）。
  - **プロンプト監査ログ監視**は2つの仕組みを併用する — Vertex の **request-response logging**（Gemini の入出力を BigQuery へサンプリング保存）と、**Cloud Audit Logs**（Admin Activity は常時、Data Access は有効化が必要）。これらを **log-based metric**（ログを数値化）と **Cloud Monitoring アラートポリシー** に接続して検知・通知する。
  - 環境全体の境界は **VPC Service Controls** で作る（Vertex AI `aiplatform.googleapis.com` を保護対象に含め、公開インターネットからのアクセスを遮断）。これに IAM最小権限・組織ポリシー・CMEK を組み合わせる。
- **スコープの定義（重要な設計判断・§2.3）**: 提出済み目標の文言は「社内Gemini Enterprise」だが、Terraform で構築・管理できるのは **Vertex AI / GCPプロジェクト層のガードレール**（Model Armor の floor settings、VPC-SC、IAM、監査/ログ設定）であって、SaaS のエンドユーザ管理コンソールの個別設定ではない。したがって本書は Terraform の対象を **プラットフォーム/プロジェクト統制層** と定める。この層の統制は、現行の「Gemini Enterprise Agent Platform」利用にも適用される。
- **目標1からの継承**: 目標1（セキュアGA4→BQアセット）で確立した方針 — 決定論的な統制（人手の判断でなくツール/設定で強制する）、最小権限、統制のモジュール化、検証環境での実証 — を本目標でも採用する。統制要件が期中に変わっても対応できるよう、統制項目は Terraform モジュールに分割する（目標の想定課題「統制要件が期中に変わる」への対策）。

## 2. 背景・目的とスコープ

### 2.1 背景・目的

社内AIタスクフォースの一環として、生成AI利用を統制されたインフラの上で行える状態を作る。統制ルールの全社承認・本番適用は体制と裁量に依存するため、本目標の基準(B)は **検証環境で動作する統制インフラ・設計・実証成果物の完成** に置く（本番採用はA/Sの加点要素。目標の想定課題に対応）。

### 2.2 3つの統制要件（対象）

提出済み目標の3要件を、統制の対象として整理する。

| 統制要件                 | 統制の意図                                                             | 主な対応（§3）                                                       |
| ------------------------ | ---------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 機密データフィルタリング | プロンプトに機密データを含めない。含まれていても検知・遮断・マスクする | Model Armor（機密データ検知）＋ Sensitive Data Protection            |
| プロンプト監査ログ監視   | 誰が何を投げたかを記録し、逸脱を検知・通知する                         | Vertex request-response logging ＋ Cloud Audit Logs → 検知・アラート |
| 生成物の法的適合         | 出力の技術的に検知できる不適合を検知・遮断する                         | Model Armor（不適切コンテンツ・悪性URL・出力側の機密データ）         |

### 2.3 スコープの定義: 「Gemini Enterprise」を Terraform で扱える層に置き換える

提出済み目標の「社内Gemini Enterprise」を、Terraform で宣言的に構築・管理できる層に置き換えて定義する。

- **置き換えの根拠**: 生成AIの統制点のうち Terraform で扱えるのは、次の**プラットフォーム/プロジェクト層のガードレール**である。

  - Model Armor のテンプレートと floor settings
  - VPC-SC の境界
  - IAM・組織ポリシー・CMEK
  - 監査ログ設定・ログルーティング・検知ルール・アラート

  SaaS のエンドユーザ向け管理コンソールの個別設定は宣言的なIaCに向かないため、Terraform の対象にしない。

- **現行製品名との対応**: 2026-07時点、生成AIの実行基盤は Vertex AI に集約され、その上位に「Gemini Enterprise Agent Platform」が位置づけられている。上記のガードレールは Vertex/プロジェクト層に適用されるため、Gemini Enterprise Agent Platform の利用に対しても効果を持つ（Model Armor は当該プラットフォームと統合し、VPC-SC・監査ログも当該プラットフォーム向けの公式ドキュメントがある）。

- **結論**: 本書は Terraform の対象を **Vertex AI / GCPプロジェクト層の統制インフラ** と定義する。この置き換えは面談で口頭補足する（提出済み目標との整合を保つため）。

### 2.4 適用環境

- **検証環境（クライアントゼロ）** は **2プロジェクト構成**で構築する（2026-07-16決定・決定記録 #8）: ①ワークロード用プロジェクト（Vertex AI・Model Armor テンプレート/floor setting・Sensitive Data Protection）、②ログ集約・監視用プロジェクト（request-response logging の BigQuery データセット、Log sink の宛先、log-based metric、アラートポリシー）。監査ログをワークロード管理者の権限から分離し（改ざん耐性・職務分離）、本番に近い構成で実証する。本番権限・全社承認に依存しない範囲でBを完結させる。
- 疑似の機密データと疑似プロンプトを用意し、検知とアラートを通しで実演できる最小構成にする（目標1の検証環境の考え方を採用）。

### 2.5 対象外（明示的に外す）

- **技術的検知が困難な法的判断**: 著作権、グラウンディングの正当性、事実性など、自動検知が難しい領域はコミットしない。生成物の法的適合は「**技術的に検知できる範囲**（出力の機密/PII漏洩・不適切コンテンツ・悪性URL）」に限定する。
- **プロンプトを送るアプリの改修**: アプリケーション側の実装は対象外。統制はプラットフォーム/API層で適用する。
- **モデルの精度・生成品質のチューニング**: 対象外。
- **一般インフラ**: ネットワークの一般設計や非AIワークロードは技術主幹の担当。本目標は統制レイヤのみを担当する（統制の設計者が実装まで一貫して担当する＝Secure by Design）。この担当境界は本書の定義を作業前提とし、事前の分科会合意は求めず、正式運用・リリース段階のレビューで確認を受ける（2026-07-16決定・決定記録 #14）。

## 3. 統制要件とGCP機能の対応づけ（成果物(a) の主要部）

> 各行の「状態」は 2026-07 の公式ドキュメント確認に基づく。Terraformリソース名は google プロバイダで実在を確認したもののみ記載し、未確認は「要確認」と明記する。

### 3.1 機密データフィルタリング（入力側）

| 統制項目                                          | GCP機能                                                                                                         | Terraform                                                                                          | 状態                                                                                                                                  |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| プロンプト内の機密/PII の検知・遮断・マスク       | **Model Armor**（Sensitive Data Protection を統合し、プロンプトとレスポンス双方の機密情報を検知/分類/防止する） | `google_model_armor_template`（フィルタ構成）／`google_model_armor_floorsetting`（階層で下限強制） | GA。API は **v1** のみ（`modelarmor.googleapis.com`、リージョンエンドポイントあり）。画像スクリーニングのみ Preview（2026-07-16確認） |
| 機密種別のカスタム定義                            | **Sensitive Data Protection**（旧 Cloud DLP。inspection template・infoType・de-identification）                 | `google_data_loss_prevention_inspect_template` / `_deidentify_template` / `_stored_info_type`      | GA                                                                                                                                    |
| プロンプトインジェクション/ジェイルブレイクの検知 | Model Armor（信頼度の閾値 HIGH 等で構成）                                                                       | 同上（template 内のフィルタ）                                                                      | GA                                                                                                                                    |

**Model Armor の課金・クォータ・システム上限（2026-07-16 公式確認）**:

| 項目                                          | 値                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 課金（スタンドアロン／SCC Premium PAYG 共通） | 無料枠 **200万トークン/月**、超過は **$0.10/100万トークン**。SCC Premium/Enterprise サブスクリプションは 30億トークン/月込み・超過同額                                                                                                                                                                                                     |
| APIクォータ                                   | **1,200 QPM/プロジェクト**（sanitize API）。ExternalProcessor 経由は 600 QPM。引き上げは Cloud Quotas 経由                                                                                                                                                                                                                                 |
| 入力サイズ上限                                | 4 MB                                                                                                                                                                                                                                                                                                                                       |
| フィルタ別トークン上限                        | Sensitive Data Protection: **130,000**／プロンプトインジェクション・Responsible AI・CSAM: **10,000**                                                                                                                                                                                                                                       |
| 上限超過時の挙動                              | フィルタは **`EXECUTION_SKIPPED`** を返す（検知は実行されない）→ §9 のリスクとして扱い、検知ルールの対象に含める（FR-3）                                                                                                                                                                                                                   |
| 適用単位（検証環境）                          | **プロジェクトレベル floor setting ＋ テンプレート**。floor setting は組織/フォルダ/プロジェクトの3階層に設定でき、下位が上位を上書き。プロジェクトレベル floor setting が Gemini モデル・Google MCP サーバーへの**インライン強制**を担う（＝Gemini 直呼び経路にもフィルタが効く）。組織/フォルダ階層はAPI設定のみ（UIはプロジェクトのみ） |

### 3.2 プロンプト監査ログ監視

| 統制項目                              | GCP機能                                                                                                         | Terraform                                                                                                                                                                                                                                           | 状態                                                                                                                                           |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| プロンプト/レスポンスの**内容**を記録 | **Vertex request-response logging**（入出力を BigQuery へ保存。`sampling_rate`・`bigquery_destination` を指定） | **エンドポイント単位は対応**: `google_vertex_ai_endpoint` の `predict_request_response_logging_config`。Gemini foundation モデルの直呼び（`generateContent`）は `setPublisherModelConfig` API 経由で、**Terraform 未対応**（provider issue #24092） | 利用可能。経路は **Gemini 直呼びに決定**（2026-07-16・決定記録 #9）。logging 設定は Terraform 外（`gcloud`/`null_resource`）で補完し手順化する |
| 管理操作・アクセスの監査証跡          | **Cloud Audit Logs**（Admin Activity は常時、Data Access は有効化が必要。Vertex/Gemini 対応）                   | `google_project_iam_audit_config`（Data Access の有効化）                                                                                                                                                                                           | GA                                                                                                                                             |
| ログの長期保持・集約                  | **Log Router sink**（BigQuery/GCS/Pub-Sub へルーティング）                                                      | `google_logging_project_sink`（`vertex-audit-pipeline` モジュールに内包。目標1の log-router-sink の設計を参照して実装 — terraform-gcp-modules には未収載のため。2026-07-16確認）                                                                    | GA                                                                                                                                             |
| 逸脱の検知ルール                      | **log-based metric**（機密検知イベント・異常アクセス等を数値化）                                                | `google_logging_metric`                                                                                                                                                                                                                             | GA                                                                                                                                             |
| アラート通知                          | **Cloud Monitoring アラートポリシー**（メトリクス閾値→通知チャネル）                                            | `google_monitoring_alert_policy` / `google_monitoring_notification_channel`                                                                                                                                                                         | GA                                                                                                                                             |
| 脅威検知（加点要素）                  | **Security Command Center / Event Threat Detection**                                                            | SCC 有効化（要確認）                                                                                                                                                                                                                                | 環境依存                                                                                                                                       |

### 3.3 生成物の法的適合（出力側・技術的に検知できる範囲）

| 統制項目                                                    | GCP機能                                                                    | Terraform                     | 状態 |
| ----------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------- | ---- |
| 出力の不適切コンテンツ検知（性的/危険/ハラスメント/ヘイト） | Model Armor の **Responsible AI コンテンツフィルタ**（信頼度の閾値で構成） | `google_model_armor_template` | GA   |
| 出力の悪性/フィッシングURL検知                              | Model Armor の **Malicious URL detection**                                 | 同上                          | GA   |
| 出力側の PII/機密漏洩の検知・マスク                         | Model Armor（レスポンス側の機密データ検知）                                | 同上                          | GA   |

### 3.4 環境全体のガードレール（境界・権限・鍵）

| 統制項目                                                                      | GCP機能                                                                                                                                                                                                                                                                                                                                                          | Terraform                                                                               | 状態                                                           |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| AI環境の境界（データ持出防止・公開アクセス遮断）                              | **VPC Service Controls**（`aiplatform.googleapis.com` を保護対象に含めて境界内に入れ、公開アクセスを遮断）＋ Access Context Manager（アクセスレベル・ingress/egress ルール）                                                                                                                                                                                     | `google_access_context_manager_access_policy` / `_service_perimeter` / `_access_level`  | GA                                                             |
| 最小権限（AI利用者と管理者の分離）                                            | Vertex AI の事前定義ロール（`roles/aiplatform.user` 等）を SA/グループ単位で付与。basic roles は付与しない                                                                                                                                                                                                                                                       | `google_project_iam_member` / `google_project_iam_custom_role`                          | GA                                                             |
| 組織ポリシーによる制限（利用可能モデル/サービス/リージョン制限・CMEK要求 等） | **Organization Policy**。AI固有: `vertexai.allowedModels`（Model Gardenの利用可モデルをallow/deny）／`vertexai.allowedPartnerModelFeatures`（partnerモデルのweb_search等を制御）。汎用: `gcp.restrictServiceUsage`／`gcp.restrictNonCmekServices`（aiplatformへCMEK必須化）／`gcp.resourceLocations`／`iam.allowedPolicyMemberDomains`。不足はカスタム制約で補完 | `google_org_policy_policy`（予定義）／`google_org_policy_custom_constraint`（カスタム） | GA。検証環境で強制する subset は決定記録 #11（2026-07-16確定） |
| 保存データの暗号化                                                            | **CMEK**（Vertex AI 対応）                                                                                                                                                                                                                                                                                                                                       | `google_kms_crypto_key` ＋ 参照設定                                                     | GA                                                             |

### 3.5 情報源（2026-07確認・実装着手時に再確認する）

- Model Armor 概要／テンプレート／floor settings／logging（cloud.google.com/model-armor, security-command-center/docs/model_armor_floor_settings）
- Model Armor の API版数・クォータ・課金（2026-07-16確認）: REST リファレンス＝v1 のみ（docs.cloud.google.com/model-armor/reference/rest）／クォータ・上限（docs.cloud.google.com/model-armor/quotas）／料金表（cloud.google.com/security/products/model-armor#pricing）
- Model Armor のネットワーク要件（2026-07-16確認）: リージョンエンドポイントを VPC 内から使う場合は PSC エンドポイントが必要（docs.cloud.google.com/model-armor/data-residency）。restricted service 対応可否は `gcloud access-context-manager supported-services describe modelarmor.googleapis.com` で②に確認
- `vertexai.allowedModels` の値形式（2026-07-16確認）: `publishers/<publisher>/models/<model>[:predict|:deploy|:tune]`。モデルのワイルドカード不可・publisher 単位指定可（docs.cloud.google.com/vertex-ai/generative-ai/docs/control-model-access）
- Model Armor の Terraform リソース（registry.terraform.io の `google_model_armor_template` / `google_model_armor_floorsetting`）
- Vertex request-response logging（cloud.google.com/vertex-ai/generative-ai/docs/multimodal/request-response-logging）
- Vertex の監査ログ（cloud.google.com/vertex-ai/docs/general/audit-logging）
- VPC-SC と Vertex AI（cloud.google.com/vertex-ai/docs/general/vpc-service-controls, vpc-service-controls/docs/supported-products）
- Sensitive Data Protection＝旧 Cloud DLP（cloud.google.com/security/products/sensitive-data-protection、Terraformは `data_loss_prevention_*` 命名を維持）
- request-response logging の Terraform: `google_vertex_ai_endpoint`（registry.terraform.io）＋ provider issue #24092（publisherモデル対応の要望）
- Organization Policy constraint: `vertexai.allowedModels` / `vertexai.allowedPartnerModelFeatures`（cloud.google.com/vertex-ai/generative-ai/docs/control-model-access）、`gcp.restrictServiceUsage` / `gcp.restrictNonCmekServices` / `gcp.resourceLocations`（organization-policy/reference/org-policy-constraints）、Vertex カスタム制約（cloud.google.com/vertex-ai/docs/training/custom-constraints）

**照合結果（2026-07）**: Model Armor（GA・機能・floor settings・`google_model_armor_template`/`_floorsetting`）、Sensitive Data Protection（旧DLPの改称・Terraformリソース）、VPC-SC の aiplatform 対応、Cloud Audit Logs（Data Access opt-in）・監視/ログのパイプライン系リソース、`google_org_policy_policy`、Vertex CMEK と `roles/aiplatform.user` は**確認済み**。唯一の修正は request-response logging の Terraform 対応（経路依存＝上表。経路は Gemini 直呼びに決定＝決定記録 #9）。

## 4. 機能要件（FR）

### FR-1 統制インフラの基本構成（構築）

検証環境のプロジェクト構成・API有効化・IAM最小権限・VPC-SC境界を Terraform で構築する。basic roles は付与せず、用途ごとにSAを分ける（目標1 の最小権限方針を採用）。

### FR-2 入出力フィルタ（構築＝機密データフィルタリング・生成物の法的適合）

Model Armor のテンプレートを定義し、**floor settings により階層で下限を強制する**（テンプレートが未指定でも下限フィルタが適用される）。フィルタ対象は、プロンプトインジェクション/ジェイルブレイク、機密データ（Sensitive Data Protection）、不適切コンテンツ、悪性URL。信頼度の閾値は環境パラメータ（FR-7）で上書きできるようにする。

### FR-3 監査ログ→検知→アラートのパイプライン（構築＝プロンプト監査ログ監視・成果物(c)）

Vertex request-response logging（BigQuery へ保存）と Cloud Audit Logs（Data Access を有効化）を収集し、Log Router sink で集約する。log-based metric で逸脱を数値化し、Cloud Monitoring アラートポリシーで通知する。**この一連を Terraform で宣言的に構築し**、検証環境で「機密検知イベント→アラート発火」を通しで実証する。

### FR-4 統制項目のモジュール化（再利用・変更への耐性）

各統制項目（Model Armor テンプレート／VPC-SC境界／監査パイプライン／IAM・組織ポリシー）を Terraform モジュールに分割し、統制要件の変更・追加に対応できる構造にする（目標の想定課題への対策）。配置は §6。

### FR-5 検証環境と実証シナリオ（B実証）

疑似の機密データと疑似プロンプトを用意し、次を実演する。(1) 機密データを含むプロンプトの検知/遮断、(2) プロンプト監査ログの取得→逸脱検知→アラート、(3) 出力側の不適切コンテンツ/悪性URLの検知。再実行しても同じ結果になるようにする。

### FR-6 レッドチーミング（A基準）

本人がプロンプトインジェクションと機密持出を試行し、ガードレールの**検知動作を実証**して結果レポートを作成する。検知ルール/統制項目を拡充する（例: 異常なツール連鎖・決定反転の検知）。

### FR-7 環境パラメータの統一（再利用の要）

環境ごとに変わる値（プロジェクトID・境界対象サービス・機密infoType・フィルタ閾値・アラート通知先・保持期間・**許可モデルリスト**〔`vertexai.allowedModels` の値。②着手時の最新安定版 Gemini で確定〕・**リージョン**）を単一のパラメータファイルに集約し、テンプレート本体は変更しないで済むようにする（目標1 の環境パラメータ方式を採用）。

## 5. 非機能要件

- **再実行しても同じ結果になること**: 構築IaCと検証は再実行で同一結果。
- **決定論的な統制を優先**: 統制の強制（フィルタ下限・境界・検知ルール）は Terraform と GCP機能で担保する。LLM には設計文面や検知ルール草案の下書きだけをさせる。
- **移植性**: 検証環境から他環境へ、パラメータの差し替えで再利用できる。
- **統制インフラ自身の最小権限**: 統制の仕組みが過剰な権限を持たない（目標1 の最小権限原則を運用系にも適用する）。
- **コスト規律**: request-response logging はサンプリング率で制御し、監査ログの Data Access は必要な範囲に限定する（過剰な有効化を避ける）。

## 6. アーキテクチャと既存資産の統合

- **基盤**: `gcp-foundations`（ea-Mitsuoka＝本リポジトリと同アカウント。2026-07-16 に本リポジトリを ea-Mitsuoka へ移設）が、組織階層・Shared VPC・**VPC-SC・組織ポリシー・IAM・ログ/アラートの生成**を実装済み。ただし **AI固有の統制（Model Armor/Sensitive Data Protection/Vertex）は未実装**。本目標は、この基盤に AI固有の統制を追加する形をとる。基盤側は重くしない（使う側だけがタグ参照で取り込む）。
- **モジュール**: 統制モジュールは `terraform-gcp-modules`（Yukihide-Mitsuoka）に **4モジュール**を追加する（2026-07-16決定・決定記録 #13。FR-4 の統制領域と1対1）: `model-armor-guard`（テンプレート＋floor setting）／`vertex-audit-pipeline`（Data Access 監査設定＋sink＋log-based metric＋アラート）／`vpc-sc-perimeter`（access policy・perimeter・access level）／`ai-org-policies`（決定記録 #11 の constraint subset）。既存規約（1モジュール1ディレクトリで `main/variables/outputs/versions/README`・provider宣言なし・入力にvalidation・SemVerタグ固定参照）に従う。なお terraform-gcp-modules の現収載は `network`/`github-oidc` のみで `log-router-sink` は存在しない（2026-07-16確認）— sink は目標1の設計を参照し `vertex-audit-pipeline` に内包する。request-response logging の `gcloud` 補完（決定記録 #9）はモジュール化せず、本ワークスペース側の手順・スクリプトとして持つ。
- **apply/CI**: `gcp-cicd-workflows` の `tf-plan`/`tf-apply`（キーレスのWIF/OIDC認証）で構築を回す。
- **規約**: `ai-dev-foundation` のセキュリティ規約（最小権限・セキュリティ後退禁止 等。規約コード SEC-011/SEC-021/GR-030）を継承し、決定は ADR/decision-log に記録する。
- **本ワークスペース**: ai-dev-foundation テンプレートは適用済み（Initial commit・2026-07-16確認）だが未インスタンス化（プレースホルダ未置換・Makefile は no-op）。②着手時にインスタンス化する（決定記録 #10、手順は [phase2-prep.md](phase2-prep.md) §2）。

## 7. 受け入れ基準（提出済み目標の達成基準との対応）

- **B（基準）**: 検証環境で「機密データ検知」と「プロンプト監査ログ取得→アラート」が動作する。成果物は (a) 3要件とGCP機能の対応づけ設計書、(b) 統制インフラ Terraform 一式、(c) 監査ログ→検知→アラートのパイプライン、＋実証ログ。主指標は**実装した統制項目数**（3要件→GCP機能の実装数）。
- **A**: 本人のレッドチーミングで検知動作を実証し、結果レポートを作成する。検知ルール/統制項目を検証環境で拡充する（追加した検知パターン数）。
- **S（裁量外・加点）**: 分科会レビューを通過して本番の一部に適用、または全社標準構成として採用、または外販パッケージの技術核として位置づけ。スペシャライゼーション/事例資料を提出。

## 8. 工数見積もり（段階化）

> 達成過程 ①要件整理(7-8月)／②基盤試作(9-10月)／③監視検知の実装(11-12月)／④攻撃実証(1-3月) に対応する。人日はレンジで示す（精度の過信を避ける）。10月の期中評価は②の基本構成＋機密検知の最初の動作確認までを示す。

| 段階                 | 内容                                                                              | 目安（人日）     |
| -------------------- | --------------------------------------------------------------------------------- | ---------------- |
| ① 要件整理・方式比較 | 本書の精緻化・constraint選定・検証環境設計                                        | 3〜5             |
| ② 基盤試作           | プロジェクト/IAM/VPC-SC の基本構成＋Model Armorフィルタ＋機密検知の最初の動作確認 | 5〜8             |
| ③ 監視・検知の実装   | 監査ログ→metric→アラートのパイプライン、モジュール化                              | 5〜8             |
| ④ 攻撃実証・拡充     | レッドチーミング・検知ルール拡充・レビュー反映                                    | 4〜7             |
| **合計（B〜A相当）** |                                                                                   | **約17〜28人日** |

## 9. リスク・対策

- **AI製品の仕様変更が速い** → GCP機能・Terraform対応を §3.5 の基準で実装着手時に再確認する。統制項目をモジュール化して変更に耐える構造にする（FR-4）。
- **統制要件が期中に変わる** → モジュール化で吸収する（目標の想定課題）。
- **全社承認・本番権限が下りない** → 検証環境（クライアントゼロ）でBを完結させる。本番はA/Sの加点に限定する。
- **技術主幹と担当が重なる** → 統制レイヤは本人が設計から実装まで一貫して担当し（Secure by Design）、一般インフラは主幹。担当境界は本書 §2.5 の定義を作業前提とし、リリース段階のレビューで確認を受ける（決定記録 #14）。検証環境（クライアントゼロ）で完結する作業のため、事前合意なしでも他者の担当領域を侵さない。
- **request-response logging の Terraform 対応が経路で分かれる**（2026-07確認）→ 検証環境の経路は **Gemini foundation モデルの直呼び（`generateContent`）に決定**（決定記録 #9。実際の社内利用形態に近く、プロジェクトレベル floor setting のインライン強制も効くため）。直呼びの logging 設定（`setPublisherModelConfig`）は Terraform 未対応（issue #24092）のため、`gcloud`/`null_resource` で補完し手順化する。issue の解消を実装時に再確認し、対応され次第 Terraform 管理に移す。
- **Model Armor のトークン上限超過で検知がスキップされる**（2026-07-16確認）→ フィルタ別トークン上限（§3.1）を超えるプロンプト/レスポンスは `EXECUTION_SKIPPED` となり検知されない。対策: (1) 検証で長文プロンプトの挙動を確認する（FR-5）、(2) `EXECUTION_SKIPPED` を log-based metric の検知対象に含め、統制の空白を監視で補う（FR-3）。

## 10. 決定記録・未決事項

### 決定記録

| #   | 決定事項                                                            | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | 節             |
| --- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| 1   | スコープの定義                                                      | 「Gemini Enterprise」を Vertex/GCPプロジェクト層の Terraform 統制に置き換えて対象とする                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | §2.3           |
| 2   | 生成物の法的適合の範囲                                              | 技術的に検知できる範囲に限定する（著作権/グラウンディングはコミットしない）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | §2.5           |
| 3   | 入出力フィルタの実体                                                | Model Armor（テンプレート＋floor settings による階層強制）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | §3.1/3.3, FR-2 |
| 4   | プロンプト監査の実体                                                | Vertex request-response logging ＋ Cloud Audit Logs の2つを併用し、検知→アラートに接続する                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | §3.2, FR-3     |
| 5   | 目標1からの継承                                                     | 決定論的な統制・最小権限・モジュール化・検証環境での実証を採用する                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | §1, §6         |
| 6   | 基盤                                                                | gcp-foundations（VPC-SC/組織ポリシー/IAM/ログ生成）に AI固有の統制を追加する                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | §6             |
| 7   | Model Armor の版数・課金・クォータ・適用単位（2026-07-16、旧未決3） | API は v1 のみ・GA（画像スクリーニングのみ Preview）。課金は無料枠200万トークン/月＋超過$0.10/100万トークン。クォータ1,200 QPM/プロジェクト。検証環境の適用単位は**プロジェクトレベル floor setting＋テンプレート**（Gemini へのインライン強制がプロジェクトレベルで効くため。組織/フォルダ階層への昇格は本番適用時に判断）                                                                                                                                                                                                                                                                                                                                            | §3.1           |
| 8   | 検証環境の構成（2026-07-16、旧未決4の一部）                         | **2プロジェクト構成**: ワークロード用（Vertex/Model Armor/SDP）とログ集約・監視用（BQ・sink・metric・アラート）を分離。監査ログの職務分離を実証し本番構成に近づける                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | §2.4           |
| 9   | request-response logging の適用経路（2026-07-16、旧未決1の残り）    | \*\*Gemini foundation モデルの直呼び（`generateContent`）\*\*を採用。実際の社内利用形態に近く、プロジェクトレベル floor setting のインライン強制が効く。logging 設定は Terraform 未対応のため `gcloud`/`null_resource` で補完し手順化                                                                                                                                                                                                                                                                                                                                                                                                                                  | §3.2, §9       |
| 10  | リポジトリ化のタイミング（2026-07-16、旧未決6）                     | ai-dev-foundation テンプレートは適用済み（Initial commit）。インスタンス化（プレースホルダ置換・Makefile 実装・pre-commit 有効化）は当初②着手時の予定を**前倒しし 2026-07-16 に実施済み**。governance の branch-protection 適用のみ GitHub の課金制約で保留（[phase2-prep.md](phase2-prep.md) §2）                                                                                                                                                                                                                                                                                                                                                                     | §6             |
| 11  | 検証環境で強制する Org Policy subset（2026-07-16、旧未決2の残り）   | 採用5件: `vertexai.allowedModels`（allow は検証で使う Google 公開 Gemini モデルのみ個別指定。値形式 `publishers/<publisher>/models/<model>[:predict\|:deploy\|:tune]`、モデルのワイルドカード不可・publisher 単位指定は可。具体リストは FR-7 パラメータで②に確定）／`gcp.restrictServiceUsage`（検証に必要な API のみ許可）／`gcp.restrictNonCmekServices`（aiplatform へ CMEK 必須化）／`gcp.resourceLocations`（原則 asia-northeast1。モデル提供リージョンとの整合は FR-7 パラメータで調整）／`iam.allowedPolicyMemberDomains`（自社ドメインのみ）。**不採用**: `vertexai.allowedPartnerModelFeatures`（allowedModels で Google モデルのみに絞るため対象が生じない） | §3.4           |
| 12  | VPC-SC 境界の方針（2026-07-16、旧未決4の残り）                      | **単一境界に2プロジェクト（決定#8）をともに含める**。restricted services: `aiplatform`・`dlp`・`bigquery`（VPC-SC 対応GAを2026-07-16確認）＋`logging`・`monitoring`（対応GAの認識。②で再確認）。`modelarmor` は restricted service 対応可否が未確認（リージョンエンドポイントは PSC 経由の要件あり）— ②着手時に `gcloud access-context-manager supported-services describe modelarmor.googleapis.com` で確認し、対応していれば境界に含める                                                                                                                                                                                                                             | §3.4           |
| 13  | 統制モジュールの粒度と配置（2026-07-16、旧未決5）                   | terraform-gcp-modules に4モジュール（FR-4 の統制領域と1対1）: `model-armor-guard`／`vertex-audit-pipeline`／`vpc-sc-perimeter`／`ai-org-policies`。log-router-sink は同リポに存在しないため sink は `vertex-audit-pipeline` に内包。logging の `gcloud` 補完はモジュール化しない。命名・分割の微調整は②のモジュールリポ規約レビューで許容                                                                                                                                                                                                                                                                                                                              | §6             |
| 14  | 担当境界とレビュー時期（2026-07-16、旧未決7）                       | 分科会との**事前合意は行わない**（合意の場が得られないため）。担当境界は §2.5 の定義（統制レイヤ＝本人が設計〜実装、一般インフラ＝技術主幹）を作業前提とし、**正式運用・リリース段階のレビューで確認を受ける**。検証環境で完結するため事前合意なしでも他者領域を侵さない。gcp-foundations への依存は読み取り専用（タグ固定参照）に留め、基盤側の変更が必要になった時点でオーナーと個別調整する                                                                                                                                                                                                                                                                         | §2.5, §9       |

### 未決事項（実装フェーズで精査）

1. **確定済み（2026-07-16）**: request-response logging の適用経路 → Gemini 直呼びに決定。決定記録 #9 と §3.2・§9 に記載。
2. **確定済み（2026-07-16）**: 強制する constraint subset → 決定記録 #11 に記載（候補6件から5件採用・1件不採用。候補の実在確認と制約〔Model Registry 登録モデル不適用・allow+deny 合計500値・restrictServiceUsage の適用対象制約〕は 2026-07 確認済み）。許可モデルの具体リストのみ FR-7 パラメータとして②で確定。
3. **確定済み（2026-07-16）**: Model Armor の API版数・課金・クォータ・適用単位 → 決定記録 #7 と §3.1 に記載。
4. **確定済み（2026-07-16）**: プロジェクト構成は2プロジェクト（決定記録 #8）、VPC-SC 境界方針は単一境界＋restricted service 集合（決定記録 #12。modelarmor の対応可否のみ②で実機確認）。
5. **確定済み（2026-07-16）**: モジュール粒度と配置 → 4モジュール。決定記録 #13 と §6 に記載。
6. **確定済み（2026-07-16）**: リポジトリ化のタイミング → ②着手時（2026-09予定）に scaffold。決定記録 #10 に記載。
7. **確定済み（2026-07-16）**: 担当境界とレビュー時期 → 事前合意なし・リリース時レビュー。決定記録 #14 に記載。

**未決事項はすべて確定した（2026-07-16）。②基盤試作で実機確認する事項**: modelarmor の VPC-SC 対応（決定 #12）、`vertexai.allowedModels` の許可モデルリスト（決定 #11・FR-7）、provider issue #24092 の解消状況（決定 #9）。
