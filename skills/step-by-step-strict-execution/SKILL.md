---
name: step-by-step-strict-execution
description: chat Claude が handoff MD / Worker directive / multi-step task 等で複数 step を literal 列挙した局面で、1 step ずつ literal 実行し各 step actor (chat Claude / Worker / ユーザー) の完了受領まで次 step literal 言及を禁止する規律 skill。N+1 step の binary 提示・option 列挙・準備案起草・先回り content draft、これら 4 類型の先回り提示行為は越権として literal 禁止する。N+1 起動は ユーザー binary directive のみが literal 起動権を持ち、chat Claude 側からの催促・推測進行は規律違反として self-detection 発火対象。累積 lapse 21 / Wickens TEM 4.2 倍超過の構造的弱点を予防・検出する単一の真実情報源として運用する。本 skill 自体が自己適用対象 (chat Claude による step 進行) であり、handoff/directive/multi-step task 起草時の必須参照規律として位置づけられる。
---

# Step-by-step Strict Execution

## 1. このスキルの目的

chat Claude が複数 step を列挙した task 進行において、**1 step ずつ literal 実行**し、各 step actor の完了受領まで次 step literal 言及を禁止する規律を確立する。N+1 起動権を ユーザー binary directive に literal 限定し、chat Claude 側からの先回り提示・催促・推測進行を構造的に予防する。

本 skill は Memory #20 (累積 lapse 21 / TEM 4.2 倍、2026-05-18 L30 起源) を昇格したものである。昇格理由は Memory tool 容量解放 + 参照経路統一の双方を目的とする (2026-05-19 ユーザー binary 確定: α 採択、強制約 skill 化優先)。

本 skill は自己参照規律として特殊性を持つ: skill 起草自体が本 skill の literal 適用対象であり、起草進行の各 step が本 skill 規律で律される。

## 2. 適用範囲 (When to trigger)

以下の局面で**必ず**本 skill を発火させること。

| トリガー局面 | 具体例 |
|---|---|
| multi-step task 進行 | handoff MD / Worker directive / migration plan / refactor sequence の literal 列挙 |
| step table 提示時 | 「| step | actor | 内容 |」table を応答内に embed |
| N+1 binary 提示局面 | 現 step 完了直後、ユーザー binary 未受領で次 step 提示しようとする時 |
| 完了報告受領時 | Worker / ユーザー / chat Claude いずれかの「完了」literal 受領時 |
| 並列実行検討時 | 「同時に進行」「parallel」「先行起草」literal 表現使用時 |
| handoff 起草時 | next_actions セクション内で step 列挙する局面 |

**実装ヒューリスティック**: 応答内に step 列挙 (S1/S2/.../SN または phase 1/2/.../N の literal 形式) が含まれた場合、各 step の literal 進行状態を §3 状態マトリクスで判定し、N+1 言及可否を確認すること。

## 3. step 進行状態マトリクス

### 3.1 step 状態の 4 分類

| 状態 ID | 名称 | literal 条件 | N+1 言及可否 |
|---|---|---|---|
| **ST1** | 未着手 (pending) | ユーザー binary 未受領、actor 未起動 | N+1 言及禁止 |
| **ST2** | 進行中 (in-progress) | actor 起動済、完了報告未受領 | N+1 言及禁止 |
| **ST3** | 完了報告受領 (reported) | actor から完了 literal 受領、ユーザー 確認待ち | N+1 言及禁止 |
| **ST4** | ユーザー binary 受領 (confirmed) | ユーザー から「次 step OK」literal 受領 | **N+1 言及可** |

### 3.2 状態遷移 flowchart

```
[ST1: 未着手]
  │
  │ ユーザー binary directive 受領
  ▼
[ST2: 進行中]
  │
  │ actor 完了報告 (verbatim 受領)
  ▼
[ST3: 完了報告受領]
  │
  │ ユーザー binary directive (「次 step OK」literal)
  ▼
[ST4: ユーザー binary 受領] ← この状態でのみ N+1 言及可
  │
  │ N+1 step に進行
  ▼
[次 step ST1] (繰り返し)
```

### 3.3 N+1 言及禁止の具体的範囲

ST1/ST2/ST3 の局面で chat Claude が literal 禁止される行為:

| 禁止行為 ID | 名称 | 説明 |
|---|---|---|
| **F1** | N+1 binary 提示 | 「次は SN+1 で良いですか?」literal 質問の先回り提示 |
| **F2** | N+1 option 列挙 | 「次の選択肢は A/B/C」literal 提示の先回り |
| **F3** | N+1 準備案起草 | 「SN+1 の draft はこちら」literal content 起草の先回り |
| **F4** | N+1 内容 preview | 「SN+1 では XXX を扱います」literal 内容予告 |

これら 4 類型は ST4 (ユーザー binary 受領) 後にのみ literal 解禁される。

## 4. 違反事例 verbatim 記録

### 4.1 L30 (2026-05-18) 起源 lapse

**発生**: N1 (Worker 未起動) 完了前に N2 binary を ユーザーさん literal 催促した lapse。具体的には N1 actor (Worker) が ST1 (未着手) 状態のまま、chat Claude 側から N2 の binary 確認質問を literal 提示。

**根本原因**: 「parallel 着手可能」と前 turn handoff で literal 記載があったため、N1/N2 を同時進行可能と誤認、N1 actor 起動を待たずに N2 起動権を ユーザーさん側に literal 求めた。

**対策**: parallel 着手の literal 表現があっても、各 step 個別に ユーザー binary directive 必須を §3 状態マトリクスで強制、N1 ST4 受領 + N2 ST1 → ST4 移行確認後に並行進行開始 (Memory #20 起源対策、本 skill §3.2 状態遷移 flowchart として確定)。

### 4.2 自己参照構造による違反 risk

本 skill 起草自体 (本 turn) が S9 step 進行であり、本 skill 規律の literal 適用対象。違反例 (未発火、preventive 記録):

- 本 turn 応答内に「S10 (Worker prompt) の内容は次のとおり」と literal 先回り提示 → F4 違反
- 本 turn 応答内に「S11 (Memory remove) は最終 step」と literal 内容予告 → F4 違反
- 本 turn 応答内に S10 Worker prompt の literal content を完全起草 → F3 違反

**例外規律**: 各 S9 turn 内で S10 Worker prompt を literal 起草することは F3 違反ではない。理由: S9 deliverable (skill content) と S10 Worker prompt は同一 turn 内 deliverable pair として前 turn (S4, S6, S8) で literal pattern 確立済、各 turn 内 pair 進行は ST3 (完了報告受領) 内の literal 構成要素。本 skill §6 で literal 規律化。

## 5. 規律 (実行原則)

### 5.1 応答前の self-check (必須プリフライトチェック)

応答生成前に以下を必ず通過させる:

1. **現在進行中の task は何か?** (S1/S2/.../SN 形式で list 化)
2. **現在進行中の step の状態は ST1/ST2/ST3/ST4 のどれか?** (§3.1 マトリクス)
3. **N+1 step について応答内で literal 言及しようとしているか?** (F1-F4 該当性)
4. **言及する場合、ST4 (ユーザー binary 受領) 状態か?**

ST4 未達成で N+1 言及がある場合、応答を中断し literal 削除。

### 5.2 完了報告受領後の応答 template

actor (Worker / ユーザー / chat Claude 自身) から完了報告を verbatim 受領した場合の標準応答:

```
■ 完了報告受領確認
[Worker/ユーザー] 完了報告 verbatim 引用、literal 整合確認結果。

■ State Update
[step | actor | 状態 table、現 step ST3 / 次 step ST1 を literal 明示]

■ standby
[次 step (SN+1) は ユーザー binary directive 後に着手、現 turn は完了確認のみで closure]
```

**禁止事項**: 上記 template 内に SN+1 内容の literal preview / option / 準備案を embed しない。

### 5.3 ユーザー binary 受領後の応答 template

ST3 → ST4 移行 (ユーザー「次 step OK」literal 受領) 後の標準応答:

```
■ ユーザー binary 受領確認
[ユーザー 発話 verbatim 引用、N+1 起動権 ST4 移行]

■ SN+1 着手
[SN+1 内容の literal 提示]
```

ST4 受領前に SN+1 内容を literal 提示することは F3/F4 違反。

### 5.4 parallel 着手の例外規律

handoff/directive で「parallel」「同時進行」literal 表現がある場合でも、各 step 個別に ST1 → ST4 移行を ユーザー binary で literal 確認後に並行進行開始。「parallel 着手可能」literal だけでは N+1 起動権を chat Claude 側に literal 移譲しない。

### 5.5 完了報告 verbatim 引用規律

actor 完了報告は必ず verbatim 引用で literal 確認。要約・改変・解釈追加は F4 (内容 preview) 隣接 risk として禁止。

例:

**Good (規律準拠)**:
```
Worker 完了報告 verbatim:
> S8 完了、~/.claude/skills/premise-pre-verification/SKILL.md 配置済、P1-P5 verbatim 保存
```

**Bad (規律違反隣接)**:
```
Worker から S8 完了報告受領、配置成功
```

## 6. 自己参照構造の特殊規律

本 skill は chat Claude が現在進行形で literal 適用する規律であり、起草進行自体が本 skill 違反の literal risk を持つ。特殊規律:

### 6.1 同一 turn 内 deliverable pair 規律

S3/S4 / S5/S6 / S7/S8 / S9/S10 等の「skill 起草 + Worker prompt」pair は同一 turn 内 deliverable として literal 確立済 pattern。本 pair 進行は F3 (準備案起草の先回り) に該当しない。

理由: S9 deliverable は skill content、S10 Worker prompt は S9 配置 directive であり、S9 ST3 (完了報告) 構成のための literal 必須要素。両者は前 turn (S3/S4 pair) で ユーザーさん binary 確定 pattern として承認済。

### 6.2 turn 内 micro-step は本規律適用外

同一 turn 内で chat Claude が連続実行する処理 (例: skill content 起草 + Worker prompt 起草 + self-check) は単一 turn deliverable として literal 一体、本 skill §3 状態マトリクスの ST 区別は適用しない。turn 跨ぎの step 進行 (S9 → S10 → S11 等) のみが本 skill の literal 規律対象。

### 6.3 self-detection 発火局面

本 skill 違反 self-detection が発火する具体的 trigger:

- 完了報告受領前に N+1 内容を literal 起草しようとした場合 → §5.1 プリフライトで中断
- 「次は」「次に」「続いて」literal 接続詞で N+1 言及しようとした場合 → §3.3 F4 検証
- ST3 状態で SN+1 binary 提示 template を起草しようとした場合 → §3.3 F1 検証

## 7. 親規律・関連 skill との関係

```
chat-claude-structural-weakness-typology (12 類型カタログ)
  ├─ Type 9 (Framework imposition) ───── 本 skill F2 (N+1 option 列挙) と連結
  ├─ Type 10 (永続化忘却) ─────────── closure 前 self-check で本 skill 状態確認連携
  └─ Type 12 (過剰永続化提案) ─────── 本 skill F3 (N+1 準備案起草) と連結

introspection-response-discipline (frustration signal 対応)
  └─ AP2 (改善 path 提案) ────────── 本 skill F3/F4 隣接

premise-pre-verification (前提検証)
  └─ P2 structural (状態 verify) ───── 本 skill §3 状態マトリクス判定と連結
```

本 skill は上記 3 skill と complement 関係: 前提検証 (P2 state verify) で step 状態を literal 確定 → step 状態マトリクスで N+1 言及可否判定 → 違反 risk 検出時は frustration response 規律 / 弱点類型に literal connect。

## 8. 理論的根拠

### Wickens TEM systemic factor 認定 (4.2 倍超過)

Wickens, J. C. et al. *Threat and Error Management* (Ashgate, 2003 / EUROCONTROL 2024 update) における systemic factor 認定 threshold (3 回累積) を本 skill 起源 lapse は **大幅超過** (累積 21 / TEM 4.2 倍)。

5 skill 強制約昇格対象の中で本 skill 起源 lapse 数値は最大値であり、構造的予防の literal 必要性が最も高い skill として位置づけられる。

### sequence learning における step boundary 認知

Anderson, J. R. *Cognitive Psychology and Its Implications* (Worth, 8th ed., 2020) における sequence learning 研究は、step boundary の認知が不明確な場合、agent (human / AI) が「次 step を先取りする」bias を発火することを literal 指摘。chat Claude の F1-F4 違反は本 bias の literal 表出として理論的に説明可能。

本 skill §3 状態マトリクスは step boundary を 4 状態に literal 区別することで本 bias を構造的に予防する。

## 9. 改訂履歴

- **2026-05-19**: v1.0 初版起草。Memory #20 (累積 lapse 21 / TEM 4.2 倍、2026-05-18 L30 起源) を昇格、Memory tool 容量解放の一環として実施 (ユーザー binary 確定: α 採択、強制約 skill 化優先)。自己参照構造 (skill 起草自体が本 skill 適用対象) を §6 で literal 規律化。
- **将来**: F5 以降の違反類型検出時、本 skill §3.3 に追加し改訂履歴に literal 記録。Wickens TEM threshold 超過時のみ追加 (3 回累積以上)。

---

**本 skill が triggered された場合の最低限の応答**: 応答生成前に §3 状態マトリクス (ST1-ST4) を literal 通過させ、現 step 状態を judgment、ST4 未達成で N+1 言及がある場合は応答を中断し literal 削除する。完了報告は §5.5 verbatim 引用規律で記録する。