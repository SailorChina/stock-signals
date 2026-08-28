# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os, sys, json
from typing import List, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stock_signals'))
from stock_signals.tracker import (
    init_db, get_recommendations, get_all_dates, get_stats,
    update_outcome, export_csv, get_best_worst
)
from stock_signals.review import auto_review

st.set_page_config(page_title='交易记录', layout='wide', initial_sidebar_state='expanded')
init_db()

@st.cache_data(ttl=60)
def get_all_data():
    return get_recommendations()

@st.cache_data(ttl=60)
def get_daily_pnl():
    recs = get_recommendations()
    if not recs: return []
    df = pd.DataFrame(recs)
    df['scan_date'] = pd.to_datetime(df['scan_date'])
    df = df[df['outcome_pnl_pct'].notna()].copy()
    df = df.sort_values('scan_date')
    df['cum_pnl'] = df['outcome_pnl_pct'].cumsum()
    return df[['scan_date', 'symbol', 'outcome_pnl_pct', 'cum_pnl']].to_dict('records')

@st.cache_data(ttl=60)
def get_entry_type_stats():
    recs = get_recommendations()
    if not recs: return {}
    df = pd.DataFrame(recs)
    tracked = df[df['outcome'].isin(['win', 'loss', 'hold'])]
    if tracked.empty: return {}
    result = {}
    for et, grp in tracked.groupby('entry_type'):
        wins = (grp['outcome'] == 'win').sum()
        total = len(grp)
        wr = str(round(wins/total*100,1)) + '%' if total else 'N/A'
        result[et] = {'total': total, 'wins': wins, 'win_rate': wr}
    return result

@st.cache_data(ttl=60)
def get_rating_stats():
    recs = get_recommendations()
    if not recs: return {}
    df = pd.DataFrame(recs)
    tracked = df[df['outcome'].isin(['win', 'loss', 'hold'])]
    if tracked.empty: return {}
    result = {}
    for rating, grp in tracked.groupby('rating'):
        wins = (grp['outcome'] == 'win').sum()
        total = len(grp)
        wr = str(round(wins/total*100,1)) + '%' if total else 'N/A'
        result[rating] = {'total': total, 'wins': wins, 'win_rate': wr}
    return result

@st.cache_data(ttl=60)
def get_trend_stats():
    recs = get_recommendations()
    if not recs: return {}
    df = pd.DataFrame(recs)
    tracked = df[df['outcome'].isin(['win', 'loss', 'hold'])]
    if tracked.empty: return {}
    result = {}
    for tp, grp in tracked.groupby('trend_phase'):
        wins = (grp['outcome'] == 'win').sum()
        total = len(grp)
        avg_pnl = grp['outcome_pnl_pct'].mean()
        wr = str(round(wins/total*100,1)) + '%' if total else 'N/A'
        ap = str(round(avg_pnl,1)) + '%' if not pd.isna(avg_pnl) else 'N/A'
        result[tp] = {'total': total, 'wins': wins, 'win_rate': wr, 'avg_pnl': ap}
    return result

@st.cache_data(ttl=60)
def get_best_worst():
    recs = get_recommendations()
    if not recs: return {'best': [], 'worst': []}
    df = pd.DataFrame(recs)
    tracked = df[df['outcome_pnl_pct'].notna()].sort_values('outcome_pnl_pct', ascending=False)
    return {'best': tracked.head(3).to_dict('records'), 'worst': tracked.tail(3).to_dict('records')[::-1]}

with st.sidebar:
    st.markdown('**📈 Tech-Signal 交易记录**')
    st.markdown('---')
    st.markdown('**🔥 快捷操作**')
    if st.button('📋 运行扫描', use_container_width=True):
        st.info('请在终端运行: python -m stock_signals.cli scan')
    st.markdown('---')
    st.markdown('**📋 数据库信息**')
    db_path = os.path.join(os.path.expanduser('~'), '.tech-signal-FUTU-skill', 'journal.db')
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / 1024 / 1024
        st.caption('数据库大小: ' + str(round(size_mb,2)) + ' MB')
    st.markdown('---')
    st.markdown('**🎨 主题设置**')
    st.selectbox('主题', ['默认', '深色'], label_visibility='collapsed')
    st.markdown('---')
    st.caption('Tech-Signal FUTU Skill v1.0')

st.markdown('**📈 Tech-Signal 交易记录**')
st.caption('美股技术分析推荐记录与绩效分析')

tab_dash, tab_daily, tab_history, tab_stats, tab_export = st.tabs([
    '📊 仪表盘', '📅 每日记录', '🔍 历史记录', '📈 统计分析', '📮 导出'
])

with tab_dash:
    st.markdown('---')
    stats = get_stats()
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric('📋 总记录', stats['total'])
    c2.metric('🔴 已追踪', stats['tracked'])
    wr = str(stats['win_rate'])+'%' if stats['win_rate'] else 'N/A'
    c3.metric('🟢 胜率', wr)
    ap = str(stats['avg_pnl_pct'])+'%' if stats['avg_pnl_pct'] else 'N/A'
    c4.metric('💰 平均盈亏', ap)
    today_count = len(get_recommendations(date=datetime.now().strftime('%Y-%m-%d')))
    c5.metric('📋 今日推荐', today_count)
    st.markdown('---')
    c1,c2 = st.columns([2,1])
    with c1:
        st.markdown('**📈 累计盈亏曲线**')
        pnl_data = get_daily_pnl()
        if pnl_data:
            df_pnl = pd.DataFrame(pnl_data)
            df_pnl['scan_date'] = pd.to_datetime(df_pnl['scan_date'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_pnl['scan_date'], y=df_pnl['cum_pnl'], mode='lines+markers', name='累计盈亏', line=dict(color='#667eea', width=3), marker=dict(size=8)))
            fig.add_hline(y=0, line_dash='dash', line_color='gray')
            fig.update_layout(height=300, showlegend=False, xaxis_title='日期', yaxis_title='累计盈亏 (%)', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('暂无已追踪的盈亏数据，请在每日记录中标记交易结果')
    with c2:
        st.markdown('**🕐 最近记录**')
        recent = get_recommendations()[:10]
        if recent:
            for r in recent:
                icon = {'win': '🟢', 'loss': '🔴', 'hold': '🟡', 'recommended': '📋'}.get(r['outcome'], '⚪')
                pnl_str = ' ' + str(r['outcome_pnl_pct']) + '%' if r['outcome_pnl_pct'] else ''
                st.markdown(icon + ' **' + r['symbol'] + '** ' + pnl_str)
                st.caption(r['scan_date'] + ' | ' + r['rating'] + ' | ' + r['entry_type'])
                st.divider()
        else:
            st.info('暂无记录')

with tab_daily:
    st.markdown('---')
    st.markdown('**📅 今日推荐**')
    today = datetime.now().strftime('%Y-%m-%d')
    today_recs = get_recommendations(date=today)
    if today_recs:
        with st.expander('🔍 筛选'):
            col_f1,col_f2,col_f3 = st.columns(3)
            with col_f1: filter_rating = st.multiselect('评级', ['Buy', 'Overweight', 'Underweight', 'Sell'])
            with col_f2: filter_entry = st.multiselect('入场方式', ['现价入场', '回调入场', '突破入场'])
            with col_f3: filter_outcome = st.selectbox('结果', ['全部', 'recommended', 'watch', 'win', 'loss', 'hold'])
        df_today = pd.DataFrame(today_recs)
        if filter_rating: df_today = df_today[df_today['rating'].isin(filter_rating)]
        if filter_entry: df_today = df_today[df_today['entry_type'].isin(filter_entry)]
        if filter_outcome != '全部': df_today = df_today[df_today['outcome'] == filter_outcome]
        recs = df_today[df_today['outcome'] == 'recommended']
        watches = df_today[df_today['outcome'] == 'watch']
        col1,col2 = st.columns([3,2])
        with col1:
            st.markdown(f'**📊 推荐股票** (共{len(recs)}只)')
            if not recs.empty:
                for r in recs.to_dict('records'):
                    st.markdown(f'**{r["symbol"]}**  {r["rating"]} | {r["entry_type"]} | 现价 ${r["current_price"]:.2f}')
                    st.caption(f'止损: ${r["stop_loss"]:.2f} | 目标1: ${r["target1"]:.2f} | 目标2: ${r["target2"]:.2f} | 盈亏比: {r["rr_ratio"]:.2f}:1')
                    st.divider()
            else:
                st.info('今日无推荐股票')
        with col2:
            st.markdown(f'**👀 观察股票** (共{len(watches)}只)')
            if not watches.empty:
                for w in watches.to_dict('records'):
                    st.markdown(f'**{w["symbol"]}**  {w["rating"]} | 现价 ${w["current_price"]:.2f}')
                    st.caption(f'入场: {w["entry_type"]} | 止损: ${w["stop_loss"]:.2f} | 目标1: ${w["target1"]:.2f} | 盈亏比: {w["rr_ratio"]:.2f}:1')
                    st.divider()
            else:
                st.info('今日无观察股票')
    else:
        st.info('今日暂无推荐数据，请运行扫描后查看')

with tab_history:
    st.markdown('---')
    st.markdown('**📜 历史记录**')
    all_dates = get_all_dates()
    if all_dates:
        selected_date = st.selectbox('选择日期', all_dates)
        day_recs = get_recommendations(date=selected_date)
        if day_recs:
            df_hist = pd.DataFrame(day_recs)
            st.dataframe(df_hist[['symbol', 'rating', 'entry_type', 'current_price', 'stop_loss', 'target1', 'target2', 'outcome', 'outcome_pnl_pct']], use_container_width=True)
        else:
            st.info('该日期无记录')
    else:
        st.info('暂无历史记录')

with tab_stats:
    st.markdown('---')
    st.markdown('**📈 统计分析**')
    entry_stats = get_entry_type_stats()
    rating_stats = get_rating_stats()
    trend_stats = get_trend_stats()
    best_worst = get_best_worst()
    col1,col2 = st.columns(2)
    with col1:
        st.markdown('**按入场方式统计**')
        if entry_stats:
            df_et = pd.DataFrame([{'入场方式': k, **v} for k,v in entry_stats.items()])
            st.dataframe(df_et, use_container_width=True)
        else:
            st.info('暂无数据')
    with col2:
        st.markdown('**按评级统计**')
        if rating_stats:
            df_rt = pd.DataFrame([{'评级': k, **v} for k,v in rating_stats.items()])
            st.dataframe(df_rt, use_container_width=True)
        else:
            st.info('暂无数据')
    col3,col4 = st.columns(2)
    with col3:
        st.markdown('**按趋势阶段统计**')
        if trend_stats:
            df_tp = pd.DataFrame([{'趋势阶段': k, **v} for k,v in trend_stats.items()])
            st.dataframe(df_tp, use_container_width=True)
        else:
            st.info('暂无数据')
    with col4:
        st.markdown('**最佳/最差记录**')
        if best_worst['best']:
            st.markdown('**🟢 最佳**')
            for r in best_worst['best']:
                st.markdown(f'**{r["symbol"]}** {r["outcome_pnl_pct"]}% | {r["rating"]}')
            st.markdown('**🔴 最差**')
            for r in best_worst['worst']:
                st.markdown(f'**{r["symbol"]}** {r["outcome_pnl_pct"]}% | {r["rating"]}')
        else:
            st.info('暂无追踪数据')

with st.container():
    st.markdown("---")
    col_r1, col_r2 = st.columns([1, 4])
    with col_r1:
        review_date = st.date_input("复盘日期", datetime.now() - timedelta(days=1))
    with col_r2:
        if st.button("自动复盘", type="primary", use_container_width=True):
            with st.spinner("获取价格中..."):
                _rd = review_date.strftime("%Y-%m-%d")
                _res = auto_review(_rd)
                st.session_state["_review_result"] = _res
                st.session_state["_review_date"] = _rd
    _stored = st.session_state.get("_review_date")
    if _stored and _stored == review_date.strftime("%Y-%m-%d"):
        _res = st.session_state["_review_result"]
        _cnt = len(_res.get("recs", []))
        st.markdown("**复盘日期: %s**  (共 %d 只)" % (_res["date"], _cnt))
        if _res.get("recs"):
            for r in _res["recs"]:
                pnl = r.get("pnl_pct")
                status = r.get("status", "")
                cur = r.get("current_price", 0)
                entry = r.get("entry_price") or r.get("current_price") or 0
                if pnl is not None:
                    pnl_color = "green" if pnl > 0 else "red"
                    pnl_icon = "+" if pnl > 0 else ""
                else:
                    pnl_color = "gray"
                    pnl_icon = ""
                st.markdown("**%s**  %s | 现价入场: $%.2f → 现价: $%.2f" % (r["symbol"], r["rating"], entry, cur))
                st.caption("止损: $%.2f | 目标1: $%.2f | 目标2: $%.2f" % (r.get("stop_loss", 0), r.get("target1", 0), r.get("target2", 0)))
                if pnl is not None:
                    html_pnl = "<span style='color:%s;font-weight:bold'>%s%s%%</span>" % (pnl_color, pnl_icon, pnl)
                    st.caption("盈亏: %s | 状态: %s" % (html_pnl, status), unsafe_allow_html=True)
                cols_btn = st.columns([2, 1, 1, 1])
                with cols_btn[0]:
                    if st.button("持仓中", key="hold_%d" % r["id"], use_container_width=True):
                        update_outcome(r["id"], "hold", cur, pnl)
                        st.session_state["_review_result"] = auto_review(_rd)
                        st.rerun()
                with cols_btn[1]:
                    if st.button("盈利", key="win_%d" % r["id"], use_container_width=True):
                        update_outcome(r["id"], "win", cur, pnl)
                        st.session_state["_review_result"] = auto_review(_rd)
                        st.rerun()
                with cols_btn[2]:
                    if st.button("止损", key="stop_%d" % r["id"], use_container_width=True):
                        update_outcome(r["id"], "loss", cur, pnl)
                        st.session_state["_review_result"] = auto_review(_rd)
                        st.rerun()
                st.divider()
        else:
            st.info(_res.get("message", "暂无复盘数据"))
    st.markdown("---")

with tab_export:
    st.markdown('---')
    st.markdown('**📮 导出数据**')
    st.markdown('将交易记录导出为 CSV 文件')
    export_btn = st.button('📥 导出 CSV')
    if export_btn:
        filepath = export_csv(os.path.join(os.path.expanduser(chr(126)), "Desktop", "tech_signal_journal_" + datetime.now().strftime("%Y%m%d") + ".csv"))
        if filepath:
            st.success("导出成功: " + filepath)
            with open(filepath, "rb") as f:
                st.download_button("下载文件", data=f, file_name=os.path.basename(filepath), mime="text/csv")
        else:
            st.error("导出失败，数据库为空")
