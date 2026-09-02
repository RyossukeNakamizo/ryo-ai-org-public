---
name: memory-discipline
description: |
  userMemories (memory_user_edits tool) への entry 追加・削除・編集・整理時の判定規律スキル。
  Memory layer (L1) と claude-mem (L2) と context-handoff (L3) の三層情報アーキテクチャを前提に、
  L1 に L3 的情報 (特定プロジェクト snapshot、数値詳細、残作業、運用現況) が侵食することを構造的に予防する。
  「Memory に何を残すべきか」を 3問テスト + 4禁止カテゴリ + 例外条項で literal に判定し、
  曖昧判断・推定確定・「とりあえず焼き込む」運用を排除する。

  トリガー:
  - memory_user_edits tool を発火させようとする時 (add/remove/replace 全て対象)
  - 「Memoryに追加して」「メモリに焼き込んで」「忘れないように記憶して」と ユーザー が要求した時
  - 既存 userMemories の整理・reorg・audit を行う時
  - userMemories の容量上限 (30 entries / 100,000 字) に接近した時
  - chat Claude が「これは Memory に入れる価値がある」と推定発火しようとした瞬間
    (自動発火は禁止、本 skill で適格性判定を通過させる)

  発火後、本 skill の判定基準を通過させてから初めて memory_user_edits を発火させる。
  判定 NG の場合は L2 (claude-mem) または L3 (context-handoff YAML/MD) への振り分けを提案する。
---

# memory-discipline

## 目的

userMemories は「恒久的に ユーザー の人格・選好・規律を保存する」場所であり、
「特定プロジェクトの状態を記録する」場所ではない。本スキルは両者の混同を構造的に排除する。

## 三層情報アーキテクチャ

| 層 | 機構 | 永続性 | 適性 |
|---|---|---|---|
| L1 | userMemories (memory_user_edits) | 明示削除まで恒久 | 人格・選好・恒久規律 |
| L2 | claude-mem (semantic index) | 自動圧縮で保持、SessionStart自動読込 | 過去 session の「読み返し」 |
| L3 | context-handoff (YAML/MD) | ファイル永続、明示参照 | 「即実行」可能な作業引き継ぎ |

**判定原則**: 情報を L1/L2/L3 のどこに置くべきかを明示判定してから操作する。

## 判定基準: 3問テスト

新規 entry 追加時、または既存 entry の retrofit 判定時、以下3問で適格性を測る。

1. **半年後も True か？**
   - プロジェクト終了、技術陳腐化、状態変化で False になるなら不適格。
   - 例: 「PoC-1 着手フェーズ」「残作業 X が pending」は半年後 False。

2. **次の会話で chat Claude が「知っていないと不自然」か？**
   - 自己紹介・選好・恒久規律は Yes。
   - 特定 session の決定経緯・数値詳細は No (それは L3 の領域)。

3. **verbatim 数値・固有名詞精度が必須か？**
   - 必須なら **不適格** (raw data 側に置くべき)。
   - 「median 15.10s / max 22.29s」のような精密値は Memory に焼くと劣化リスク。

### 判定閾値

**Yes 2つ以上で適格、1つ以下で不適格。**

特に問3は「Yes なら不適格」の逆転問なので注意 (適格条件は「Yes ≥ 2」だが問3だけは No が望ましい)。

明示する: 適格 = (問1 Yes) + (問2 Yes) + (問3 No) のうち 2つ以上満たす。

## 禁止カテゴリ (literal 列挙)

以下4カテゴリは Memory 焼き込み禁止。発見次第 reorg 対象。

### (a) 特定プロジェクト/時点 snapshot
- 「YYYY-MM-DD 時点で X フェーズに着手」
- 「現セッションで論点 A/B/C 提示済」
- → L3 (context-handoff) へ。

### (b) 数値詳細
- 性能測定値 (latency, accuracy, token count)
- ファイルサイズ、行数、進捗率
- → raw data ディレクトリ + L3 参照リンク。

### (c) 残作業・次ステップ
- 「pending: X, Y, Z」
- 「次の検証ポイント」
- → L3 (context-handoff の next_actions セクション) へ。

### (d) スキル/システム運用の現況スナップショット
- 「N skills 配置済」「構成= A + B + C」
- → 陳腐化早い。SKILL_REGISTRY.md に書け。

## 例外条項

snapshot 系情報から **恒久ノウハウを抽出した場合**、抽出版のみ Memory 適格。
ただし **元の snapshot は削除**、二重保持禁止。

### 抽出パターン例

| 元 snapshot (NG) | 抽出版 (OK) |
|---|---|
| 「Pre-PoC手法A実測: 15.10s/22.29s、9/9達成、DI回転自動補正観察」 | 「DI Layout highRes は回転自動補正するため、前段正立判定ステップは不要」 |
| 「2026-04-26 タスクD で検証2軸原則確立、forward-compat test 採用」 | 「Skill検証は構造軸 + 意味軸の2軸で行う (構造のみでは意味整合性を捕捉不可)」 |
| 「nohup起動時に export $(grep -v '^#' .env \| xargs) を実行しないと KeyError」 | (これは既に抽出済の典型例: 恒久運用ノウハウ) |

抽出版の特徴:
- 日付なし、固有プロジェクト名なし、数値なし
- 「次に同じ状況に遭遇した時に再利用可能な knowledge」

## 既存 entry 判定例 (2026-05-24 時点 16 entries)

参考として、過去 entry を本スキルで判定した結果:

### Tier 1 (即削除候補: snapshot 性質)
- #13 〈案件〉PoC-1着手フェーズ 2026-04-27 → L3 へ
- #15 Pre-PoC手法A性能実測 2026-05-08 → 抽出版 (DI 回転自動補正) のみ残し、数値詳細削除
- #12 claude-mem 初稼働実測 2026-04-26 23:04 → L3 へ
- #16 tutor skill v1.0 追加 残作業含む → L3 + SKILL_REGISTRY へ

### Tier 2 (統合・圧縮候補)
- #7, #8 → 「グローバルスキル体制: ~/.claude/skills/ + ~/claude-global-skills/ で local Git 管理」1 entry に統合
- #9, #11 → 「引き継ぎ二層: claude-mem(自動) + context-handoff(手動)、検証は構造+意味の2軸」1 entry
- #10 → 削除 (commit message 規律は git log で十分)

### Tier 3 (保持)
- #1 年収、#2 SaaS構想、#3 ログ特定ルール、#4 nohup問題、#5 memory運用方針、#6 wise-man存在、#14 handoff path

整理後想定: 16 → 7〜8 entries、5,400字 → 2,500字。

## reorg 手順

既存 Memory の audit + reorg を行う場合:

### Step 1: snapshot 取得
```bash
mkdir -p ~/.claude/memory-backups/
# memory_user_edits(command='view') の出力を MD ファイルとして保存
# ファイル名: YYYY-MM-DD_memory_snapshot_before_reorg.md
```

### Step 2: 全 entry に対し本スキルの判定を適用
- Tier 1 (削除): 該当 entry を list 化
- Tier 2 (統合): 統合後の entry 案を起草
- Tier 3 (保持): 変更なし

### Step 3: ユーザー 承認取得
- Tier 1/2/3 判定結果を提示
- 削除・統合の妥当性を ユーザー に明示確認 (推定確定禁止)

### Step 4: memory_user_edits で実行
**実行順序の注意**:
1. **add を先に**: 統合後の新 entry を先に add (line_number 確定)
2. **remove を後に、降順で**: 削除対象を line_number 降順で remove
   - 理由: 昇順で remove すると line_number がずれる
3. 各操作後に view で確認 (batch 処理時は特に)

### Step 5: post-reorg snapshot
- 同じく MD で `~/.claude/memory-backups/YYYY-MM-DD_memory_snapshot_after_reorg.md` 保存
- before/after を git commit で履歴化 (`~/.claude/memory-backups/` を local Git 管理)

## 新規 entry 追加時のチェックリスト

memory_user_edits(command='add') を発火させる前に:

- [ ] 3問テスト適用、Yes ≥ 2 か?
- [ ] 4禁止カテゴリ (a)(b)(c)(d) に該当しないか?
- [ ] 該当する場合、抽出版に変換可能か?
- [ ] 既存 entry と重複・矛盾しないか? (view で確認)
- [ ] 500字制限内、1件1論点に圧縮されているか?
- [ ] L2/L3 に置く方が適切ではないか?

全てパスした場合のみ add を実行。

## 発火しない場合

以下は本スキル発火不要:
- 一時的なファイル参照、計算、検索などの通常タスク
- userMemories を「読む」だけの操作 (view command 単独)
- L2/L3 操作 (claude-mem, context-handoff) のみで完結する場合

## 関連 skill

- `context-handoff` / `context-handoff-md`: L3 への振り分け時に発火
- `preemptive-challenger`: 判定迷い時の盲点列挙
- `tool-system-affinity-discipline`: Memory tool と Mac local file の系統混同予防
