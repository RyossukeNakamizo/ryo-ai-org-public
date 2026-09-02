---
name: save-instruction
description: |
  chat Claude（Judge）が起草した Worker 指示書全文を、クリップボードから
  Downloads 受け渡し規約（claude_YYYY-MM-DD_<topic>_worker_instruction_vN.md）で保存し、
  SHA-256 全体・先頭16桁・Worker への着手指示文を表示する 1 コマンド化スキル。
  従来の「Downloads へ手動配置 → shasum 手打ち → 先頭16桁を目視転記」を置き換える。

  トリガー:
  - `/save-instruction [topic]` が明示投入された時のみ発火する。自動発火・暗黙発火は禁止。
  - topic は保存ファイル名のスラグ（例: uc2-recount）。未指定なら "instruction"。
---

# save-instruction

chat 側でコピーした指示書全文を、1 コマンドで正しい受け渡し形式に落とす。

## 手順

1. `bash ~/.claude/scripts/save-instruction.sh <topic>` を実行する
   - topic は `/save-instruction uc2-recount` のように引数から取る。未指定なら省略（既定 "instruction"）
   - スクリプトはクリップボード（pbpaste）を読む。パイプ・ファイル指定でも動く
2. スクリプトの出力（保存パス・委任ID・SHA-256・先頭16桁・着手指示文）を**そのまま**ユーザーへ報告する
   - 「── Worker への着手指示にそのまま貼れる文 ──」以下の1文は必ず含める（ユーザー はこれを Worker セッションに貼るだけでよい）
3. 出力に委任ID（W-MMDD-NN）が含まれない場合は「指示書に委任IDが見当たりません。chat 側の起草を確認してください」と注意を添える（保存自体は有効）

## エラー時

- 「入力が空です」→ chat 側で指示書全文をコピーし直してから再実行するよう案内する
- それ以外の失敗は原文のまま報告し、勝手にリトライ・修復しない

## 前提（chat 側の出し方）

chat Claude（Judge）には「指示書は W-MMDD-NN 形式の Markdown **1ブロック**で出力して」と依頼しておく
（章立て: タイトル行 / 発行・Judge・承認 / 種別 / 背景 / 目的 / 範囲 / 手順 / 制約 / 報告様式）。
SHA-256 は本スキルが保存後に計算するため、chat 側に書かせない。

## 連携

- Worker 側の照合: `~/.claude/tools/sha256-check.html`（ドロップ照合）または `shasum -a 256`
- 手元でゼロから書く場合の代替: `~/.claude/tools/worker-instruction-gen.html`
