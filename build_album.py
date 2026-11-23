import json, os, sys
from urllib.parse import quote
from datetime import date
from string import Template

BASE = os.path.dirname(os.path.abspath(__file__))
PIC_DIR = "resource/pic"

def img_src(name):
    # 图片统一放在 resource/pic/，HTML 在项目根，这里写相对路径引用
    return quote(PIC_DIR + "/" + name)

sys.path.insert(0, BASE)
from album_db import all_tickets, stats
import sqlite3

def load_trips():
    try:
        con = sqlite3.connect(os.path.join(BASE, "resource", "db", "tickets.db"))
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT kind,date,date_end,city,name,detail,source FROM trips ORDER BY date DESC").fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

TRIPS = load_trips()

TICKETS = all_tickets()
# 无日期的排最后
TICKETS.sort(key=lambda t: (t["date"] or ""), reverse=True)

data = []
for t in TICKETS:
    d = dict(t)
    # 多图：每张都作为独立资源引用，带面标记
    d["imgs"] = [
        {"side": im["side"], "src": img_src(im["img_file"])}
        for im in t.get("images", [{"side": "正面", "img_file": t["img_file"]}])
    ]
    # 缩略图统一用 imgs[0].src
    # 无日期票显示占位
    d["date_label"] = d.get("date_label") or "日期待补充"
    d["sub"] = d.get("sub") or ""
    data.append(d)

st = stats()

TPL = Template(r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>足迹票册 · 门票收藏</title>
<style>
  :root{
    color-scheme:light;
    --bg:#faf7f2; --card:#fffdfa; --ink:#2b2520; --muted:#756a5f;
    --accent:#c2703a; --accent-soft:#f7e9dd; --line:#e9dfd3; --pending:#b8863b;
    --glass:rgba(255,253,250,.76);
    --glass-strong:rgba(255,253,250,.90);
    --glass-edge:rgba(255,255,255,.92);
    --glass-outline:rgba(203,186,168,.42);
    --glass-shadow:0 8px 24px rgba(96,74,52,.10),0 1px 3px rgba(96,74,52,.06);
    --glass-blur:blur(13px) saturate(140%);
  }
  *{box-sizing:border-box}
  body{margin:0;color:var(--ink);min-height:100vh;background:var(--bg);
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
    line-height:1.6;-webkit-font-smoothing:antialiased}
  /* 背景柔光：单层 fixed 容器承载所有色彩，光斑静止，滚动时不重绘不晃 */
  .bg-orbs{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
    background:radial-gradient(900px 640px at 6% -6%,rgba(251,230,210,.85) 0%,rgba(251,230,210,0) 64%),
      radial-gradient(820px 620px at 98% 4%,rgba(220,235,244,.75) 0%,rgba(220,235,244,0) 66%),
      radial-gradient(760px 760px at 50% 106%,rgba(230,225,242,.62) 0%,rgba(230,225,242,0) 68%)}
  .bg-orbs i{position:absolute;display:block;border-radius:50%;filter:blur(80px);opacity:.26}
  .bg-orbs i:nth-child(1){width:440px;height:440px;left:-110px;top:-100px;background:#f6b98c}
  .bg-orbs i:nth-child(2){width:400px;height:400px;right:-120px;top:18%;background:#a9c9e2}
  .bg-orbs i:nth-child(3){width:380px;height:380px;left:12%;top:62%;background:#c8b6e4}
  .bg-orbs i:nth-child(4){width:340px;height:340px;right:6%;bottom:-90px;background:#f3c9cf}
  .wrap{position:relative;z-index:1;max-width:880px;margin:0 auto;padding:44px 20px 72px}
  header{text-align:center;margin-bottom:32px}
  .kicker{font-size:11px;letter-spacing:.3em;color:var(--accent);text-transform:uppercase;margin-bottom:10px}
  h1{font-size:30px;margin:0 0 8px;font-weight:700;letter-spacing:.06em}
  header p{margin:0;color:var(--muted);font-size:13px}
  .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}
  .stat{background:var(--glass);border:1px solid var(--glass-edge);border-radius:14px;padding:14px 10px;text-align:center;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.9),var(--glass-shadow)}
  .stat b{display:block;font-size:23px;color:var(--accent);font-weight:700;line-height:1.2}
  .stat span{font-size:11px;color:var(--muted)}
  .toolbar{display:flex;gap:8px;justify-content:flex-end;margin-bottom:28px;flex-wrap:wrap}
  .btn{font:inherit;font-size:12px;padding:7px 14px;border:1px solid var(--glass-edge);background:var(--glass);
    color:var(--ink);border-radius:9px;cursor:pointer;transition:all .15s;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 4px 14px rgba(96,74,52,.06)}
  .btn:hover{border-color:var(--accent);color:var(--accent)}
  .btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
  .btn.primary:hover{opacity:.9;color:#fff}
  h2{font-size:17px;margin:0 0 18px;font-weight:600;display:flex;align-items:center;gap:9px}
  h2::before{content:"";width:4px;height:17px;background:var(--accent);border-radius:2px}
  .hint{font-size:12px;color:var(--muted);margin:-8px 0 18px}
  .cnt{font-size:11px;font-weight:400;color:var(--muted);background:#f0e8dc;padding:2px 8px;border-radius:10px}
  h2.pending-h::before{background:var(--pending)}
  .timeline{margin-bottom:44px}
  .timeline.pending-tl{position:relative;padding-left:28px}
  .pending-tl::before{content:"";position:absolute;left:8px;top:6px;bottom:6px;width:2px;background:#e8dcc8}
  /* 年份卡 */
  .year-block{margin-bottom:38px;scroll-margin-top:58px}
  .year-block + .year-block{border-top:1px dashed rgba(190,170,148,.55);padding-top:26px}
  .year-head{position:relative;display:flex;align-items:center;gap:12px;
    padding:11px 18px;margin-bottom:16px;border:1px solid var(--glass-edge);border-left:4px solid var(--accent);
    background:linear-gradient(100deg,rgba(247,233,221,.78) 0%,rgba(255,253,250,.62) 58%,rgba(255,255,255,.42) 100%);
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.9),var(--glass-shadow);
    border-radius:0 14px 14px 0}
  .year-num{font:800 32px/1 Georgia,"Times New Roman",serif;color:var(--accent);letter-spacing:.01em}
  .year-tag{font-size:9px;letter-spacing:.24em;color:var(--muted);text-transform:uppercase;
    align-self:flex-end;padding-bottom:3px}
  .year-stat{margin-left:auto;text-align:right;font-size:11px;color:var(--muted);line-height:1.35}
  .year-stat b{display:block;font-size:13px;color:var(--ink);font-weight:650}
  /* 月份分隔 */
  .month-group{margin-bottom:20px}
  /* 月份头吸顶：长列表滚动时始终知道自己在哪一个月 */
  .month-head{position:sticky;top:8px;z-index:6;display:flex;align-items:center;gap:10px;
    margin-bottom:12px;padding:6px 11px;border-radius:12px;
    background:var(--glass-strong);border:1px solid var(--glass-outline);
    backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 5px 16px rgba(96,74,52,.10)}
  .month-num{font-size:13px;font-weight:700;color:var(--ink);background:var(--glass-strong);
    border:1px solid var(--glass-edge);border-radius:14px;padding:3px 12px;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 3px 10px rgba(96,74,52,.06)}
  .month-rule{flex:1;height:1px;background:linear-gradient(90deg,var(--line),rgba(233,223,211,0))}
  .month-cnt{font-size:11px;color:var(--muted)}
  .month-items{position:relative;margin-left:8px;padding-left:22px;border-left:2px solid #ded0c0}
  /* 票条目圆点 */
  .slot{position:relative;margin-bottom:14px}
  .slot::before{content:"";position:absolute;left:-25px;top:26px;width:10px;height:10px;border-radius:50%;
    background:var(--accent);box-shadow:0 0 0 3px var(--accent-soft);z-index:1}
  .month-items .slot::before{left:-28px}
  .slot.pending::before{background:var(--pending);box-shadow:0 0 0 3px #f3e8d2}
  .slot.guess::before{background:#8a7fc9;box-shadow:0 0 0 3px #eae7f5}
  .slot.guess details.ticket{border:1px dashed rgba(169,157,214,.85);
    background:linear-gradient(180deg,rgba(250,249,255,.80),rgba(255,255,255,.66) 60px)}
  .guess-flag{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;
    color:#6b5fb0;background:rgba(238,235,250,.8);border:1px solid rgba(255,255,255,.85);border-radius:9px;padding:1px 7px;margin-left:6px}
  .guess-bar{font-size:11px;color:#6b5fb0;background:rgba(246,244,253,.72);border:1px dashed rgba(169,157,214,.6);
    border-radius:9px;padding:7px 10px;margin:9px 0 2px;line-height:1.6;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur)}
  .guess-bar b{color:#4c4288}
  .guess-acts{display:flex;gap:8px;margin-top:7px;flex-wrap:wrap}
  .guess-btn{font:inherit;font-size:11px;padding:4px 10px;border:1px solid #b9aee0;background:#fff;
    color:#5b4fa3;border-radius:6px;cursor:pointer}
  .guess-btn:hover{background:#efecfb}
  .guess-btn.dismiss{color:var(--muted);border-color:var(--line)}
  .city-group{margin-bottom:22px}
  .city-head{display:flex;align-items:center;gap:9px;margin:0 0 10px}
  .city-name{font-size:13px;font-weight:700;color:var(--pending);background:rgba(248,239,225,.82);
    border:1px solid var(--glass-edge);border-radius:14px;padding:3px 12px;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur)}
  .city-rule{flex:1;height:1px;background:linear-gradient(90deg,#e8dcc8,rgba(232,220,200,0))}
  .city-cnt{font-size:11px;color:var(--muted)}
  .city-items{position:relative;margin-left:8px;padding-left:22px;border-left:2px solid #e8dcc8}
  /* 行程串联：交通往返插在门票两头 */
  .journey-strip{margin:2px 0 14px 8px;padding:10px 13px;
    background:linear-gradient(100deg,rgba(233,244,250,.95),rgba(251,253,255,.92) 72%);
    border:1px solid #cfdfe9;border-left:4px solid #6b93b0;border-radius:11px;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 4px 14px rgba(96,74,52,.07)}
  .journey-row{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-size:12px;line-height:1.5}
  .journey-row + .journey-row{margin-top:8px;padding-top:8px;border-top:1px dashed #d6e3ec}
  .journey-tag{font-size:10px;font-weight:700;color:#4e7390;background:#dcebf4;border-radius:8px;padding:1px 8px;flex:none}
  .journey-node{display:inline-flex;flex-direction:column;align-items:flex-start;gap:2px;max-width:280px;
    background:#fff;border:1px solid #d6e3ec;border-radius:7px;padding:4px 9px;color:var(--ink)}
  .journey-node.trans{border-color:#a9c6da;background:#f4fafe}
  .journey-node.stay-node{border-color:#d8c9e8;background:#faf6fd}
  .jn-main{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;max-width:100%}
  .jn-sub{font-size:10px;color:#6b8296;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
  .journey-node .role{font-size:10px;font-weight:700;padding:0 5px;border-radius:6px;color:#fff;flex:none}
  .journey-node .role.out{background:#5c8f6f}
  .journey-node .role.ret{background:#b0705a}
  .journey-node .role.local{background:#8aa0b0}
  .journey-arrow{color:#8aa0b0;font-size:13px;flex:none}
  .journey-route{font-size:11px;color:#4e7390}
  .journey-row.seg{align-items:flex-start;margin-top:4px;padding-top:5px;border-top:1px dashed #e3eaf0}
  .seg-label{font-size:10px;font-weight:700;color:#fff;border-radius:8px;padding:2px 9px;flex:none;margin-top:4px}
  .seg-label.out{background:#5c8f6f}
  .seg-label.mid{background:#8aa0b0}
  .seg-label.ret{background:#b0705a}
  .journey-node.spot{background:#fffaf3;border-color:#e8d5bb}
  .journey-node.spot .t-date{color:#a07b4e}
  /* 纵向行程节点：去程 → 门票/住宿 → 返程 */
  .flow-node{display:flex;align-items:flex-start;gap:9px;margin:0 0 10px;padding:8px 11px;
    border-radius:11px;border:1px solid #cfdfe9;border-left:4px solid #6b93b0;
    background:linear-gradient(100deg,rgba(240,248,252,.96),rgba(252,254,255,.94));
    box-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 3px 10px rgba(96,74,52,.055)}
  .flow-node.ret{border-color:#ead6ce;border-left-color:#b0705a;background:linear-gradient(100deg,rgba(253,244,240,.96),rgba(255,253,252,.94))}
  .flow-node.local{border-left-color:#8aa0b0}
  .flow-node.stay{border-color:#ded0ec;border-left-color:#8a6ba8;background:linear-gradient(100deg,rgba(249,244,253,.96),rgba(255,253,255,.94))}
  .flow-node .fn-badge{flex:none;font-size:10px;font-weight:700;color:#fff;background:#5c8f6f;
    border-radius:6px;padding:2px 7px;margin-top:1px}
  .flow-node.ret .fn-badge{background:#b0705a}
  .flow-node.local .fn-badge{background:#8aa0b0}
  .flow-node.stay .fn-badge{background:#8a6ba8}
  .flow-node .fn-title{font-size:13px;font-weight:600;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
  .flow-node .fn-date{font-size:11px;font-weight:400;color:#4f6a7e}
  .flow-node .fn-sub{font-size:11px;color:#536c80;margin-top:1px}
  /* 一段完整往返与相邻内容之间的轻分隔，避免两段行程视觉连成一条 */
  .flow-gap{height:0;margin:0}
  .flow-gap.round{margin:14px 0 20px;border-top:0;position:relative;
    background:linear-gradient(90deg,rgba(150,175,195,.42) 0 38%,transparent 38% 62%,rgba(150,175,195,.42) 62% 100%) top center/100% 1px no-repeat}
  .flow-gap.round::after{content:"";position:absolute;left:50%;top:-3px;width:7px;height:7px;
    transform:translateX(-50%);border-radius:50%;background:var(--glass-strong);
    border:1px solid rgba(150,175,195,.6);box-shadow:0 2px 7px rgba(96,74,52,.12)}
  .flow-gap.soft{margin:8px 0 6px}
  .role.stay{background:#8a6ba8}
  .t-date{font-variant-numeric:tabular-nums;color:#4e7390;font-size:11px;margin-right:2px}
  .slot.transport-entry{display:none}
  body.show-transport .slot.transport-entry{display:block}
  details.ticket{background:var(--glass);border:1px solid var(--glass-outline);border-radius:15px;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.95),var(--glass-shadow);
    transition:border-color .2s,box-shadow .2s}
  details.ticket:hover{box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 14px 34px rgba(96,74,52,.13)}
  details.ticket[open]{border-color:rgba(220,199,178,.95);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 12px 30px rgba(96,74,52,.11)}
  summary{display:flex;align-items:center;gap:14px;padding:12px 16px;cursor:pointer;list-style:none;user-select:none}
  summary::-webkit-details-marker{display:none}
  summary:hover{background:rgba(255,255,255,.42);border-radius:15px}
  .thumb{width:76px;height:50px;flex:none;border-radius:7px;overflow:hidden;
    border:1px solid var(--glass-edge);background:rgba(255,255,255,.5);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.8),0 2px 8px rgba(96,74,52,.07)}
  .thumb img{width:100%;height:100%;object-fit:cover;display:block}
  .sum-main{flex:1;min-width:0}
  .sum-title{font-size:15px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .sum-meta{font-size:12px;color:#6d6155;margin-top:2px}
  .sum-meta .todo{color:var(--pending);font-weight:600}
  .sum-meta .role{font-size:10px;font-weight:700;padding:1px 6px;border-radius:6px;color:#fff}
  .sum-meta .role.out{background:#5c8f6f}
  .sum-meta .role.ret{background:#b0705a}
  .sum-meta .role.local{background:#8aa0b0}
  .sum-right{text-align:right;flex:none}
  .chev{color:var(--muted);font-size:12px;transition:transform .2s;margin-left:8px;display:inline-block}
  details[open] .chev{transform:rotate(180deg)}
  .detail{padding:0 16px 16px;border-top:1px dashed var(--line)}
  .detail .full{width:100%;border-radius:8px;margin:14px 0 6px;display:block;border:1px solid var(--line);cursor:zoom-in}
  .sides{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:14px 0 6px}
  .side{position:relative}
  .side-label{position:absolute;top:8px;left:8px;background:rgba(43,37,32,.78);color:#fff;
    font-size:11px;padding:3px 9px;border-radius:12px;pointer-events:none}
  .side img{width:100%;border-radius:8px;display:block;border:1px solid var(--line);cursor:zoom-in}
  .place{font-size:12px;color:var(--muted);margin:12px 0 10px}
  .place .pin{color:var(--accent);margin-right:4px}
  .info{display:grid;grid-template-columns:1fr 1fr;gap:9px 18px;margin:0}
  .info div{border-top:1px dashed var(--line);padding-top:7px}
  .info dt{font-size:11px;color:var(--muted);margin-bottom:1px}
  .info dd{margin:0;font-size:13px;font-weight:500;word-break:break-all}
  .note{grid-column:1/-1;font-size:11px;color:var(--muted);border-top:1px dashed var(--line);padding-top:9px}
  .supp{margin-top:14px;padding:12px 14px;background:rgba(253,248,242,.68);
    border:1px dashed rgba(220,199,178,.9);border-radius:11px;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur)}
  .supp h4{margin:0 0 9px;font-size:12px;color:var(--accent);font-weight:600}
  .supp-row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}
  .supp label{font-size:11px;color:var(--muted);display:block;margin-bottom:3px}
  .supp input,.supp textarea{font:inherit;font-size:13px;width:100%;padding:6px 9px;border:1px solid var(--line);
    border-radius:7px;background:rgba(255,255,255,.8);color:var(--ink);
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur)}
  .supp textarea{min-height:52px;resize:vertical}
  .supp .col{flex:1;min-width:150px}
  .supp .saved{font-size:11px;color:var(--pending);margin-left:8px;opacity:0;transition:opacity .2s}
  .supp .saved.show{opacity:1}
  .supp-src{font-size:10px;color:var(--muted);margin-top:6px}
  .mapbox{border:1px solid var(--glass-edge);border-radius:15px;overflow:hidden;background:var(--glass);
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.9),var(--glass-shadow)}
  #map{width:100%;height:400px}
  .maphint{padding:10px 14px;font-size:11px;color:var(--muted);border-top:1px solid var(--line)}
  footer{text-align:center;color:var(--muted);font-size:11px;margin-top:36px;line-height:1.9}
  /* 滚动定位：常驻年月 + 年份跳转 + 回顶，长列表不会滑着滑着迷路 */
  .nav-dock{position:fixed;right:18px;top:18px;z-index:30;display:none;flex-direction:column;align-items:flex-end;gap:8px}
  .nav-dock.show{display:flex}
  .nav-now{font:inherit;font-size:12px;font-weight:700;padding:7px 13px;border-radius:20px;cursor:pointer;
    color:var(--ink);background:var(--glass-strong);border:1px solid var(--glass-outline);
    backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 6px 20px rgba(96,74,52,.14);
    display:flex;align-items:center;gap:7px}
  .nav-now .nav-caret{font-size:9px;color:var(--muted);transition:transform .18s}
  .nav-dock.open .nav-caret{transform:rotate(180deg)}
  .nav-panel{display:none;flex-wrap:wrap;justify-content:flex-end;gap:6px;max-width:260px;
    padding:10px;border-radius:14px;background:var(--glass-strong);
    border:1px solid var(--glass-outline);
    backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
    box-shadow:0 12px 30px rgba(96,74,52,.18)}
  .nav-dock.open .nav-panel{display:flex}
  .nav-year{font:inherit;font-size:11px;padding:5px 10px;border-radius:8px;cursor:pointer;
    border:1px solid var(--glass-outline);background:rgba(255,255,255,.78);color:var(--ink)}
  .nav-year:hover,.nav-year.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .to-top{position:fixed;right:18px;bottom:20px;z-index:30;display:none;
    width:40px;height:40px;border-radius:50%;cursor:pointer;font-size:17px;line-height:1;
    color:var(--ink);background:var(--glass-strong);border:1px solid var(--glass-outline);
    backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
    box-shadow:0 6px 20px rgba(96,74,52,.16)}
  .to-top.show{display:block}
  @media(max-width:640px){
    .nav-dock{right:10px;top:10px}
    .nav-now{font-size:11px;padding:6px 11px}
    .nav-panel{max-width:200px}
    .to-top{right:12px;bottom:14px;width:38px;height:38px}
  }
  #lightbox{display:none;position:fixed;inset:0;background:rgba(36,29,23,.72);z-index:99;
    backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
    align-items:center;justify-content:center;padding:20px;cursor:zoom-out}
  #lightbox img{max-width:100%;max-height:90vh;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.35)}
  #modal{display:none;position:fixed;inset:0;background:rgba(36,29,23,.42);z-index:100;
    backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
    align-items:center;justify-content:center;padding:20px}
  .modal-box{background:rgba(255,253,250,.88);border:1px solid var(--glass-edge);border-radius:18px;padding:22px;max-width:560px;width:100%;
    backdrop-filter:var(--glass-blur);-webkit-backdrop-filter:var(--glass-blur);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 24px 60px rgba(0,0,0,.22)}
  .modal-box h3{margin:0 0 6px;font-size:16px}
  .modal-box p{margin:0 0 12px;font-size:12px;color:var(--muted)}
  .modal-box textarea{width:100%;min-height:180px;font:12px/1.5 monospace;padding:10px;
    border:1px solid var(--line);border-radius:8px;background:rgba(255,255,255,.85);color:var(--ink)}
  .modal-box .acts{display:flex;gap:8px;justify-content:flex-end;margin-top:12px}
  @media(max-width:640px){
    .wrap{padding:28px 14px 56px} h1{font-size:25px}
    .stats{grid-template-columns:repeat(2,1fr)}
    .info{grid-template-columns:1fr}
    .sum-title{font-size:13px}
    .year-num{font-size:26px}
    .year-head{padding:9px 12px;gap:9px}
    .year-tag{display:none}
    .toolbar{justify-content:center}
    .month-head{top:4px;padding:5px 8px}
    .month-items{padding-left:16px;margin-left:6px}
    .month-items .slot::before{left:-22px}
    #map{height:320px}
    .flow-node,.journey-strip,.guess-bar,.supp,.supp input,.supp textarea{backdrop-filter:none;-webkit-backdrop-filter:none}
    .flow-node{background:linear-gradient(100deg,rgba(240,248,252,.94),rgba(252,254,255,.90))}
    .flow-node.ret{background:linear-gradient(100deg,rgba(253,244,240,.94),rgba(255,253,252,.90))}
    .flow-node.stay{background:linear-gradient(100deg,rgba(249,244,253,.94),rgba(255,253,255,.90))}
  }
</style>
<script type="text/javascript">
  window._TMapSecurityConfig = {
    serviceHost: 'http://127.0.0.1:__WB_HTTP_PORT__/_TMapService/_wbt/__WB_TMAP_SECRET__',
  };
</script>
<script src="https://map.qq.com/api/gljs?v=1.exp"></script>
</head>
<body>
<div class="bg-orbs" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
<div class="wrap">
  <header>
    <div class="kicker">Ticket Album</div>
    <h1>足迹票册</h1>
    <p>每一张票，都是一次到场证明</p>
  </header>

  <div class="stats">
    <div class="stat"><b>$count</b><span>张门票</span></div>
    <div class="stat"><b>$spots</b><span>处足迹</span></div>
    <div class="stat"><b>$span</b><span>时间跨度</span></div>
  </div>

  <div class="toolbar">
    <button class="btn" id="btnTransport">显示登机牌</button>
    <button class="btn" id="btnCollapseAll">全部收起</button>
    <button class="btn" id="btnExpandAll">全部展开</button>
    <button class="btn" id="btnExport">导出我的补充</button>
  </div>

  <h2>时间线 <span class="cnt" id="datedCount"></span></h2>
  <p class="hint">按年份、月份分组，年内倒序 · 航旅截图的航班/高铁/酒店按日期串成「行程串联」，与门票同轴展示 · 登机牌默认隐藏，点顶部「显示登机牌」可看原件</p>
  <div class="timeline" id="timeline"></div>

  <h2 class="pending-h">日期待补充 <span class="cnt" id="pendingCount"></span></h2>
  <p class="hint">按城市归组 · 同城/同省若有已确定日期的票，会标出「待确认」推测供核实 · 点采用或自行填写日期后自动移到时间线</p>
  <div class="timeline pending-tl" id="pendingTimeline"></div>

  <h2>足迹地图</h2>
  <div class="mapbox">
    <div id="map"></div>
    <div class="maphint">坐标依据票面景区名称匹配 · 点击地图标记可展开对应门票</div>
  </div>

  <footer>
    由门票照片自动整理生成 · 共 $count 张 · 生成于 $gen_date<br>
    票面敏感字段按原样保留，如要分享请自行检查
  </footer>
</div>

<div class="nav-dock" id="navDock">
  <button class="nav-now" id="navNow"><span id="navLabel">时间线</span><span class="nav-caret">▾</span></button>
  <div class="nav-panel" id="navPanel"></div>
</div>
<button class="to-top" id="toTop" title="回到顶部" aria-label="回到顶部">↑</button>

<div id="lightbox"><img id="lightbox-img" src=""></div>

<div id="modal">
  <div class="modal-box">
    <h3>我的补充数据</h3>
    <p>复制下面内容发给整理者，即可写回数据库。补充内容也已保存在这台设备的浏览器里。</p>
    <textarea id="exportText" readonly></textarea>
    <div class="acts">
      <button class="btn" id="btnCopy">复制</button>
      <button class="btn primary" id="btnCloseModal">关闭</button>
    </div>
  </div>
</div>

<script>
  const TICKETS = $tickets;
  const TRIPS = $trips;
  const SKEY = "ticket_album_supplements_v1";

  function loadSup(){
    try{
      var v = JSON.parse(localStorage.getItem(SKEY) || "{}");
      return (v && typeof v === "object" && !Array.isArray(v)) ? v : {};
    }catch(e){ return {}; }
  }
  function saveSup(s){
    try{ localStorage.setItem(SKEY, JSON.stringify(s)); }catch(e){}
  }

  // 补充信息三处来源合并成一份 sup：数据库优先，本机缓存补齐，页面新输入随后覆盖。
  // 旧逻辑是「库里只要有一条 user 记录就完全丢掉浏览器缓存」，用非 8765 地址
  // 打开页面时填的内容只留在本机，下次从正常地址打开就看不见了。
  var sup = {};
  var knownIds = {}, userIds = {};
  TICKETS.forEach(function(t){ knownIds[t.id] = true; });
  var localSup = loadSup();
  Object.keys(localSup).forEach(function(id){
    if(!knownIds[id]) return;                    // 已删除的票，丢弃
    var s = localSup[id];
    if(!s || typeof s !== "object") return;
    var item = {};
    if(s.date) item.date = String(s.date);
    if(s.note != null && String(s.note) !== "") item.note = String(s.note);
    if(item.date || item.note) sup[id] = item;   // 空条目不进 sup，避免写库时清空原有备注
  });
  TICKETS.forEach(function(t){
    if(t.date_source === "user"){
      userIds[t.id] = true;
      sup[t.id] = { date: t.date || "", note: t.note || "" };   // 库为准，整条覆盖
    }
  });
  saveSup(sup);                                 // 让两处始终保持一致

  // 只把「库里还没有、本机缓存里有」的补充回填数据库；服务不可用时静默留在本机
  var pending = {};
  Object.keys(sup).forEach(function(id){ if(!userIds[id]) pending[id] = sup[id]; });
  function syncSupToDb(){
    if(!Object.keys(pending).length) return;
    fetch("/api/supplement", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(pending)
    }).then(function(r){ return r.json(); }).then(function(res){
      if(!res || !res.ok) return;
      Object.keys(pending).forEach(function(id){
        var tag = document.getElementById("saved-" + id);
        if(tag){
          tag.textContent = "已同步到数据库 ✓";
          tag.classList.add("show");
          setTimeout(function(){ tag.classList.remove("show"); }, 2200);
        }
      });
    }).catch(function(){});
  }
  if(Object.keys(pending).length) setTimeout(syncSupToDb, 800);

  const timeline = document.getElementById("timeline");
  const pendingTimeline = document.getElementById("pendingTimeline");

  function effDateOf(t){
    const s = sup[t.id] || {};
    return s.date || (t.date_label && t.date_label!=="日期待补充" ? t.date_label : "");
  }
  function normCity(s){ return (s||"").replace(/（.*?）/g,"").replace(/[市区县]/g,"").trim(); }
  // 为无日期票找同期参考：同城精确 > 同省，取有 dates 的票
  function guessFor(t){
    if(effDateOf(t)) return null;
    var c = normCity(t.city), p = t.province;
    // 优先级1：同城行程记录（酒店入住 / 火车乘车），来自航旅纵横截图，可信度较高
    var cityTrips = (typeof TRIPS!=="undefined" ? TRIPS : []).filter(function(x){
      return c && normCity(x.city)===c && x.date;
    });
    if(cityTrips.length){
      // 酒店优先，其次火车；取最近的一条
      cityTrips.sort(function(a,b){
        var ka = a.kind==="hotel"?0:1, kb = b.kind==="hotel"?0:1;
        if(ka!==kb) return ka-kb;
        return (b.date||"").localeCompare(a.date||"");
      });
      var gt = cityTrips[0];
      var gLabel = gt.date.replace(/-/g,".");
      var gKind = gt.kind==="hotel" ? "酒店入住" : (gt.kind==="train" ? "火车乘车" : "航班");
      return {date:gLabel, reason:"同城行程 · " + gKind + "「" + gt.name + "」" + gLabel + "（航旅截图，待核实）", trip:gt};
    }
    // 优先级2：同城有日期的票
    var dated = TICKETS.filter(function(x){ return x.id!==t.id && !!effDateOf(x); });
    if(!dated.length) return null;
    var sameCity = dated.filter(function(x){ return c && normCity(x.city)===c; });
    if(sameCity.length) return {t:sameCity[0], reason:"同城 · " + (t.city||c)};
    var sameProv = dated.filter(function(x){ return p && x.province===p; });
    if(sameProv.length) return {t:sameProv[0], reason:"同省 · " + p + "（不同城市，仅作参考）"};
    return null;
  }
  function normalizeDate(s){ return (s||"").replace(/\./g,"-"); }
  // 只精确到月的日期（票面/记忆只能给到月份）
  function isMonthOnly(s){ return /^[0-9]{4}-[0-9]{1,2}$$/.test(normalizeDate(s||"").trim()); }
  function fmtDate(s){
    var d = normalizeDate(s||"").trim();
    return /^[0-9]{4}-[0-9]{1,2}$$/.test(d) ? d.replace(/-/g,".") : (s||"").replace(/-/g,".");
  }
  // ---- 交通与行程串联 ----
  var HOME_CACHE = null;  // 全局常驻城市（上海），跨月缓存
  function isTransport(t){ return Number(t.transport||0) === 1; }
  function transIcon(t){
    var m = t.transport_mode || "";
    if(/飞机|航班|登机/.test(m)) return "✈";
    if(/火车|高铁|动车|铁路/.test(m)) return "🚄";
    if(/汽车|大巴|直通|客运/.test(m)) return "🚌";
    if(/轮渡|船/.test(m)) return "⛴";
    return "➜";
  }
  function transRole(t){
    var m = t.transport_mode || "";
    if(/酒店|住宿|宾馆/.test(m)) return {k:"stay", label:"住宿"};
    var from = t.transport_from || "", to = t.transport_to || "", c = t.city || "";
    if(c && to.indexOf(c)>=0) return {k:"out", label:"去程"};
    if(c && from.indexOf(c)>=0) return {k:"ret", label:"返程"};
    if(/返|回/.test(t.name||"")) return {k:"ret", label:"返程"};
    return {k:"local", label:"途经"};
  }
  // 行程节点：来自航旅纵横截图的航班/高铁/酒店，按日期与门票同轴串联
  function tripIcon(kind){
    if(kind==="flight") return "✈";
    if(kind==="train") return "🚄";
    if(kind==="hotel") return "🏨";
    return "➜";
  }
  function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
  function daysBetween(a,b){
    if(!a || !b) return 0;
    var da = new Date(a + "T00:00:00"), db = new Date(b + "T00:00:00");
    if(isNaN(da) || isNaN(db)) return 0;
    return Math.abs(db - da) / 86400000;
  }
  // 站点名归一（上海虹桥→上海、潍坊北→潍坊），用于判断「回到出发城市」
  function normCity(s){
    var t = String(s||"").replace(/\s+/g,"");
    if(t.slice(-1) === "站") t = t.slice(0,-1);
    ["虹桥","浦东","机场"].forEach(function(k){
      if(t.length > k.length && t.slice(-k.length) === k) t = t.slice(0,-k.length);
    });
    if(t.length > 2 && "东南西北".indexOf(t.slice(-1)) >= 0) t = t.slice(0,-1);
    return t;
  }
  function citySame(a,b){
    if(!a || !b) return false;
    return a.indexOf(b) === 0 || b.indexOf(a) === 0;
  }
  function tripCities(x){
    var d = String(x.detail||"");
    var m = d.match(/^(.+?)\d{1,2}:\d{2}\s*→\s*(.+?)\d{1,2}:\d{2}/);
    if(!m) m = d.match(/^(.+?)\s*→\s*(.+)/);  // 票卡只有城市没有时刻
    if(!m) return null;
    return {from:normCity(m[1]), to:normCity(m[2])};
  }
  function tripTime(x){
    var m = String(x.detail||"").match(/(\d{1,2}):(\d{2})/);
    return m ? (("0"+m[1]).slice(-2) + ":" + m[2]) : "";
  }
  // 当月「常驻城市」：出现次数最多的城市，用来判断哪一头算回家
  function homeCityOf(arr){
    var cnt = {};
    arr.forEach(function(x){
      var c = tripCities(x); if(!c) return;
      if(c.from) cnt[c.from] = (cnt[c.from]||0) + 1;
      if(c.to) cnt[c.to] = (cnt[c.to]||0) + 1;
    });
    var best = "", n = 0;
    Object.keys(cnt).forEach(function(k){ if(cnt[k] > n){ best = k; n = cnt[k]; } });
    return n >= 2 ? best : "";
  }
  // 一次往返 = 从 A 出发，最后又回到 A；中间换乘（如潍坊→青岛机场）只算「途经」
  function pairTrips(arr, home){
    var used = {};
    arr.forEach(function(x){ x._pk = ""; x._plabel = ""; });
    for(var i=0;i<arr.length;i++){
      if(used[i]) continue;
      var a = arr[i], ca = tripCities(a);
      if(!ca) continue;
      for(var j=i+1;j<arr.length;j++){
        var b = arr[j], cb = tripCities(b);
        if(!cb) continue;
        if(daysBetween(normalizeDate(a.date), normalizeDate(b.date)) > 6) break;
        if(citySame(ca.from, cb.to)){
          a._pk = "out"; a._plabel = "去程";
          b._pk = "ret"; b._plabel = "返程";
          used[i] = used[j] = true;
          for(var k=i+1;k<j;k++){
            if(!used[k]){ arr[k]._pk = "local"; arr[k]._plabel = "途经"; used[k] = true; }
          }
          break;
        }
      }
    }
    // 没配上的：按「离开常驻地/回到常驻地」兜底
    arr.forEach(function(x){
      if(x._pk || !home) return;
      var c = tripCities(x); if(!c) return;
      if(citySame(c.from, home)){ x._pk = "out"; x._plabel = "去程"; }
      else if(citySame(c.to, home)){ x._pk = "ret"; x._plabel = "返程"; }
    });
  }
  function tripRoute(x){
    var d = x.detail || "";
    var m = d.match(/^(.+?)\d{1,2}:\d{2}\s*→\s*(.+?)\d{1,2}:\d{2}/);
    if(m) return {from:m[1].trim(), to:m[2].trim(), raw:d};
    return {from:"", to:"", raw:d};
  }
  function tripRole(trip, monthTickets, transTrips){
    if(trip.kind==="hotel") return {k:"stay", label:"住宿"};
    var d = normalizeDate(trip.date);
    var ds = monthTickets.map(function(x){ return normalizeDate(x.dateOf||""); }).filter(Boolean).sort();
    if(ds.length && d){
      if(d < ds[0]) return {k:"out", label:"去程"};
      if(d > ds[ds.length-1]) return {k:"ret", label:"返程"};
    }
    var arr = transTrips || [];
    if(arr.length >= 2){
      var i = arr.indexOf(trip);
      if(i === 0) return {k:"out", label:"去程"};
      if(i === arr.length-1) return {k:"ret", label:"返程"};
    }
    if(arr.length === 1) return {k:"out", label:"去程"};
    return {k:"local", label:"途经"};
  }
  // ---- 跨月行程链 ----
  // 一次行程 = 从常驻城市出发，逐段「上一段终点 = 下一段起点」接续，回到常驻城市收口。
  // 中间可能跨月（9.27 上海→曼谷→哥本哈根，10.7 哥本哈根→阿姆斯特丹→上海），
  // 整条链算一个行程、统一落在最后一段所在的月份，不再被月份切成两段假的往返。
  var JOURNEYS = null;
  function buildJourneys(){
    if(JOURNEYS) return JOURNEYS;
    var home = HOME_CACHE || "上海";
    var arr = (typeof TRIPS!=="undefined" ? TRIPS : []).filter(function(x){ return x.kind!=="hotel"; })
      .slice().sort(function(a,b){
        var c = normalizeDate(a.date).localeCompare(normalizeDate(b.date));
        if(c) return c;
        return tripTime(a).localeCompare(tripTime(b));
      });
    var map = {}, seq = 0, open = null;
    arr.forEach(function(x){
      x._jid = ""; x._jr = ""; x._jlabel = "";
      var c = tripCities(x); if(!c) return;
      var f = c.from, t = c.to, d = normalizeDate(x.date);
      if(open && citySame(open.tail, f) && daysBetween(open.last, d) <= 21){
        x._jid = open.id;
        open.last = d; open.tail = t;
        map[open.id].legs.push(x);
        if(citySame(t, home)){ x._jr = "ret"; x._jlabel = "返程"; open = null; }
        else { x._jr = "via"; x._jlabel = "途经"; }
        return;
      }
      open = null;
      if(citySame(f, home)){
        seq++;
        x._jid = "j" + seq; x._jr = "out"; x._jlabel = "去程";
        open = {id:x._jid, tail:t, last:d};
        map[x._jid] = {id:x._jid, legs:[x]};
      }else if(citySame(t, home)){
        seq++;
        x._jid = "j" + seq; x._jr = "ret"; x._jlabel = "返程";
        map[x._jid] = {id:x._jid, legs:[x]};
      }
    });
    Object.keys(map).forEach(function(k){
      var j = map[k], legs = j.legs;
      j.first = normalizeDate(legs[0].date);
      j.last = normalizeDate(legs[legs.length-1].date);
      j.anchor = j.last.slice(0,7);   // 整段行程落在最后一段（返程）所在月
      j.route = [];
      legs.forEach(function(x){
        var c = tripCities(x);
        if(c && c.from && j.route.indexOf(c.from) < 0) j.route.push(c.from);
      });
      var lc = tripCities(legs[legs.length-1]);
      if(lc && lc.to) j.route.push(lc.to);
    });
    JOURNEYS = {list:arr, map:map};
    return JOURNEYS;
  }
  function buildJourneyStrip(monthItems){
    if(HOME_CACHE === null){
      HOME_CACHE = homeCityOf((typeof TRIPS!=="undefined" ? TRIPS : []).filter(function(x){ return x.kind!=="hotel"; }));
      if(!HOME_CACHE) HOME_CACHE = "上海";
    }
    var J = buildJourneys();
    var mg = monthItems.parentNode;
    var ym = mg.closest(".year-block").dataset.year + "-" + mg.dataset.month;
    // 属于某个行程的交通段跟着行程走（落在返程月），其余按自己的月份归位
    var trips = (typeof TRIPS!=="undefined" ? TRIPS : []).filter(function(x){
      if(x.kind === "hotel") return (x.date||"").indexOf(ym)===0;
      var j = (x._jid && J.map[x._jid]) ? J.map[x._jid] : null;
      if(j) return j.anchor === ym;
      return (x.date||"").indexOf(ym)===0;
    });
    var slots = Array.prototype.slice.call(monthItems.querySelectorAll(".slot:not(.transport-entry)"));
    // 同日多段交通按实际发车/起飞时刻排序，否则「上海→青岛、青岛→潍坊」会被当成一次往返
    var transTrips = trips.filter(function(x){ return x.kind!=="hotel"; })
      .sort(function(a,b){
        var c = normalizeDate(a.date).localeCompare(normalizeDate(b.date));
        if(c) return c;
        return tripTime(a).localeCompare(tripTime(b));
      });
    // 登机牌/高铁票卡片默认隐藏，但往返交通信息本身仍进入时间线
    var extra = [], extraSeen = {};
    Array.prototype.slice.call(monthItems.querySelectorAll(".slot.transport-entry")).forEach(function(s){
      if(!/✈|🚄/.test(s.dataset.icon||"")) return;  // 只展示机票与高铁，地铁/直通车等仍隐藏
      var d = normalizeDate(s.dataset.date||"");
      if(!d) return;
      var raw = s.dataset.short || "";
      var m = raw.match(/([A-Z]{1,2}\d{2,6})/);
      var nm = m ? m[1] : raw;
      var from = s.dataset.from||"", to = s.dataset.to||"";
      var cd0 = tripCities({detail: from + " → " + to});
      // 和航旅记录去重：先认航班号，再认「同一天 + 同一对城市」，
      // 这样票面没印航班号的登机牌（如郑州新郑·登机牌）也不会把返程写第二遍
      var dup = (m && J.list.some(function(x){
        return normalizeDate(x.date)===d && (x.name||"").indexOf(m[1])>=0;
      })) || (cd0 && J.list.some(function(x){
        if(normalizeDate(x.date)!==d) return false;
        var c = tripCities(x);
        return !!c && citySame(c.from, cd0.from) && citySame(c.to, cd0.to);
      }));
      if(dup) return;
      if(cd0){
        var key = d + "|" + cd0.from + "|" + cd0.to;
        if(extraSeen[key]) return;   // 同一段路的多张票卡只留一个节点
        extraSeen[key] = 1;
      }
      var role = s.dataset.role||"途经", rolek = s.dataset.rolek||"local";
      var cd = cd0;
      if(cd && HOME_CACHE){
        // 票卡自带的去程/返程标记不一定对，按「离开/回到常驻地」校正
        if(citySame(cd.to, HOME_CACHE)){ role = "返程"; rolek = "ret"; }
        else if(citySame(cd.from, HOME_CACHE)){ role = "去程"; rolek = "out"; }
      }
      extra.push({date:d, kind:"trans-ticket", data:{
        date:d, name:nm||"交通", detail:(from ? from + " → " : "") + to,
        role:role, rolek:rolek, icon:s.dataset.icon
      }});
    });
    if(!trips.length && !extra.length) return;  // 当月无行程记录则不显示行程条
    mg.dataset.trips = trips.length + extra.length;
    // 门票按日期
    var tickets = slots.map(function(s){
      return {dateOf:s.dataset.date, short:s.dataset.short||"门票"};
    });
    // 全部节点按日期正序
    var nodes = [];
    trips.forEach(function(x){ nodes.push({date:normalizeDate(x.date), kind:"trip", data:x}); });
    tickets.forEach(function(x){ if(x.dateOf) nodes.push({date:normalizeDate(x.dateOf), kind:"ticket", data:x}); });
    extra.forEach(function(x){ nodes.push(x); });
    nodes.sort(function(a,b){
      var c = a.date.localeCompare(b.date);
      if(c) return c;
      // 同日：保持行程节点在前
      return a.kind==="trip" ? -1 : (b.kind==="trip" ? 1 : 0);
    });
    // 标记每个节点的角色：优先用跨月行程链（去程 → 途经… → 返程），配不上再回退到月份内推断
    pairTrips(transTrips, HOME_CACHE);
    nodes.forEach(function(n){
      if(n.kind==="trip"){
        var x = n.data;
        if(x.kind === "hotel"){
          var rh = tripRole(x, tickets, transTrips);
          n.roleK = rh.k; n.roleLabel = rh.label;
        }else if(x._jr){
          n.roleK = x._jr === "via" ? "local" : x._jr;
          n.roleLabel = x._jlabel;
          n.jid = x._jid;
        }else if(x._pk){
          n.roleK = x._pk; n.roleLabel = x._plabel;
        }else{
          var r = tripRole(x, tickets, transTrips);
          n.roleK = r.k; n.roleLabel = r.label;
        }
      }else if(n.kind==="trans-ticket"){
        n.roleK = n.data.rolek; n.roleLabel = n.data.role;
      }else{
        n.roleK = "spot"; n.roleLabel = "";
      }
    });
    // 纵向铺进整条时间线：去程在最前，返程在最后，门票与住宿按日期夹在中间
    function flowEl(n){
      var badge = "", title = "", sub = "", cls = "local", day = n.date.slice(5).replace("-",".");
      if(n.kind==="trip"){
        var x = n.data;
        if(x.kind==="hotel"){
          cls = "stay"; badge = "住宿"; title = "🏨 " + (x.name||"住宿");
          var nights = (x.detail||"").match(/共(\d+)晚/);
          sub = "入住 " + day + (x.date_end ? " · 离店 " + x.date_end.slice(5).replace("-",".") : "") +
                (nights ? " · " + nights[1] + " 晚" : "");
        }else{
          cls = n.roleK; badge = n.roleLabel || "交通";
          title = tripIcon(x.kind) + " " + (x.name||"");
          sub = (x.detail||"").replace(/\s+/g," ");
        }
      }else{
        cls = n.data.rolek || "local"; badge = n.data.role || "交通";
        title = n.data.icon + " " + (n.data.name||"");
        sub = n.data.detail || "";
      }
      var el = document.createElement("div");
      el.className = "flow-node " + cls;
      el.dataset.date = n.date;
      el.dataset.rolek = cls;
      if(n.jid) el.dataset.jid = n.jid;
      el.dataset.at = (n.kind==="trip" ? tripTime(n.data) : tripTime({detail:sub}));
      el.innerHTML = '<span class="fn-badge">' + esc(badge) + '</span>' +
        '<div class="fn-body"><div class="fn-title">' + esc(title) +
        '<span class="fn-date">' + day + '</span></div>' +
        (sub ? '<div class="fn-sub">' + esc(sub) + '</div>' : '') + '</div>';
      monthItems.appendChild(el);
    }
    // 门票本身已有卡片，不再重复生成节点；重排前先清掉上一轮生成的分隔
    Array.prototype.slice.call(monthItems.querySelectorAll(".flow-node,.flow-gap"))
      .forEach(function(el){ el.remove(); });
    nodes.forEach(function(n){ if(n.kind!=="ticket") flowEl(n); });

    // 月内条目（行程节点 + 门票卡片）：先按时间正序排好
    // 隐藏的交通票卡只是原始凭证，不参与往返分组（否则它自带的「返程」标记会切错块）
    var hiddenSlips = Array.prototype.slice.call(monthItems.querySelectorAll(".slot.transport-entry"));
    var kids = Array.prototype.slice.call(monthItems.children).filter(function(el){
      return el.classList && !el.classList.contains("transport-entry") &&
        (el.classList.contains("flow-node") || el.classList.contains("slot"));
    });
    // 只有月份、没有具体日的条目先摘出来：它们不参与按天分块，最后并入当月行程块
    var monthOnly = kids.filter(function(el){ return isMonthOnly(el.dataset.date||""); });
    kids = kids.filter(function(el){ return !isMonthOnly(el.dataset.date||""); });
    kids.sort(function(a,b){
      var c = normalizeDate(a.dataset.date||"").localeCompare(normalizeDate(b.dataset.date||""));
      if(c) return c;
      var ra = a.dataset.rolek==="out" ? 0 : 1;
      var rb = b.dataset.rolek==="out" ? 0 : 1;
      if(ra !== rb) return ra - rb;
      // 同日按出发时刻；没有时刻的（住宿）排在当天最前
      var ta = a.dataset.at||"", tb = b.dataset.at||"";
      if(!ta && tb) return -1;
      if(ta && !tb) return 1;
      return ta.localeCompare(tb);
    });
    // 识别完整往返块：一个「去程」起头，遇到「返程」收口；
    // 不属于任何往返的条目（如单独一晚住宿）按自身日期独立成块，不再硬塞进交通中间
    var blocks = [], cur = null, lastD = "";
    kids.forEach(function(el){
      var rk = el.dataset.rolek || "";
      var d = normalizeDate(el.dataset.date||"");
      var jid = el.dataset.jid || "";
      if(rk === "out"){
        cur = {items:[el], open:true, jid:jid}; blocks.push(cur); lastD = d; return;
      }
      if(rk === "ret"){
        if(cur && cur.open && (!jid || !cur.jid || jid === cur.jid)){
          cur.items.push(el); cur.open = false; cur = null; return;
        }
        if(cur) cur.open = false;
        cur = null;
        blocks.push({items:[el], open:false}); return;
      }
      // 同一行程的中间段不论隔几天都留在块里（如欧洲行中途住了 9 天）
      if(cur && cur.open && ((jid && cur.jid && jid === cur.jid) ||
          (!lastD || !d || daysBetween(lastD, d) <= 8))){
        cur.items.push(el); if(d) lastD = d; return;
      }
      cur = null;
      blocks.push({items:[el], open:false});
    });
    // 月精度条目并入当月的行程块：有块就跟着最近的块，没有就自己成块
    monthOnly.forEach(function(el){
      var target = null;
      for(var i=blocks.length-1;i>=0;i--){
        if(blocks[i].items.length){ target = blocks[i]; break; }
      }
      if(target){ target.items.push(el); }
      else { blocks.push({items:[el], open:false}); }
    });
    // 倒序渲染：最新的一块在最上，块内也倒序；完整往返块之间用虚线隔开
    var isRound = function(b){
      var hasOut = b.items.some(function(el){ return el.dataset.rolek === "out"; });
      var hasRet = b.items.some(function(el){ return el.dataset.rolek === "ret"; });
      return hasOut && hasRet;
    };
    var rev = blocks.slice().reverse();
    rev.forEach(function(b, i){
      var items = b.items.slice().sort(function(x,y){
        var dx = normalizeDate(x.dataset.date||""), dy = normalizeDate(y.dataset.date||"");
        if(!isMonthOnly(dx) && !isMonthOnly(dy)){
          var c = dy.localeCompare(dx);
          if(c) return c;
        }
        // 同日倒序：返程最先、去程垫底（正序旅程的镜像）
        var rankOf = function(el){
          var r = el.dataset.rolek;
          return r === "ret" ? 2 : (r === "out" ? 0 : 1);
        };
        var rx = rankOf(x), ry = rankOf(y);
        if(rx !== ry) return ry - rx;
        var tx = x.dataset.at||"", ty = y.dataset.at||"";
        if(!tx && ty) return 1;
        if(tx && !ty) return -1;
        return ty.localeCompare(tx);
      });
      if(i > 0){
        var gap = document.createElement("div");
        // 与完整往返块相邻时隔得明显些，否则只留轻间距
        gap.className = "flow-gap" + ((isRound(b) || isRound(rev[i-1])) ? " round" : " soft");
        monthItems.appendChild(gap);
      }
      items.forEach(function(el){ monthItems.appendChild(el); });
    });
    // 默认隐藏的交通票卡统一收到月块末尾，展开时才可见
    hiddenSlips.forEach(function(el){ monthItems.appendChild(el); });
  }
  function ensureGroup(year, month){
    month = String(month == null ? "" : month);
    if(!/^[0-9]{1,2}/.test(month)) month = "00";
    month = ("0" + month).slice(-2);
    var yg = timeline.querySelector('.year-block[data-year="' + year + '"]');
    if(!yg){
      yg = document.createElement("section");
      yg.className = "year-block";
      yg.dataset.year = year;
      yg.innerHTML = '<div class="year-head"><span class="year-num">' + year +
        '</span><span class="year-tag">Year</span><span class="year-stat"></span></div>' +
        '<div class="year-body"></div>';
      timeline.appendChild(yg);
    }
    var mg = yg.querySelector('.month-group[data-month="' + month + '"]');
    if(!mg){
      mg = document.createElement("div");
      mg.className = "month-group";
      mg.dataset.month = month;
      mg.innerHTML = '<div class="month-head"><span class="month-num">' +
        parseInt(month,10) + '月</span><span class="month-rule"></span>' +
        '<span class="month-cnt"></span></div><div class="month-items"></div>';
      yg.querySelector(".year-body").appendChild(mg);
    }
    return mg.querySelector(".month-items");
  }
  function ensureCityGroup(city, prov){
    var key = city || prov || "未标注城市";
    var g = pendingTimeline.querySelector('.city-group[data-city="' + key + '"]');
    if(!g){
      g = document.createElement("section");
      g.className = "city-group";
      g.dataset.city = key;
      g.innerHTML = '<div class="city-head"><span class="city-name">' + key +
        '</span><span class="city-rule"></span><span class="city-cnt"></span></div>' +
        '<div class="city-items"></div>';
      pendingTimeline.appendChild(g);
    }
    return g.querySelector(".city-items");
  }
  function placeSlot(slot, effDate, t){
    var norm = normalizeDate(effDate);
    if(!norm){
      var city = (t && t.city) ? t.city : "";
      var prov = (t && t.province) ? t.province : "";
      var label = city ? (prov && prov!==city ? city + " · " + prov : city) : (prov || "未标注城市");
      var box = ensureCityGroup(city ? city : "", prov);
      var head = box.parentNode.querySelector(".city-name");
      if(head) head.textContent = label;
      box.appendChild(slot);
      slot.classList.add("pending");
      return;
    }
    var parts = norm.split("-");
    var y = parts[0] || "", m = parts[1] || "";
    var okYear = y.length === 4 && /^[0-9]{4}/.test(y);
    var okMonth = /^[0-9]{1,2}/.test(m) && Number(m) >= 1 && Number(m) <= 12;
    if(!okYear || !okMonth){
      // 只有年份等不完整日期先放待补区，避免出现「NaN 月」这种空分组
      var city2 = (t && t.city) ? t.city : "";
      var prov2 = (t && t.province) ? t.province : "";
      var box2 = ensureCityGroup(city2, prov2);
      var head2 = box2.parentNode.querySelector(".city-name");
      if(head2) head2.textContent = city2 ? (prov2 && prov2!==city2 ? city2 + " · " + prov2 : city2) : (prov2 || "未标注城市");
      box2.appendChild(slot);
      slot.classList.add("pending");
      return;
    }
    ensureGroup(y, m).appendChild(slot);
    slot.classList.remove("pending");
  }
  function reorder(container, selector, cmp){
    Array.prototype.slice.call(container.querySelectorAll(selector))
      .sort(cmp).forEach(function(el){ container.appendChild(el); });
  }
  function reorganize(){
    // 为「有行程但无门票」的月份也建空组，让行程能独立出现在时间线上
    (typeof TRIPS!=="undefined" ? TRIPS : []).forEach(function(x){
      if(!x.date) return;
      var p = x.date.split("-");
      if(p.length===3) ensureGroup(p[0], p[1]);
    });
    reorder(timeline, ".year-block", function(a,b){
      return b.dataset.year.localeCompare(a.dataset.year);
    });
    reorder(pendingTimeline, ".city-group", function(a,b){
      var ga = a.querySelector(".slot"), gb = b.querySelector(".slot");
      var ha = ga && ga.dataset.guess ? 1 : 0, hb = gb && gb.dataset.guess ? 1 : 0;
      if(ha !== hb) return hb - ha;  // 有推测的组排前面
      return a.dataset.city.localeCompare(b.dataset.city, "zh");
    });
    timeline.querySelectorAll(".year-block").forEach(function(yg){
      var body = yg.querySelector(".year-body");
      reorder(body, ".month-group", function(a,b){
        return Number(b.dataset.month) - Number(a.dataset.month);
      });
      body.querySelectorAll(".month-group").forEach(function(mg){
        var box = mg.querySelector(".month-items");
        reorder(box, ".slot", function(a,b){
          return normalizeDate(b.dataset.date).localeCompare(normalizeDate(a.dataset.date));
        });
        var old = mg.querySelector(".journey-strip"); if(old) old.remove();
        buildJourneyStrip(box);
      });
      // 行程整体挪到返程月后，出发月可能被搬空，收掉空月份
      body.querySelectorAll(".month-group").forEach(function(mg){
        var box = mg.querySelector(".month-items");
        if(!box) return;
        if(!box.querySelector(".slot,.flow-node")) mg.remove();
      });
      if(!body.querySelector(".month-group")) yg.remove();
    });
  }
  function refreshStats(){
    var dated = timeline.querySelectorAll(".slot:not(.transport-entry)").length;
    var tripCnt = 0;
    timeline.querySelectorAll(".month-group").forEach(function(mg){ tripCnt += Number(mg.dataset.trips || 0); });
    document.getElementById("datedCount").textContent = dated + " 张门票" +
      (tripCnt ? " · " + tripCnt + " 段行程" : "");
    var pendCnt = pendingTimeline.querySelectorAll(".slot").length;
    var guessCnt = pendingTimeline.querySelectorAll(".slot[data-guess]").length;
    document.getElementById("pendingCount").textContent = pendCnt + " 张" +
      (guessCnt ? "（含 " + guessCnt + " 张待确认推测）" : "");
    pendingTimeline.querySelectorAll(".city-group").forEach(function(g){
      var c = g.querySelectorAll(".slot").length;
      g.querySelector(".city-cnt").textContent = c + " 张";
    });
    timeline.querySelectorAll(".year-block").forEach(function(yg){
      var c = 0;
      yg.querySelectorAll(".slot:not(.transport-entry)").forEach(function(s){ c++; });
      var yTrips = 0;
      yg.querySelectorAll(".month-group").forEach(function(mg){ yTrips += Number(mg.dataset.trips || 0); });
      var st = yg.querySelector(".year-stat");
      st.innerHTML = "<b>" + c + " 张" + (yTrips ? " · " + yTrips + " 段行程" : "") +
        "</b>本年收藏";
      yg.querySelectorAll(".month-group").forEach(function(mg){
        var n = mg.querySelectorAll(".slot:not(.transport-entry)").length;
        var t = Number(mg.dataset.trips || 0);
        mg.querySelector(".month-cnt").textContent = n + " 张" + (t ? " · " + t + " 段行程" : "");
      });
    });
    refreshNav();
  }

  TICKETS.forEach(function(t){
    const s = sup[t.id] || {};
    const effDate = effDateOf(t);
    const hasDate = !!effDate;
    const guess = hasDate ? null : guessFor(t);
    const slot = document.createElement("div");
    slot.className = "slot" + (hasDate ? "" : " pending") + (guess ? " guess" : "") +
      (isTransport(t) ? " transport-entry" : "");
    slot.dataset.date = effDate;
    slot.dataset.short = t.short || t.name;
    if(isTransport(t)){
      slot.dataset.transport = "1";
      slot.dataset.icon = transIcon(t);
      slot.dataset.from = t.transport_from || "";
      slot.dataset.to = t.transport_to || "";
      var role = transRole(t);
      slot.dataset.role = role.label;
      slot.dataset.rolek = role.k;
    }
    if(guess) slot.dataset.guess = guess.t ? guess.t.id : ('trip:' + (guess.trip ? guess.trip.name : 'x'));
    let fields = "";
    t.fields.forEach(function(f){
      fields += '<div><dt>' + f[0] + '</dt><dd>' + f[1] + '</dd></div>';
    });
    const srcNote = s.note ? '<div class="note">我补充的备注：' + s.note + '</div>' : '';
    let sidesHtml = '';
    if(t.imgs && t.imgs.length > 1){
      sidesHtml = '<div class="sides">' + t.imgs.map(function(im){
        return '<div class="side"><span class="side-label">' + im.side + '</span>' +
          '<img src="' + im.src + '" alt="' + t.name + ' ' + im.side + '"></div>';
      }).join('') + '</div>';
    }else{
      sidesHtml = '<img class="full" src="' + (t.imgs[0] ? t.imgs[0].src : '') + '" alt="' + t.name + '">';
    }
    slot.innerHTML =
      '<details class="ticket" id="ticket-' + t.id + '">' +
        '<summary>' +
          '<div class="thumb"><img src="' + (t.imgs[0] ? t.imgs[0].src : '') + '" alt=""></div>' +
          '<div class="sum-main">' +
            '<div class="sum-title">' + t.name + '</div>' +
            '<div class="sum-meta">' + (hasDate ? fmtDate(effDate) +
              (isMonthOnly(effDate) ? '<span class="todo"> · 日待定</span>' : '') : '<span class="todo">日期待补充</span>') +
              (guess ? '<span class="guess-flag">待确认同期</span>' : '') +
              (isTransport(t) ? ' · <span class="role ' + slot.dataset.rolek + '">' +
                (slot.dataset.icon||"➜") + ' ' + slot.dataset.role + '</span> ' +
                (slot.dataset.from||"") + ' → ' + (slot.dataset.to||"") : '') +
              ' · ' + t.sub + ' · ' + t.short + '</div>' +
          '</div>' +
          '<div class="sum-right"><span class="chev">▾</span></div>' +
        '</summary>' +
        '<div class="detail">' +
          sidesHtml +
          '<div class="place"><span class="pin">◉</span>' + t.place +
            ' · ' + t.lat.toFixed(4) + ', ' + t.lng.toFixed(4) + '</div>' +
          '<dl class="info">' + fields + srcNote +
            (t.note ? '<div class="note">' + t.note + '</div>' : '') +
          '</dl>' +
          (guess ? '<div class="guess-bar">待确认：' +
              (guess.t ? '可能与 <b>' + guess.t.name + '</b>（' + effDateOf(guess.t) + '）同期' :
                         '可能与 <b>' + guess.date + '</b> 同期') +
              ' · 依据：' + guess.reason +
              '。请核实后决定是否采用。' +
              '<div class="guess-acts">' +
                '<button class="guess-btn" data-adopt="' + t.id + '" data-date="' +
                  (guess.t ? normalizeDate(effDateOf(guess.t)) : normalizeDate(guess.date)) +
                  '">采用该日期 ' + (guess.t ? effDateOf(guess.t) : guess.date) + '</button>' +
                '<button class="guess-btn dismiss" data-dismiss="' + t.id + '">不是同期，忽略</button>' +
              '</div></div>' : '') +
          '<div class="supp">' +
            '<h4>补充信息 <span class="saved" id="saved-' + t.id + '">已保存到本机 ✓</span></h4>' +
            '<div class="supp-row">' +
              '<div class="col"><label>日期（票面没写时可填）</label>' +
                '<input type="date" id="date-' + t.id + '" value="' + (s.date||"") + '"></div>' +
            '</div>' +
            '<label>备注（任意补充）</label>' +
            '<textarea id="note-' + t.id + '" placeholder="例如：现场买的 / 和朋友一起去 / 记错了日期…">' +
              (s.note||"") + '</textarea>' +
            '<div class="supp-src">' +
              ("当前日期来源：" + (t.date_source === "user" ? "我补充的" :
                (t.date_source === "app_match" ? "同城行程推测（待确认）" : "票面识别"))) +
              ' · 填完自动保存，记得点顶部「导出我的补充」发回整理者</div>' +
          '</div>' +
        '</div>' +
      '</details>';
    placeSlot(slot, effDate, t);
  });
  // ===== 滚动定位：始终显示当前年月，可跳年、可回顶 =====
  var navDock = document.getElementById("navDock");
  var navNow = document.getElementById("navNow");
  var navLabel = document.getElementById("navLabel");
  var navPanel = document.getElementById("navPanel");
  var toTop = document.getElementById("toTop");
  var navYearsKey = "";
  function refreshNav(){
    if(!navPanel) return;
    var ys = Array.prototype.slice.call(timeline.querySelectorAll(".year-block"));
    var key = ys.map(function(y){ return y.dataset.year; }).join(",");
    if(key === navYearsKey) return;
    navYearsKey = key;
    navPanel.innerHTML = "";
    ys.forEach(function(yg){
      var b = document.createElement("button");
      b.className = "nav-year";
      b.textContent = yg.dataset.year;
      b.dataset.y = yg.dataset.year;
      navPanel.appendChild(b);
    });
  }
  var navTicking = false;
  function updateNav(){
    navTicking = false;
    var tl = timeline.getBoundingClientRect();
    var inTl = tl.top < 72 && tl.bottom > 130;
    navDock.classList.toggle("show", inTl);
    toTop.classList.toggle("show", (window.scrollY || 0) > 600);
    if(!inTl) return;
    var probe = 120, cur = null;
    var mgs = timeline.querySelectorAll(".month-group");
    for(var i=0;i<mgs.length;i++){
      var r = mgs[i].getBoundingClientRect();
      if(r.top <= probe && r.bottom > 0) cur = mgs[i];
    }
    if(!cur) return;
    var y = cur.closest(".year-block").dataset.year;
    var label = y + " · " + parseInt(cur.dataset.month,10) + "月";
    if(navLabel.textContent !== label){
      navLabel.textContent = label;
      navPanel.querySelectorAll(".nav-year").forEach(function(b){
        b.classList.toggle("on", b.dataset.y === y);
      });
    }
  }
  function onNavScroll(){
    if(navTicking) return;
    navTicking = true;
    requestAnimationFrame(updateNav);
    // 某些环境（后台标签、无帧渲染）rAF 不推进，兜底保证位置指示不会卡住
    setTimeout(function(){ if(navTicking) updateNav(); }, 120);
  }
  window.addEventListener("scroll", onNavScroll, {passive:true});
  window.addEventListener("resize", onNavScroll);
  navNow.addEventListener("click", function(e){
    e.stopPropagation(); navDock.classList.toggle("open");
  });
  navPanel.addEventListener("click", function(e){
    var b = e.target.closest(".nav-year");
    if(!b) return;
    var yg = timeline.querySelector('.year-block[data-year="' + b.dataset.y + '"]');
    if(yg) yg.scrollIntoView({behavior:"smooth", block:"start"});
    navDock.classList.remove("open");
  });
  document.addEventListener("click", function(e){
    if(!navDock.contains(e.target)) navDock.classList.remove("open");
  });
  toTop.addEventListener("click", function(){
    window.scrollTo({top:0, behavior:"smooth"});
  });
  refreshNav();
  updateNav();

  reorganize();
  refreshStats();

  // 待确认推测：采用日期 / 忽略
  function adoptGuess(id, dateVal){
    var input = document.getElementById("date-" + id);
    if(!input) return;
    input.value = dateVal;
    input.dispatchEvent(new Event("input", {bubbles:true}));
  }
  function dismissGuess(id, btn){
    var slot = btn.closest(".slot");
    if(slot){ delete slot.dataset.guess; slot.classList.remove("guess"); }
    var bar = btn.closest(".guess-bar");
    if(bar) bar.remove();
    var flag = slot && slot.querySelector(".guess-flag");
    if(flag) flag.remove();
    reorganize(); refreshStats();
  }
  document.addEventListener("click", function(e){
    var ad = e.target.closest("[data-adopt]");
    if(ad){ adoptGuess(ad.getAttribute("data-adopt"), ad.getAttribute("data-date")); return; }
    var dm = e.target.closest("[data-dismiss]");
    if(dm){ dismissGuess(dm.getAttribute("data-dismiss"), dm); }
  });

  // 输入即写数据库（经本地服务），失败则退回浏览器本地缓存
  var pushTimer = {};
  function pushToDb(id){
    clearTimeout(pushTimer[id]);
    pushTimer[id] = setTimeout(function(){
      var tag = document.getElementById("saved-" + id);
      fetch("/api/supplement", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(sup)
      }).then(function(r){ return r.json(); }).then(function(res){
        if(res.ok){
          tag.textContent = "已写入数据库 ✓";
        }else{
          tag.textContent = "仅存本机（数据库未连接）";
        }
        tag.classList.add("show");
        clearTimeout(tag._tm);
        tag._tm = setTimeout(function(){ tag.classList.remove("show"); }, 2200);
      }).catch(function(){
        tag.textContent = "仅存本机（数据库未连接）";
        tag.classList.add("show");
        clearTimeout(tag._tm);
        tag._tm = setTimeout(function(){ tag.classList.remove("show"); }, 2200);
      });
    }, 400);
  }

  // 改日期后把卡片挪到对应月份；挪动时以「同月邻居」为锚点恢复滚动位置，
  // 不跟着卡片满页跑，避免整页乱跳（手机上尤其明显）
  var dateTimer = {}, dateDone = {};
  function anchorOf(slot){
    var mg = slot.closest(".month-group");
    var yg = slot.closest(".year-block");
    return [
      mg,                                   // 月组本身非 sticky，位置稳定
      yg ? yg.querySelector(".year-head") : null,
      yg
    ].filter(Boolean);
  }
  function restoreScroll(anchors, tops){
    for(var i=0;i<anchors.length;i++){
      var a = anchors[i];
      if(a && a.isConnected){
        var diff = a.getBoundingClientRect().top - tops[i];
        if(Math.abs(diff) > 1) window.scrollBy(0, diff);
        return true;
      }
    }
    return false;
  }
  function commitDate(t, slot, val){
    var id = t.id;
    if(dateDone[id] === (val||"")) return;
    dateDone[id] = (val||"");
    var input = document.getElementById("date-" + id);
    var wasFocused = !!(input && document.activeElement === input);
    var selStart = input && input.selectionStart;
    var anchors = anchorOf(slot);
    var tops = anchors.map(function(a){ return a.getBoundingClientRect().top; });
    var sy = window.scrollY;
    placeSlot(slot, val ? val.replace(/-/g,".") : "", t);
    reorganize();
    refreshStats();
    if(!restoreScroll(anchors, tops)) window.scrollTo(0, sy);
    requestAnimationFrame(function(){
      if(!restoreScroll(anchors, tops)) window.scrollTo(0, sy);
    });
    if(wasFocused){
      var again = document.getElementById("date-" + id);
      if(again){
        try{ again.focus({preventScroll:true}); }catch(e){ again.focus(); }
        try{ if(selStart != null) again.setSelectionRange(selStart, selStart); }catch(e){}
      }
    }
  }
  TICKETS.forEach(function(t){
    ["date","note"].forEach(function(k){
      const el = document.getElementById(k + "-" + t.id);
      if(!el) return;
      el.addEventListener("input", function(){
        if(!sup[t.id]) sup[t.id] = {};
        sup[t.id][k] = el.value;
        saveSup(sup);            // 兜底
        pushToDb(t.id);          // 主路径：写库
        if(k === "date"){
          const meta = el.closest("details").querySelector(".sum-meta");
          const slot = el.closest(".slot");
          const label = el.value ? el.value.replace(/-/g,".") : "";
          if(label){
            meta.innerHTML = label + " · " + t.sub + " · " + t.short;
            slot.dataset.date = label;
            delete slot.dataset.guess;
            slot.classList.remove("guess");
            var gb = slot.querySelector(".guess-bar"); if(gb) gb.remove();
          }else{
            meta.innerHTML = '<span class="todo">日期待补充</span> · ' + t.sub + ' · ' + t.short;
            slot.dataset.date = "";
          }
          // 先把票面信息改掉，等输入停手再真正挪位置，避免边打字边搬家
          clearTimeout(dateTimer[t.id]);
          dateTimer[t.id] = setTimeout(function(){ commitDate(t, slot, el.value); }, 700);
        }
      });
      if(k === "date"){
        el.addEventListener("change", function(){
          clearTimeout(dateTimer[t.id]);
          commitDate(t, el.closest(".slot"), el.value);
        });
        el.addEventListener("blur", function(){
          if(dateDone[t.id] !== (el.value||"")){
            clearTimeout(dateTimer[t.id]);
            commitDate(t, el.closest(".slot"), el.value);
          }
        });
      }
    });
  });

  function pinSrc(color){
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="34" height="42" viewBox="0 0 34 42">' +
      '<path d="M17 1C8.7 1 2 7.7 2 16c0 11 15 25 15 25s15-14 15-25C32 7.7 25.3 1 17 1z" fill="' + color + '"/>' +
      '<circle cx="17" cy="16" r="6" fill="#ffffff"/></svg>';
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }

  var datedTickets = TICKETS.filter(function(t){ return t.lat && t.lng; });
  var map = new TMap.Map("map", { zoom:5, center:new TMap.LatLng(36.6,109.2), pitch:0 });
  var styles = {};
  datedTickets.forEach(function(t,i){
    styles[t.id] = new TMap.MarkerStyle({
      width:34, height:42, anchor:{x:17,y:42}, src:pinSrc(i%2 ? "#6b8e6b" : "#c2703a")
    });
  });
  var markers = new TMap.MultiMarker({
    map:map, styles:styles,
    geometries:datedTickets.map(function(t){
      return {id:t.id, styleId:t.id, position:new TMap.LatLng(t.lat,t.lng)};
    })
  });
  var infoWin = new TMap.InfoWindow({
    map:map, position:new TMap.LatLng(36.6,109.2), offset:{x:0,y:-38}, content:""
  });
  infoWin.close();
  markers.on("click", function(evt){
    var t = datedTickets.filter(function(x){return x.id===evt.geometry.id;})[0];
    if(!t) return;
    infoWin.setContent('<div style="font-family:-apple-system,PingFang SC,sans-serif;padding:4px 8px">' +
      '<b style="font-size:13px">' + t.name + '</b><br>' +
      '<span style="font-size:11px;color:#888">' + (sup[t.id]&&sup[t.id].date ? sup[t.id].date.replace(/-/g,".") : t.date_label) + '</span></div>');
    infoWin.setPosition(new TMap.LatLng(t.lat,t.lng));
    infoWin.open();
    var el = document.getElementById("ticket-" + t.id);
    if(el){ el.open = true; el.scrollIntoView({behavior:"smooth", block:"center"}); }
  });

  var lb = document.getElementById("lightbox");
  var lbi = document.getElementById("lightbox-img");
  document.addEventListener("click", function(e){
    if(e.target.tagName === "IMG" && (e.target.classList.contains("full") || e.target.closest(".detail"))){
      lbi.src = e.target.src; lb.style.display = "flex";
    }
  });
  lb.addEventListener("click", function(){ lb.style.display="none"; lbi.src=""; });

  var btnTransport = document.getElementById("btnTransport");
  btnTransport.addEventListener("click", function(){
    var on = document.body.classList.toggle("show-transport");
    btnTransport.textContent = on ? "隐藏登机牌" : "显示登机牌";
    refreshStats();
  });
  document.getElementById("btnCollapseAll").addEventListener("click", function(){
    document.querySelectorAll("details.ticket").forEach(function(d){ d.open = false; });
  });
  document.getElementById("btnExpandAll").addEventListener("click", function(){
    document.querySelectorAll("details.ticket").forEach(function(d){ d.open = true; });
  });

  var modal = document.getElementById("modal");
  document.getElementById("btnExport").addEventListener("click", function(){
    var out = {};
    TICKETS.forEach(function(t){ if(sup[t.id]) out[t.id] = sup[t.id]; });
    document.getElementById("exportText").value = JSON.stringify(out, null, 2);
    modal.style.display = "flex";
  });
  document.getElementById("btnCloseModal").addEventListener("click", function(){ modal.style.display="none"; });
  document.getElementById("btnCopy").addEventListener("click", function(){
    var ta = document.getElementById("exportText");
    ta.select();
    try{ document.execCommand("copy"); this.textContent="已复制"; }
    catch(e){ this.textContent="请手动复制"; }
    var self=this;
    setTimeout(function(){ self.textContent="复制"; }, 1500);
  });
  modal.addEventListener("click", function(e){ if(e.target===modal) modal.style.display="none"; });
  document.addEventListener("keydown", function(e){
    if(e.key === "Escape"){
      lb.style.display="none"; lbi.src=""; modal.style.display="none";
      navDock.classList.remove("open");
    }
  });

</script>
</body>
</html>''')

out = TPL.substitute(
    count=st["count"], spots=st["spots"], span=st["span"],
    gen_date=date.today().isoformat(),
    tickets=json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"),
    trips=json.dumps(TRIPS, ensure_ascii=False).replace("<", "\\u003c")
)
path = f"{BASE}/门票收藏册.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(out)
print("written:", path, len(out), "chars")
