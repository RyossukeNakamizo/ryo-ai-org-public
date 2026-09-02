#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_layout.py — 「見る報告」の文字壁検問（見せ方の憲法 第4条の実装）

なにをする道具か（平易な説明）:
  AIが書いたHTMLの報告書を開く前に、機械が「これは文字だらけではないか」を調べます。
  人の目は疲れるし、作った本人の目はいちばん甘い。だから関門を機械に置きます。

見た目の決まりの正本:
  同じフォルダの ..\SKILL.md 「見た目の4つの決まり」
  （図解ファースト／1画面1論点／文字壁は機械で検問／スマホでも成立する）

使い方:
  python check_layout.py "<報告HTMLのフルパス>"      # 検問する
  python check_layout.py --mirror "<パス>"           # ミラー（保管庫）なので検問を免除
  python check_layout.py --reference "<パス>"        # 参照図（組織図・地図）なので「押せる部品」だけ免除
  python check_layout.py --json "<パス>"             # 機械が読む用にJSONで出す
  python check_layout.py --selftest                  # この道具自身が壊れていないか確かめる

判定:
  OK   合格   … 本人に出してよい
  WARN 要改善 … 惜しい。指摘を直してから出す
  NG   文字壁 … 憲法違反。出してはいけない（v3 第2章の変換規範からやり直す）

見ている6つのこと:
  1. 本文の文字数            … 報告全体の重さ
  2. 長すぎる文字の塊の数    … 1つのカタマリに詰め込みすぎていないか（LONG_BLOCK_CHARS 以上）
  3. 視覚部品の数            … 表・図・カード・バーなど「見て分かる部品」がいくつあるか
  4. 押せる部品の数          … ボタン・3択・コピー・開閉（本人の手が動く場所があるか）
  5. スマホで成立するか      … viewport指定／表が横スクロールの囲みに入っているか／可変レイアウト（憲法第6条）
  6. 禁止句が無いか          … 「一言で返してください」等、判断を文章で頼む言い回し（憲法第2条の部品表）
                               2026-08-01追加: ㊱の報告が「A/B/Cを一言で返す」と文章で聞いた事故を受けて

しきい値の根拠:
  文字だらけの実物を NG、図と表で組んだ実物を OK と判定できる位置に置いてあります。
  ここを動かすときは、必ず --selftest が通ることを確かめてください。

ELI5（読む図解）での使い方:
  python check_layout.py --reference "<作った図解HTMLのフルパス>"
  ※ --reference を付けます。読んで終わる資料なので「押せる部品」の条件だけ免除されます。
"""

import sys
import os
import re
import json
import math
from html.parser import HTMLParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- しきい値
LONG_BLOCK_CHARS = 200      # これ以上の文字が1つの塊に入っていたら「長い塊」
CHARS_PER_VISUAL = 700      # 本文700文字につき視覚部品1つは要る、という目安
SMALL_REPORT_CHARS = 400    # これ未満は「短いメモ」扱いで検問をゆるめる
NEEDS_ACTION_CHARS = 1200   # これ以上の報告に押せる部品が1つも無ければ憲法第2条違反

NG_LONG_BLOCKS = 4          # 長い塊がこれ以上 → 文字壁
WARN_LONG_BLOCKS = 2        # 長い塊がこれ以上 → 要改善

# 視覚部品とみなすタグ
VISUAL_TAGS = {"table", "svg", "img", "canvas", "progress", "meter", "figure"}
# 視覚部品とみなす class 名。
#   EXACT = 短くてありふれた名前。部分一致にすると "arrow" が "row" に化けるので完全一致で見る
#   PARTS = 長くて紛れの無い名前。接頭辞つき（dept-card 等）を拾いたいので部分一致で見る
VISUAL_CLASS_EXACT = {
    "row", "box", "tile", "bar", "chip", "step", "act", "panel", "col",
    "cell", "node", "swap", "law", "article", "fbox", "rhythm",
}
VISUAL_CLASS_PARTS = (
    "card", "verdict", "flow", "chart", "graph", "diagram",
    "kpi", "stat", "timeline", "gauge", "matrix",
)
# 押せる部品とみなすタグ
CLICKABLE_TAGS = {"button", "details", "select"}
CLICKABLE_INPUT_TYPES = {"button", "submit", "checkbox", "radio", "reset"}

# 禁止句（憲法第2条の部品表・SKILL.md第1章と対）:
#   判断を求めるならチャット=AskUserQuestion／HTML=承認シート型。文章で頼む言い回しは検出する。
#   注意: 「一言で返して」だけを検出語にすると、憲法の条文説明（『「一言で返して」は禁止句』という
#   言及）まで誤検出する。だから「を一言で返」「〜してください」の形まで含めて検出語にしている。
BANNED_PHRASES = [
    ("を一言で返",             "「A/B/Cを一言で返す」——判断はAskUserQuestionか承認シート型で"),
    ("一言で返してください",   "「一言で返してください」——判断はAskUserQuestionか承認シート型で"),
    ("どれにするか教えてください", "「どれにするか教えてください」——選択肢はボタンにする"),
    ("と返信してください",     "「〜と返信してください」——返信文を打たせない。ボタンかコピー欄に"),
    ("と書いてもらえれば",     "「〜と書いてもらえれば」——同上"),
    ("よければ言ってください", "「よければ言ってください」——判断の口を曖昧にしない"),
    ("確認しておいてください", "「確認しておいてください」——誰が・いつ・何をまで書くか、チェック欄にする"),
]

# 本文の塊とみなすタグ（この単位で文字数を数える）
BLOCK_TAGS = {
    "p", "li", "td", "th", "div", "blockquote", "dd", "dt",
    "h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "summary", "caption",
}
# 中身を本文に数えないタグ
SKIP_TAGS = {"script", "style", "head", "title", "noscript", "textarea"}


class ReportParser(HTMLParser):
    """報告HTMLを1回なめて、4つの数字を集める"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.block_stack = []          # [(tag, 直下に貯めた文字列), ...]
        self.blocks = []               # 塊ごとの文字数
        self.visual_count = 0
        self.visual_detail = {}
        self.clickable_count = 0
        self.clickable_detail = {}
        self.textarea_count = 0
        self.texts = []                # 禁止句検出用の全文（textarea等のSKIP_TAGS内は含めない）

    # -- 部品を数える -------------------------------------------------
    def _count_visual(self, tag, attrs):
        d = dict(attrs)
        if tag in VISUAL_TAGS:
            self.visual_count += 1
            self.visual_detail[tag] = self.visual_detail.get(tag, 0) + 1
            return
        cls = (d.get("class") or "").lower()
        if not cls:
            return
        for token in cls.split():
            hit = token in VISUAL_CLASS_EXACT or any(p in token for p in VISUAL_CLASS_PARTS)
            if hit:
                self.visual_count += 1
                key = "." + token
                self.visual_detail[key] = self.visual_detail.get(key, 0) + 1
                return

    def _count_clickable(self, tag, attrs):
        d = dict(attrs)
        hit = None
        if tag in CLICKABLE_TAGS:
            hit = tag
        elif tag == "input" and (d.get("type") or "").lower() in CLICKABLE_INPUT_TYPES:
            hit = "input"
        elif "onclick" in d:
            hit = "onclick"
        elif (d.get("role") or "").lower() == "button":
            hit = 'role="button"'
        if hit:
            self.clickable_count += 1
            self.clickable_detail[hit] = self.clickable_detail.get(hit, 0) + 1

    # -- HTMLParser の口 ----------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag == "textarea":
            self.textarea_count += 1
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        self._count_visual(tag, attrs)
        self._count_clickable(tag, attrs)
        if tag in BLOCK_TAGS:
            self.block_stack.append([tag, []])

    def handle_startendtag(self, tag, attrs):
        if self.skip_depth:
            return
        self._count_visual(tag, attrs)
        self._count_clickable(tag, attrs)

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in BLOCK_TAGS:
            # 対応する開始タグまで巻き戻す（閉じ忘れに耐える）
            for i in range(len(self.block_stack) - 1, -1, -1):
                if self.block_stack[i][0] == tag:
                    for popped in self.block_stack[i:]:
                        text = normalize("".join(popped[1]))
                        if text:
                            self.blocks.append(len(text))
                    del self.block_stack[i:]
                    break

    def handle_data(self, data):
        if self.skip_depth or not data.strip():
            return
        self.texts.append(data)
        if self.block_stack:
            # いちばん内側の塊にだけ足す（入れ子の親に二重計上しない）
            self.block_stack[-1][1].append(data)

    def finish(self):
        for popped in self.block_stack:
            text = normalize("".join(popped[1]))
            if text:
                self.blocks.append(len(text))
        self.block_stack = []


def normalize(s):
    return re.sub(r"\s+", " ", s).strip()


def measure(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    return measure_html(html, path)


def measure_html(html, path="(inline)"):
    p = ReportParser()
    p.feed(html)
    p.close()
    p.finish()

    # 憲法第2条の部品表: 禁止句（判断を文章で頼む言い回し）を本文から探す
    fulltext = normalize("".join(p.texts))
    banned_hits = [label for pat, label in BANNED_PHRASES if pat in fulltext]

    # 憲法第6条: スマホで成立するか（静かに見られる3点だけ機械で見る）
    has_viewport = bool(re.search(r'<meta[^>]+name=["\']viewport', html, re.I))
    has_media = "@media" in html
    n_tables = len(re.findall(r"<table\b", html, re.I))
    has_hscroll = bool(re.search(r"overflow-x\s*:\s*auto|overflow\s*:\s*auto", html, re.I))

    total_chars = sum(p.blocks)
    long_blocks = [n for n in p.blocks if n >= LONG_BLOCK_CHARS]
    return {
        "has_viewport": has_viewport,
        "has_media": has_media,
        "n_tables": n_tables,
        "has_hscroll": has_hscroll,
        "file": os.path.basename(path),
        "path": os.path.abspath(path),
        "total_chars": total_chars,
        "block_count": len(p.blocks),
        "long_blocks": len(long_blocks),
        "max_block": max(p.blocks) if p.blocks else 0,
        "visual_count": p.visual_count,
        "visual_detail": p.visual_detail,
        "clickable_count": p.clickable_count,
        "clickable_detail": p.clickable_detail,
        "textarea_count": p.textarea_count,
        "banned_hits": banned_hits,
        "required_visuals": max(1, math.ceil(total_chars / CHARS_PER_VISUAL)) if total_chars else 0,
    }


def judge(m, is_mirror=False, is_reference=False):
    """4つの数字から判定する。理由は必ず日本語で返す。"""
    if is_mirror:
        return "MIRROR", ["ミラー（保管庫）として申告されたので検問を免除しました（憲法第5条）。"
                          "報告として本人に出す場合は、この免除は使えません。"]

    ng, warn = [], []
    tc = m["total_chars"]

    # 憲法第2条の部品表: 禁止句（判断を文章で頼んでいないか）
    #   短いメモでも参照図でも免除しない——判断を求めた時点で「押せる形」の義務が生じる。
    for label in dict.fromkeys(m.get("banned_hits") or []):
        ng.append(f"禁止句があります: {label}（憲法第2条の部品表違反）。")

    if tc < SMALL_REPORT_CHARS and not ng:
        # 短いメモは飾りすぎのほうが害。最低限だけ見る
        if m["visual_count"] == 0 and m["clickable_count"] == 0:
            warn.append(f"本文{tc}文字と短いですが、図も押せる部品も0です。メモ以上の内容なら1つは要ります。")
        return ("WARN" if warn else "OK"), (warn or ["短い報告として問題なしです。"])

    # 憲法第1条: 図解ファースト
    if m["visual_count"] == 0:
        ng.append(f"視覚部品が0です（本文{tc}文字）。表もカードも図もありません＝憲法第1条違反。")
    elif m["visual_count"] * 2 < m["required_visuals"]:
        ng.append(f"視覚部品が{m['visual_count']}個しかありません。"
                  f"本文{tc}文字なら目安{m['required_visuals']}個以上（{CHARS_PER_VISUAL}文字に1個）。")
    elif m["visual_count"] < m["required_visuals"]:
        warn.append(f"視覚部品{m['visual_count']}個は目安{m['required_visuals']}個に届いていません。"
                    "結論・原因・比較のどれかを図か表にしてください。")

    # 憲法第2条: アクションは押せる形
    #   参照図（組織図・地図・カタログ）は「本人にしてほしいこと」が無いのが正常なので、この条は掛けない。
    #   2026-08-01: 本人が「良い」と評価しているORG-CHART.htmlを不合格にしてしまい、線を引き直した。
    if is_reference and m["clickable_count"] == 0:
        pass
    elif m["clickable_count"] == 0:
        if tc >= NEEDS_ACTION_CHARS:
            ng.append(f"押せる部品が0です（本文{tc}文字）。"
                      "ボタン・3択・コピー・開閉のどれも無い＝本人に文章で頼んでいます（憲法第2条違反）。")
        else:
            warn.append("押せる部品が0です。本人にしてほしいことがあるなら、ボタンかコピー欄にしてください。")

    # 憲法第2条の部品表: 禁止句（判断を文章で頼んでいないか）
    #   参照図でも免除しない——判断を求めているなら、それはもう参照図ではない。
    if m.get("banned_hits"):
        for label in m["banned_hits"]:
            ng.append(f"禁止句があります: {label}（憲法第2条の部品表違反）。")

    # 憲法第3条: 1画面1判断（畳めていない＝長い塊）
    # 憲法第6条: スマホで成立するか
    if not m["has_viewport"]:
        ng.append("viewport の指定がありません。スマホで開くと文字が極小になります（憲法第6条違反）。"
                  '<meta name="viewport" content="width=device-width, initial-scale=1.0"> を入れてください。')
    else:
        if not m["has_media"]:
            warn.append("可変レイアウト（@media）がありません。狭い画面で1カラムに落ちるか確かめてください（憲法第6条）。")
        if m["n_tables"] and not m["has_hscroll"]:
            warn.append(f"表が{m['n_tables']}個ありますが、横スクロールの囲み（overflow-x:auto）が見当たりません。"
                        "スマホでページ全体が横に振れます（横に振ってよいのは表の中だけ）。")

    if m["long_blocks"] >= NG_LONG_BLOCKS:
        ng.append(f"{LONG_BLOCK_CHARS}文字以上の長い塊が{m['long_blocks']}個あります"
                  f"（最長{m['max_block']}文字）。詳細は開閉に畳むか、表・カードに割ってください（憲法第3条）。")
    elif m["long_blocks"] >= WARN_LONG_BLOCKS:
        warn.append(f"長い塊が{m['long_blocks']}個あります（最長{m['max_block']}文字）。"
                    "1つでも図か開閉に変えられないか見てください。")

    if ng:
        return "NG", ng + warn
    if warn:
        return "WARN", warn
    return "OK", ["憲法の最低線（図がある・押せる・畳めている）を満たしています。"]


LABEL = {
    "OK": "✅ 合格",
    "WARN": "⚠️ 要改善",
    "NG": "❌ 文字壁（出してはいけません）",
    "MIRROR": "📦 ミラー（検問免除）",
}


def report(m, verdict, reasons):
    print("=" * 64)
    print(f"検問結果: {LABEL[verdict]}")
    print(f"対象: {m['file']}")
    print("-" * 64)
    print(f"  本文の文字数        : {m['total_chars']}")
    print(f"  長すぎる塊({LONG_BLOCK_CHARS}字以上): {m['long_blocks']} 個 （最長 {m['max_block']} 字）")
    print(f"  視覚部品（図・表・カード）: {m['visual_count']} 個 （目安 {m['required_visuals']} 個以上）")
    print(f"  押せる部品（ボタン・開閉）: {m['clickable_count']} 個")
    sp = []
    sp.append("viewport✅" if m["has_viewport"] else "viewport❌")
    sp.append("可変レイアウト✅" if m["has_media"] else "可変レイアウト❌")
    if m["n_tables"]:
        sp.append("表の横スクロール✅" if m["has_hscroll"] else "表の横スクロール❌")
    print(f"  スマホ対応（第6条）  : " + " / ".join(sp))
    print(f"  禁止句（第2条）      : " + ("❌ " + str(len(m["banned_hits"])) + " 件" if m.get("banned_hits") else "✅ なし"))
    if m["visual_detail"]:
        top = sorted(m["visual_detail"].items(), key=lambda x: -x[1])[:6]
        print("    内訳: " + ", ".join(f"{k}×{v}" for k, v in top))
    if m["clickable_detail"]:
        print("    内訳: " + ", ".join(f"{k}×{v}" for k, v in m["clickable_detail"].items()))
    print("-" * 64)
    for r in reasons:
        print(f"  ・{r}")
    print("=" * 64)


# ---------------------------------------------------------------- 自己テスト
# 自己テストの見本は、この中に埋め込んである（配った先でも動くように・外のファイルを読まない）

WALL_HTML = """<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>文字壁の見本</title>
</head><body>
<h1>文字だらけの資料の見本</h1>
<p>""" + ("この段落は、図も表もカードも無いまま、ひたすら文章だけが続く資料の見本です。"
          "人はこれを渡されると、どこを読めばいいのか分からなくなります。"
          "作った側は書いたので分かっていますが、読む側には届きません。") * 12 + """</p>
</body></html>"""

GOOD_HTML = """<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>図解の見本</title>
<style>@media(max-width:640px){.card{width:100%}}</style></head><body>
<h1>図で見せた資料の見本</h1>
<p>結論を先に図で見せて、文章はその補足にまわします。</p>
<div class="card">結論のカード1</div><div class="card">結論のカード2</div>
<div style="overflow-x:auto"><table><tr><th>項目</th><th>結果</th></tr>
<tr><td>ひとつめ</td><td>できた</td></tr><tr><td>ふたつめ</td><td>できた</td></tr></table></div>
<svg viewBox="0 0 200 60" role="img" aria-label="AからBへ渡す関係図">
  <rect x="4" y="10" width="70" height="40" rx="6" fill="#fff" stroke="#3460FB"/>
  <text x="39" y="35" font-size="12" text-anchor="middle">A</text>
  <line x1="78" y1="30" x2="120" y2="30" stroke="#3460FB" stroke-width="2"/>
  <text x="99" y="22" font-size="10" text-anchor="middle">渡す</text>
  <rect x="126" y="10" width="70" height="40" rx="6" fill="#fff" stroke="#3460FB"/>
  <text x="161" y="35" font-size="12" text-anchor="middle">B</text>
</svg>
<details><summary>詳しく見る</summary><p>細かい話はここに畳みます。</p></details>
</body></html>"""

SELFTEST_CASES = [
    # (中身, 期待, なぜこれを試すのか)
    (WALL_HTML, "NG", "図も表も無く文章だけの資料。これを止められなければ、検問の意味がない"),
    (GOOD_HTML, "OK", "図・表・開閉があり、スマホでも成立する資料。これを落とすなら、しきい値が厳しすぎる"),
]


# 禁止句の自己テスト用: 図もボタンもviewportもある「見た目は合格」のHTMLに、禁止句だけを仕込む。
#   これをNGにできなければ、禁止句検出は飾りになっている。
BANNED_SELFTEST_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>@media(max-width:640px){.card{width:100%}}</style></head><body>
<div class="card">結論カード</div><table><tr><td>表</td></tr></table>
<div style="overflow-x:auto"></div><button>押せるボタン</button>
<p>次のアクション: A / B / C を一言で返してください（1分）。</p>
</body></html>"""


def selftest():
    print("【自己テスト】この検問が正しく効いているかを確かめます\n")
    all_ok = True

    # 追加テスト: 禁止句入りHTML（2026-08-01・㊱報告の事故を再現）
    m = measure_html(BANNED_SELFTEST_HTML, "(禁止句テスト)")
    v, _ = judge(m)
    ok = (v == "NG" and m["banned_hits"])
    all_ok = all_ok and bool(ok)
    print(f"  {'✅' if ok else '❌'} 禁止句テスト（『一言で返してください』を仕込んだHTML）")
    print(f"     期待=NG / 実際={v} / 検出={len(m['banned_hits'])}件\n")

    for html, expect, why in SELFTEST_CASES:
        m = measure_html(html, "(見本)")
        v, reasons = judge(m, is_reference=(expect == "OK"))
        ok = (v == expect)
        all_ok = all_ok and ok
        print(f"  {'✅' if ok else '❌'} {why[:20]}…")
        print(f"     期待={expect} / 実際={v}　（{why}）")
        print(f"     文字{m['total_chars']} 長い塊{m['long_blocks']} 図{m['visual_count']} 押せる{m['clickable_count']}")
        print()
    print("結果: " + ("✅ 検問は正しく効いています" if all_ok else "❌ 検問がおかしいので、しきい値を見直してください"))
    return 0 if all_ok else 1


def main():
    args = [a for a in sys.argv[1:]]
    if "--selftest" in args:
        sys.exit(selftest())

    is_mirror = "--mirror" in args
    is_reference = "--reference" in args
    as_json = "--json" in args
    files = [a for a in args if not a.startswith("--")]

    if not files:
        print(__doc__)
        sys.exit(2)

    worst = 0
    rank = {"OK": 0, "MIRROR": 0, "WARN": 1, "NG": 2}
    for path in files:
        if not os.path.exists(path):
            print(f"❌ ファイルが見つかりません: {path}")
            worst = max(worst, 2)
            continue
        m = measure(path)
        v, reasons = judge(m, is_mirror, is_reference)
        if as_json:
            print(json.dumps({"verdict": v, "reasons": reasons, **m}, ensure_ascii=False, indent=2))
        else:
            report(m, v, reasons)
        worst = max(worst, rank[v])
    sys.exit(worst)


if __name__ == "__main__":
    main()
