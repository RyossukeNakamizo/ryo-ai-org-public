---
name: "feedback-loop"
description: "Slack #project-feedback（Claude Code Loop サンドボックス）の巡回トリアージを1語で発火する。トリガー: ユーザー が「/feedback-loop」「巡回して」「フィードバック巡回」と明示した時のみ。自動発火禁止。"
---

# feedback-loop — Slack フィードバック巡回スキル

ユーザー が明示的に発火した時のみ実行する（自動発火・暗黙発火禁止）。

## 前提
- プロジェクトフォルダ: `~/Documents/Claude-Workspace/claude-code-loop/`
  （未接続ならフォルダアクセスを要求してから進む）
- Slack コネクタが claudecodeloop.slack.com に接続されていること
  （`#project-feedback` が見えない場合は接続先相違として停止・報告）

## 実行
プロジェクトフォルダ直下の `loop_prompt.md` を読み、その手順（a→e）に**忠実に**従う。
要点（loop_prompt.md が正本。矛盾時は loop_prompt.md が優先）:
1. `state/last_run.txt` の T_last 以降の新着を Slack read_channel 1回で取得
2. **`message_ts <= T_last` を数値比較で除外**（oldest は inclusive）
3. フィルタ後 0件 → last_run.txt を更新し「新着なし・即終了」と1行報告して終了
4. 新着あり → 3分類トリアージ（対応可能/軽微・即断/情報不足）→ `tasks.md` 末尾追記、
   情報不足には質問下書きを `drafts/<ts>.md` へ
5. 停止条件: 1報告5試行・全体20ターン。Slack への送信は下書きまで（ユーザー 承認後のみ送信）
6. 報告は4行以内: 新着件数・分類内訳・下書き所在・停止条件到達の有無

## 禁止
- 報告されたバグの実修正・commit・Slack 送信・スコープ外チャンネルの読み取り
- 巡回頻度の変更・スケジュール化の無断実行（提案は可、実行は ユーザー Go 後）

