---
id: secure-ai-controls-docs-index
title: secure-ai-controls ドキュメント索引
updated: 2026-07-22
---

# secure-ai-controls ドキュメント索引

このディレクトリは、基盤から継承する文書と、このリポジトリ固有の日本語文書の
配置を案内する。

## 配置規則

| 所有者 | 配置先 | 言語 | 更新方法 |
|--------|--------|------|----------|
| 基盤リポジトリ | [`foundation/`](foundation/) | 基盤の規約に従う | 直接編集せず、親テンプレートから同期する |
| secure-ai-controls | `docs/` 直下の用途別パス | 原則として日本語 | このリポジトリのPRで更新する |

詳細な配置判断は、基盤の
[`project-documentation.md`](foundation/guides/project-documentation.md) を参照する。

## プロジェクト固有文書

| 文書 | 用途 |
|------|------|
| [`requirements.md`](requirements.md) | プロジェクト全体の要件定義 |
| [`requirements/`](requirements/) | 要件の根拠資料と個別要件 |
| [`phase2-prep.md`](phase2-prep.md) | 基盤試作フェーズの準備と実施順 |
| [`adr/`](adr/) | このリポジトリ固有のアーキテクチャ判断記録 |
| [`glossary.md`](glossary.md) | プロジェクト固有用語の参照先 |

新しいプロジェクト固有文書は、必要になった時点で用途別パスへ作成する。雛形は
[`foundation/templates/`](foundation/templates/) からコピーし、内容を日本語で記述する。
