# ADR-0006: 基盤文書名前空間だけを直接親から継承する

| Field | Value |
|-------|-------|
| Status | accepted |
| Date | 2026-07-19 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | ADR-0005 の `docs/` 全体を保護する部分を置き換える |

## Context

直接親 `terraform-gcp-template` は、再利用可能な基盤文書を
`docs/foundation/` に配置する規約へ移行済みである。一方、このリポジトリの
継承 manifest は `docs/` 全体を子所有として保護しているため、ローカル優先の
継承計画では基盤文書を取り込めない。

暫定輸送である Template Sync には `docs/foundation/` の例外があるが、
`actions-template-sync@v2` が必要とする Git pathspec と manifest の所有境界が
一致していない。また、子所有の manifest、lock、同期 workflow を ignore
ファイルが網羅しておらず、同期成功時に直接親の設定で上書きされる可能性がある。

## Options considered

### Option 1: `docs/` 全体を子所有のまま維持する

- **Pros:** 現在の manifest を変更しない。
- **Cons:** 基盤文書が伝播せず、各利用先で再配置と手動コピーが必要になる。

### Option 2: Template Sync の例外だけを使用する

- **Pros:** 変更範囲が ignore ファイルだけに限定される。
- **Cons:** manifest と輸送処理が異なる所有境界を持ち、ローカル優先の計画結果を
  正として扱えない。

### Option 3: manifest と暫定輸送の所有境界を一致させる（採用）

- **Pros:** `docs/foundation/` だけが直接親から伝播し、利用先が作成する日本語文書は
  `docs/` 直下の用途別パスで保護される。継承計画と暫定輸送を同じ基準でレビューできる。
- **Cons:** 既存の基盤由来プレースホルダーをプロジェクト文書の場所から除去する移行が必要。

## Decision

Option 3 を採用する。`.github/inheritance/manifest.json` は
`docs/foundation/` を `inherited_paths` に含め、プロジェクト固有文書だけを
`protected_paths` に列挙しなければならない。

`.templatesyncignore` は `docs/**` を除外した後、Git pathspec の
`:!docs/foundation/` と `:!docs/foundation/**` だけを再包含しなければならない。
manifest、lock、同期 workflow など他の子所有パスも同ファイルで除外する。
Makefile、Terraform profile、継承契約テストなど manifest 上の継承パスは
暫定輸送から除外してはならない。

親コミットは第一親順にレビューし、プロジェクト固有ファイルを維持したまま
継承 lock をレビュー済みコミットへ進める。

## Consequences

**Positive:**

- 基盤文書は `docs/foundation/`、利用先文書は `docs/` の用途別パスという境界が
  多段継承でも維持される。
- manifest と Template Sync の差異をテストで検出できる。

**Negative:**

- 既存の基盤由来プレースホルダーは一度だけ整理する必要がある。
- Template Sync は workflow を変更するPRを GitHub App token で push できないため、
  当面は人または workflow 権限を持つローカル認証で反映する必要がある。

**Follow-ups:**

- Issue #7 で所有境界の回帰テスト、manifest、ignore ファイルを更新する。
- 親 `terraform-gcp-template` の未反映コミットを取り込み、継承 lock を更新する。
- 基盤由来プレースホルダーをプロジェクト文書の場所から除去する。
