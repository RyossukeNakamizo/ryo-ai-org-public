---
name: notion-io-discipline
description: |
  Chat Claude が Notion connector 経由で書き込み系操作（create / update）を行う際の、
  保存先判定・命名規約・更新規律を強制する規律スキル。読み取り操作は対象外。

  トリガー（該当時は必ず適用）：
  - Notion への create / update / move 操作を実行する直前（自動適用）。
  - ユーザー が「/notion」コマンドを明示的に投入した時（読み取りを含む IA 確認にも使用可）。

  発火制限：
  - 読み取りのみ（search / fetch）の操作では自動発火しない。
  - Worker（Claude Code）側は Notion MCP 未構成のため対象外。構成された時点で
    本スキルの複製要否を再判定する（tool-system-affinity-discipline §3 参照）。
---

# Notion I/O 規律（保存先・命名・更新の統制）

## §1 Single Source of Truth
- 正本は Notion 上の「📇 Notion IAマップ（ドキュメント索引）」
  （page_id: `3953ef6b-e648-81d1-8997-cb7f70f79718`）。
- fetch 失敗時のフォールバック：タイトル「Notion IAマップ」で notion-search し、
  一意ヒットを確認してから使用する。ヒットしない場合は操作を中断し ユーザー に報告する。
- 本スキルは手順のみを持ち、カテゴリ構造・運用ルールの実体は IA マップ側に置く
  （二重定義禁止）。

## §2 書き込み前チェックリスト（create / update 共通）
1. IA マップを fetch し、対象カテゴリ（A〜E）と既存ページの有無を確認する。
2. update-vs-create 判定：既存ページが索引に存在する → update を第一候補とする。
   メジャー改訂（vX→vX+1）のみ create + 索引更新。
3. update の場合：**必ず現状ページを fetch してから**差分を設計する。
   既存構造（見出し・DB スキーマ・プロパティ）を破壊する変更は提案止まりとし、
   ユーザー の承認を得てから実行する。
4. create の場合：命名規約（§3）を通し、親ページ／配置先を明示して実行する。
   配置先が不明なら ユーザー に確認する（推測で workspace 直下に散置しない）。

## §3 命名・バージョン規約
- 恒久資産（カテゴリ A）：`名称 vX.Y` 形式。改訂履歴をページ末尾に 1 行追記する。
- 案件ドキュメント（カテゴリ B）：`案件名 — 主題` 形式。
- Handoff：context-handoff スキルの命名規約に従う（本スキルでは再定義しない）。

## §4 破壊的操作ガード
- ページ・DB の削除、アーカイブ、大規模構造変更は Claude 側から実行しない。
  提案としてページ URL と影響範囲を提示するに留める。
- DB スキーマ変更（update-data-source）は before スキーマを応答内に記録してから行う。

## §5 索引更新義務
- カテゴリ A / B に該当する新規ページ作成時、同一ターン内で IA マップへ 1 行追記する。
- クリップ・デイリー・一時メモは索引更新の対象外（カテゴリ E 準拠）。

## §6 ポインタ
- 系統判定：`tool-system-affinity-discipline`（Notion connector = 系統 A）
- 判断構造：`fidp-thinking` ／ Handoff 命名：`context-handoff`
