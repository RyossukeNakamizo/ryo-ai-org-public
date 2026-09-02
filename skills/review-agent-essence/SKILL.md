---
name: review-agent-essence
description: |
  Claude Codeグローバルスキルの品質レビューエンジン。
  5軸評価（Trigger精度・指示明確性・出力品質・連携整合性・保守性）でSKILL.mdを定量評価し、
  改善提案を出力する。カスタムコマンド `/review-agent-essence` としても動作する。

  トリガー:
  - `/review-agent-essence [skill-name]` でClaude Codeから呼び出された時
  - `/review-agent-essence --all` で全スキル一括レビュー
  - 「スキルをレビューして」「SKILL.mdの品質チェック」「スキルの改善提案」と言われた時
  - スキル新規作成後の品質確認時

  グローバルコマンド（~/.claude/commands/review-agent-essence.md）としても配置し、
  どのプロジェクトからでも呼び出し可能にする。

  skill-creator-eval は作成・最適化ループ担当、本スキルは軽量 read-only 評価担当（--fix 時のみ書込）。
disable-model-invocation: true
user-invocable: true
---

# Review Agent Essence — スキル品質レビューエンジン

## 目的

SKILL.mdの品質を定量的に評価し、改善サイクルを回す。
スキルクリエイター（skill-creator）が「作る」ためのツールなら、
review-agent-essenceは「育てる」ためのツール。

---

## 評価5軸

| # | 軸 | 評価観点 | スコア |
|---|-----|---------|--------|
| 1 | **Trigger精度** | descriptionのトリガー条件がshould-trigger/should-not-triggerを正しく分離できるか | 1-5 |
| 2 | **指示明確性** | 本文の指示に曖昧さがないか。Claude Codeが迷わず実行できるか | 1-5 |
| 3 | **出力品質** | 期待される出力フォーマットが明確に定義されているか | 1-5 |
| 4 | **連携整合性** | 他スキルとの参照パス・連携手順が正確か | 1-5 |
| 5 | **保守性** | 500行以内か。構造が明快で更新しやすいか | 1-5 |

### スコア基準

| スコア | 意味 |
|--------|------|
| 5 | 模範的。改善不要 |
| 4 | 良好。軽微な改善余地あり |
| 3 | 標準的。明確な改善ポイントが1-2点 |
| 2 | 要改善。機能に支障が出る可能性 |
| 1 | 致命的。再設計が必要 |

---

## 実行モード

### 単体レビュー（デフォルト）
```
/review-agent-essence [skill-name]
```

指定されたスキルのSKILL.mdを読み込み、5軸評価を実施。

**出力フォーマット:**
```markdown
## Review: [skill-name]
**日時**: [YYYY-MM-DD]
**対象**: ~/.claude/skills/[skill-name]/SKILL.md
**行数**: [N]行 / 500行制限

| 軸 | スコア | コメント |
|----|--------|---------|
| Trigger精度 | X/5 | ... |
| 指示明確性 | X/5 | ... |
| 出力品質 | X/5 | ... |
| 連携整合性 | X/5 | ... |
| 保守性 | X/5 | ... |

**総合**: X.X/5.0
**判定**: ✅ 良好 / ⚠️ 改善推奨 / ❌ 要対応

### 改善提案
1. [具体的な改善案]
2. [具体的な改善案]
```

### 全スキル一括レビュー
```
/review-agent-essence --all
```

`~/.claude/skills/` 配下の全SKILL.mdを順次レビュー。
最後にサマリーテーブルを出力。

### 自動修正モード
```
/review-agent-essence [skill-name] --fix
```

レビュー結果に基づき、SKILL.mdの改善版を生成。
**HIL原則**: Before/After差分を提示し、ユーザー承認後に上書き。

### レジストリ更新モード
```
/review-agent-essence --registry
```

最新のレビュー結果でSKILL_REGISTRY.mdの月次スコア欄を更新。

---

## レビュー実行手順

### 1. SKILL.md読み込み
```bash
cat ~/.claude/skills/[skill-name]/SKILL.md
```

### 2. frontmatter検証
- `name` がディレクトリ名と一致するか
- `description` にトリガー条件が明記されているか
- `description` が過度に長くないか（目安: 20行以内）

### 3. 本文検証
- 実行フローが番号付きで記述されているか
- 出力フォーマットがコードブロックで定義されているか
- 禁止事項が明記されているか
- 他スキルへの参照パスが存在する場合、パスが正しいか

### 4. 行数チェック
```bash
wc -l ~/.claude/skills/[skill-name]/SKILL.md
```
500行超過は減点。

### 5. 総合判定
- 平均4.0以上 → ✅ 良好
- 平均3.0-3.9 → ⚠️ 改善推奨
- 平均3.0未満 → ❌ 要対応

---

## 連携スキル

- **preemptive-challenger**: レビュー結果に対する盲点検出に使用可能
- **fidp-thinking**: レビュー結果の報告をFIDP形式で構造化する際に参照
- **SKILL_REGISTRY.md**: `--registry` モードで直接更新

---

## 禁止事項

- ユーザー承認なしのSKILL.md上書き（`--fix` でも必ずBefore/After確認）
- 〈案件〉案件ファイル（`cowork-ops/`配下）のスキャン
- レビュー結果の水増し（全部5点にしない）
- 存在しないスキルへのレビュー実行
