---
name: verbatim-quote-diff-interpretation-discipline
description: |
  ユーザー が前 turn の chat Claude 応答を verbatim quote 形式で再掲しつつ一部に差分 (diff) を含めて返してきた局面で、その diff signal が「承認 + 部分修正」「再検討要求」「全項目再確認要求」のいずれを意味するかを構造的に判定する規律スキル。

  トリガー（以下 3 条件のうち 2 つ以上を満たす場合に必ず発火）：
  ① ユーザー 発話内に表形式・箇条書き形式で前 turn 内容が再掲されている
  ② 再掲内容と前 turn chat Claude 応答との間に literal 差分が 1 箇所以上存在する
  ③ ユーザー 側からの明示的「承認」「修正」「却下」signal が同時に存在しない

  発火制限：
  - ユーザー verbatim quote を受領した瞬間、応答前に必ず本スキルの diff 類型判定マトリクスを通過させる。「verbatim quote = 全項目承認」との機械的解釈は禁止。
---

# Verbatim Quote Diff Interpretation Discipline

## 1. このスキルの目的

ユーザー が前 turn chat Claude 応答内容を verbatim quote 形式で再掲しつつ一部に差分を含めて返してきた局面で、その diff signal を**構造的に解釈する単一の真実情報源 (single source of truth)** を提供する。

本スキルは Memory 内 `verbatim-wording-discipline` (Type 11) の子規律として位置づけられる。Type 11 の core 違反は「前 turn 内容を literal に温存して ユーザー 修正指示を無視する処理」であるが、その下位類型として「verbatim quote の diff 部分の解釈誤り」が複数回観察されているため、解釈ルールを明示化する。

## 2. 適用範囲 (When to trigger)

以下の条件のうち 2 つ以上を満たす場合、応答前に**必ず**本スキル §3 を通過させること。

| 条件 ID | 条件内容 |
|---|---|
| C1 | ユーザー 発話内に表形式・箇条書き形式で前 turn 内容が再掲されている |
| C2 | 再掲内容と前 turn chat Claude 応答との間に literal 差分が 1 箇所以上存在する |
| C3 | ユーザー 側からの明示的 signal (「OK」「承認」「確定」「却下」「修正してください」等) が同時に存在しない |

**実装ヒューリスティック**: ユーザー 発話が長文かつ前 turn 内容と highly similar である場合、自動的に C1 を満たすと判定すること。前 turn 応答との literal 比較は応答生成前に必ず実施すること。

## 3. diff 類型判定マトリクス

### 3.1 diff の物理的形態

| 類型 ID | 物理的特徴 | 該当例 |
|---|---|---|
| D1: 単純数値 diff | 1 項目内の数値・日時のみが変化 | 「5/13 18:00 JST → 5/12 18:00 JST」 |
| D2: 単純文字列 diff | 1 項目内の文字列が変化 (固有名詞・状態語等) | 「田中さん → 山田さん」、「standby → halt」 |
| D3: 順序入れ替え diff | 項目内容は同一だが順序が変化 | 「α → β → γ」が「γ → α → β」 |
| D4: 項目追加 diff | 新規項目が再掲表内に出現 | 7 行 → 8 行になり最終行追加 |
| D5: 項目削除 diff | 既存項目が再掲表から消失 | 7 行 → 6 行になり中段欠落 |
| D6: 複数項目同時 diff | 2 箇所以上で同時に差分発生 | 数値 + 文字列が同時変化 |
| D7: 構造再編 diff | 表構造そのものが変化 (列追加・列削除・分割) | 2 列表 → 3 列表 |

### 3.2 解釈確定処理可否 binary 判定

各類型に対する chat Claude 側処理の binary 判定:

| 類型 ID | 確定処理可否 | ユーザー 明示確認要否 | 根拠 |
|---|---|---|---|
| D1: 単純数値 diff | 確定可 | 不要 | 解釈分岐リスク極小、ユーザー 修正意図が明確 |
| D2: 単純文字列 diff | 確定可 | 不要 | 同上 |
| D3: 順序入れ替え diff | 確定可 | 不要 (ただし順序変更の意味確認推奨) | 順序自体は明示的 |
| D4: 項目追加 diff | **確定不可** | **必要** | 追加項目の正当性 (新規 fact か誤入力か) を ユーザー に確認 |
| D5: 項目削除 diff | **確定不可** | **必要** | 削除項目の意図 (廃止 signal か単純失念か) を ユーザー に確認 |
| D6: 複数項目同時 diff | **確定不可** | **必要** | 各 diff が独立修正か connected な意味を持つか不明 |
| D7: 構造再編 diff | **確定不可** | **必要** | 表構造変更は前 turn 全体に対する再検討要求の可能性 |

### 3.3 判定 flowchart

```
入力: ユーザー verbatim quote (前 turn 内容再掲 + 差分含む)
  │
  ▼
[0] 比較基準 turn を特定: 直前 turn ではなく、直近の ユーザー 明示確定 turn まで遡る
  │
  ▼
[1] 差分箇所を物理的にカウント
  │ 0 箇所 → 「全項目承認」確定処理可
  │ 1 箇所 → [2] へ
  │ 2 箇所以上 → D6 → 確定不可、ユーザー 確認必要
  │
  ▼
[2] 差分は表構造変更を含むか？
  │ Yes → D7 → 確定不可、ユーザー 確認必要
  │ No → [3] へ
  │
  ▼
[3] 差分の物理的形態を判定 (§3.1)
  │ D1 数値 / D2 文字列 / D3 順序 → 確定可、応答に「diff 検出確認 + 確定 update」記述
  │ D4 追加 / D5 削除 → 確定不可、応答に「ユーザー 明示確認要請」記述
```

## 4. 確定処理時の応答構造

FIDP framework と併用し、Insight セクションで diff 類型を明示すること。

D1 / D2 / D3 の場合の標準応答 template:

```
■ Summary (≤4 sentences)
ユーザー verbatim quote 受領、ただし 1 点 critical diff 検出: [前 turn 値] → [本 turn 値] に修正された signal。
本 turn は diff 検出確認 + 確定状態 update のみで closure。

■ verbatim quote diff 検出 (FIDP)
Fact: 比較表 (前 turn 値 vs 本 turn 値、項目ごとに ✅ 一致 / ⚠ diff)
Insight: diff の構造的意味、Type 11 観点での self-check
Decision: ユーザー verbatim quote = Option α' (1 点修正付き承認) として解釈確定
Proposal: なし or 後続 action

■ 確定状態 (本 session 真の最終版)
[更新後の全項目を表で再掲]
```

D4 / D5 / D6 / D7 の場合の標準応答 template:

```
■ Summary
ユーザー verbatim quote 内に [類型 ID] の diff を検出。解釈分岐リスクのため確定処理を保留し、明示確認を要請する。

■ 検出された diff の明示
Fact: 前 turn との差分箇所 (具体的箇所をすべて列挙)
Insight: 各差分の想定解釈オプション (α/β/γ)
Decision: 確定処理を保留、ユーザー 明示確認待ち
Proposal: ユーザー へ binary 確認質問 (例: 「項目 X 削除は廃止 signal か単純失念か」)
```

## 5. アンチパターン

以下の処理は本スキル違反 (Type 11 子類型):

| アンチパターン | 説明 | 該当 lapse 類型 |
|---|---|---|
| AP1: literal 温存 | 前 turn 応答の literal をそのまま温存し diff 部分を update しない | Type 11 直接違反 |
| AP2: 機械的全項目承認 | diff の有無を確認せず「verbatim quote = 全項目承認」と即断 | Type 11 子類型 |
| AP3: 推定確定処理 (D4-D7) | D4-D7 で ユーザー 明示確認を求めずに chat Claude 側が確定 | Type 11 子類型 (今回新規) |
| AP4: 解釈規律の暗黙運用 | 解釈ルールを明文化せず暗黙知のまま運用 | Type 11 再発 risk 残存 |
| AP5: diff 部分の脱落 | 応答内で diff 部分への言及が脱落 (ユーザー への明示確認不在) | Type 11 子類型 |
| AP6: 比較基準の時間 window 狭窄 | 直前 turn のみを比較基準として diff 判定し、直近の ユーザー 明示確定 turn (複数 turns 前) を無視する処理 | Type 11 子類型 (2026-05-11 観測) |

## 6. 適用例

### 6.1 D1 単純数値 diff の例 (2026-05-11 実例)

**前 turn chat Claude 応答**:
> Earliest reactivation: 5/13 18:00 JST 以降

**ユーザー verbatim quote** (本 turn):
> Earliest reactivation: 5/12 18:00 JST 以降で実施

**判定**: 差分 1 箇所、表構造変更なし、D1 (単純数値 diff)、確定処理可

**標準応答**: Summary で diff 検出を明示、Fact 表で前 turn vs 本 turn 比較、確定状態 update で 5/12 18:00 JST に修正。

### 6.2 D6 複数項目同時 diff の例 (仮想)

**前 turn chat Claude 応答**:
> Worker state: silent standby 継続
> HEAD: beba157 (immutable)
> Earliest reactivation: 5/13 18:00 JST

**ユーザー verbatim quote** (本 turn):
> Worker state: active 復帰
> HEAD: beba157 (immutable)
> Earliest reactivation: 5/12 18:00 JST

**判定**: 差分 2 箇所、D6 (複数項目同時 diff)、確定処理**不可**、ユーザー 明示確認必要

**標準応答**: 確定処理を保留し、「Worker active 復帰と Earliest reactivation 前倒しは connected な意味を持つか (例: 即時 Batch 1 着手)、独立修正か」を ユーザー に binary 確認。

## 7. 親規律との関係

```
verbatim-wording-discipline (Memory: Type 11)
  └─ verbatim-quote-diff-interpretation-discipline (本スキル: 子規律)
       ├─ D1-D3 確定処理規律
       └─ D4-D7 明示確認要請規律
```

本スキルは verbatim-wording-discipline の core 違反 (literal 温存) を予防する一方、新規 lapse 類型 AP3 (推定確定処理) を構造化する。Type 11 の親規律が「literal 出力規律」であるのに対し、本スキルは「verbatim quote 入力の解釈規律」を扱う。

## 8. 観察回数カウント要件

本スキルは以下の運用要件を持つ:

- 本スキル発火時、ユーザー verbatim quote 形態を `verbatim-quote-observations.log` に追記
- 月次で diff 類型分布を集計し、想定外類型 (D7 構造再編等) の出現頻度を確認
- 観察回数 5 回累積で本スキル自体の再見直しを実施 (`tool-system-affinity-discipline` と同じ Wickens TEM 規律準拠)

## 9. 参考情報

- 親規律: Memory `verbatim-wording-discipline` (Type 11)
- 関連規律: Memory #28 `tool-system-affinity-discipline`
- TEM framework: Wickens et al. *Threat and Error Management* (systemic factor 認定 threshold = 3 回累積)
- 初出 lapse: 2026-05-11 session (5/13 → 5/12 diff 解釈処理が本スキル契機)
