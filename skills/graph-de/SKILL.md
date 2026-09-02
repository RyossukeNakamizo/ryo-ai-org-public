---
name: graph-de
description: |
  インタラクティブなグラフ・チャート・データビジュアライゼーションをウィジェットとして表示するスキル。
  トリガーは明示要求のみ: 「グラフで見せて」「チャートにして」「視覚化して」と言われた時、または /graph-de コマンドが投入された時に使う。
  Chart.js を使ったインタラクティブなスライダー付きウィジェットを生成し、ユーザーがパラメータを動かしてリアルタイムに変化を確認できるようにする。
  claude.ai のウィジェット表示（visualize:）は Claude Code CLI では使えないため、CLI では HTML ファイル生成 + open コマンドが主経路。
  〈案件〉 PoC評価結果の精度比較グラフ、WBS進捗チャートにも使用可能。
  汎用チャート設計原則は dataviz skill が担当。本スキルはスライダー付きインタラクティブウィジェット特化。
---

# グラフで スキル

ユーザーが「グラフで見せて」「チャートにして」「視覚化して」と明示的に要求したとき、または /graph-de コマンドが投入されたとき、インタラクティブなウィジェットを生成する。

**環境による主経路の違い:** claude.ai のウィジェット表示（`visualize:read_me` / `visualize:show_widget`）は Claude Code CLI では使えない。CLI では「HTMLファイル生成 + `open` コマンド」が主経路となる（後述「Claude Code向け実行手順」参照）。以下の基本フローは claude.ai 環境向け。

## 基本フロー

1. `visualize:read_me` を呼んでデザインシステムを確認（`modules: ["chart", "interactive", "data_viz"]`）
2. `visualize:show_widget` でHTML/Chart.jsウィジェットを生成
3. 簡潔な説明をテキストで補足

## ウィジェット設計ルール

### スライダーで操作可能にする
ユーザーがパラメータを変更してリアルタイムに結果を確認できるよう、入力値はすべてスライダー（`<input type="range">`）で操作可能にする。

### メトリクスカードでサマリーを表示
グラフの上または下に、主要な数値をカード形式で表示する。

### Chart.js の使い方
```html
<div style="position: relative; width: 100%; height: 280px;">
  <canvas id="chart"></canvas>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
```

**Chart.js 必須ルール:**
- `canvas` は必ず `position: relative` のdivでラップ、heightはdivに指定
- `responsive: true, maintainAspectRatio: false`
- 凡例は `legend: { display: false }` にして手動でHTMLに書く
- 数値は必ず丸める（`Math.round()`, `.toFixed(n)`）
- 色はハードコードのhex値（CSSvar非対応）

### カラーパレット（推奨）
| 用途 | 色 |
|------|-----|
| メイン（複利・成長など） | `#7F77DD`（パープル） |
| サブ（比較・単利など） | `#1D9E75`（ティール） |
| 中立・元本 | `#888780`（グレー） |
| 警告・リスク | `#D85A30`（コーラル） |
| 情報 | `#378ADD`（ブルー） |

### 数値フォーマット
日本語表示では万・億単位に変換する：
```js
function fmt(n) {
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '億円';
  if (n >= 10000) return Math.round(n / 10000) + '万円';
  return n.toLocaleString() + '円';
}
```

## よく使うチャートタイプ

| タイプ | 用途 | Chart.js設定 |
|--------|------|-------------|
| line | 時系列・成長・推移 | `fill: true`, `tension: 0.4` |
| bar | カテゴリ比較・ランキング | `indexAxis: 'y'` で水平も可 |
| doughnut | 構成比・シェア | 視認性が高い |
| scatter | 相関・分布 | 2変数の関係 |

## テキスト補足のルール

ウィジェットの後に以下を簡潔に書く：
- グラフの読み方・ポイント（2〜3文）
- 背景にある原理・公式（必要な場合のみ）
- 過剰な説明は不要（ユーザーはグラフを見て理解できる）

---

## Claude Code向け実行手順

Claude Code環境では `visualize:show_widget` が使用できないため、以下の代替手順で実行する:

### 方法1: HTMLファイル書き出し（推奨）
```bash
# Chart.jsウィジェットをHTMLファイルとして生成
cat > /tmp/chart_output.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head>
<body>
  <!-- ウィジェットコードをここに配置 -->
</body>
</html>
EOF
open /tmp/chart_output.html  # macOS
```

### 方法2: React Artifact（Claude.ai連携）
Claude.aiに切り替えて `visualize:show_widget` で表示する。
Claude Codeで生成したデータ/設定をClaude.aiに渡す場合は `context-handoff` を使用。

### 環境検出
Claude Codeで実行中かどうかの判断:
- `visualize:show_widget` が利用不可 → Claude Code環境
- 利用可能 → Claude.ai環境

---

## 連携スキル

- **fidp-thinking**: FIDPのFact部分をグラフで視覚化し、報告の説得力を高める
- **azure-rag**: PoC評価結果（精度・レイテンシ・コスト）の比較チャートに使用
- **review-agent-essence**: スキルスコアの推移を時系列グラフで表示可能
