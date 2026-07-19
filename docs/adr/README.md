---
id: secure-ai-controls-adr-index
title: secure-ai-controls アーキテクチャ判断記録
---

# secure-ai-controls アーキテクチャ判断記録

このディレクトリには、このリポジトリ固有のADRだけを配置する。基盤全体の判断は
[`../foundation/adr/`](../foundation/adr/) を参照する。

## 規則

- 新規ADRは `NNNN-kebab-case-title.md` の連番で作成する。
- 雛形は [`../foundation/templates/adr.md`](../foundation/templates/adr.md) をコピーする。
- 状態は `proposed → accepted | rejected` とし、accepted のADRは編集せず新しいADRで置き換える。
- すべてのADRを [`.ai/decision-log.md`](../../.ai/decision-log.md) に記録する。

## 一覧

| # | 判断 | 状態 | 日付 |
|---|------|------|------|
| [0005](0005-adopt-terraform-gcp-template-parent.md) | `terraform-gcp-template` を直接親として採用する | accepted | 2026-07-16 |
| [0006](0006-inherit-foundation-documentation-namespace.md) | 基盤文書名前空間だけを直接親から継承する | accepted | 2026-07-19 |
