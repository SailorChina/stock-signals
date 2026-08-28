# -*- coding: utf-8 -*-
"""Tech-Signal 交易记录 v2.0"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os, sys, json, sqlite3
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_signals"))
from stock_signals.tracker import init_db, get_recommendations, get_all_dates, get_stats, update_outcome, export_csv, get_best_worst
from stock_signals.review import auto_review
from stock_signals.sync_data import sync_to_github, pull_from_github, sync_status

st.set_page_config(page_title="交易记录", layout="wide", initial_sidebar_state="expanded", page_icon="📈")
init_db()

_THEME = {"light": "plotly_white", "dark": "plotly_dark"}
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

@st.cache_data(ttl=30)
def get_deduped_records():
    raw = get_recommendations()
    df = pd.DataFrame(raw)
    if df.empty:
        return raw
    df["_key"] = df["scan_date"] + "___" + df["symbol"]
    df = df.sort_values(["_key", "score"], ascending=[True, False])
    df = df.drop_duplicates(subset=["_key"], keep="first").drop(columns=["_key"])
    return [dict(r) for r in df.to_dict("records")]

def dedup_count():
    raw = get_recommendations()
    df = pd.DataFrame(raw)
    if df.empty:
        return len(raw), len(raw)
    df["_key"] = df["scan_date"] + "___" + df["symbol"]
    unique = df.drop_duplicates(subset=["_key"])
    return len(raw), len(unique)

def get_template():
    return _THEME.get(st.session_state["theme"], "plotly_white")

def outcome_icon(o):
    return {"win": "🟢", "loss": "🔴", "hold": "🟡", "recommended": "📋", "watch": "👁"}.get(o, "⚪")

# Sidebar
with st.sidebar:
    st.markdown("**📈 Tech-Signal 交易记录**")
    st.markdown("---")
    theme_opt = st.radio("🎨 主题", ["☀️ 浅色", "🌙 深色"],
                         index=1 if st.session_state["theme"] == "dark" else 0,
                         label_visibility="collapsed", horizontal=True)
    new_theme = "dark" if theme_opt == "🌙 深色" else "light"
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme
        st.rerun()
    st.markdown("---")
    st.markdown("**📊 快捷操作**")
    if st.button("📋 运行扫描", use_container_width=True):
        st.info("请在终端执行: python -m stock_signals.cli scan")
    if st.button("🔄 强制同步", use_container_width=True, type="primary"):
        with st.spinner("同步中..."):
            sync_to_github()
        st.success("已同步到云端")
        st.rerun()
    st.markdown("---")
    db_path = os.path.join(os.path.expanduser("~"), ".tech-signal-FUTU-skill", "journal.db")
    total, unique = dedup_count()
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / 1024 / 1024
        st.caption("DB: " + str(round(size_mb, 2)) + " MB")
    st.caption("Records: " + str(total) + " -> " + str(unique) + " unique")
    st.markdown("---")
    st.caption("Tech-Signal FUTU Skill v2.0")

st.markdown("**📈 Tech-Signal 交易记录**")
st.caption("US Stock Technical Analysis Tracker")

tab_dash, tab_daily, tab_history, tab_stats, tab_calendar, tab_review, tab_sync, tab_export = st.tabs([
    "📊 Dashboard", "📅 Daily", "🔍 History", "📈 Analytics", "🗓️ Calendar", "✅ Review", "📮 Sync", "📮 Export"
])

# Tab 1: Dashboard
with tab_dash:
    recs = get_deduped_records()
    stats = get_stats()
    tracked = [r for r in recs if r.get('outcome') in ('win', 'loss', 'hold')]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('📋 Total', len(recs))
    c2.metric('🔴 Tracked', stats['tracked'])
    wr = str(stats['win_rate']) + '%' if stats['win_rate'] else 'N/A'
    c3.metric('🟢 Win Rate', wr)
    ap = str(stats['avg_pnl_pct']) + '%' if stats['avg_pnl_pct'] else 'N/A'
    c4.metric('💰 Avg PnL', ap)
    today_count = len([r for r in recs if r['scan_date'] == datetime.now().strftime('%Y-%m-%d')])
    c5.metric('📋 Today', today_count)
    st.markdown('---')
    col_main, col_side = st.columns([3, 2])
    with col_main:
        st.markdown('**📈 Cumulative PnL**')
        if tracked:
            df_pnl = pd.DataFrame(tracked)
            df_pnl['scan_date'] = pd.to_datetime(df_pnl['scan_date'])
            df_pnl = df_pnl.sort_values('scan_date')
            df_pnl['cum_pnl'] = df_pnl['outcome_pnl_pct'].cumsum()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_pnl['scan_date'], y=df_pnl['cum_pnl'],
                mode='lines+markers', name='Cum PnL',
                line=dict(color='#667eea', width=3), marker=dict(size=8)))
            if df_pnl['cum_pnl'].notna().any():
                target = df_pnl['cum_pnl'].mean()
                fig.add_hline(y=target, line_dash='dash', line_color='orange', annotation_text='Mean ' + str(round(target, 1)) + '%')
            fig.add_hline(y=0, line_dash='dash', line_color='gray')
            fig.update_layout(height=300, showlegend=False, xaxis_title='Date', yaxis_title='Cum PnL (%)', template=get_template())
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('No tracked PnL data yet. Mark outcomes in Daily tab.')
    with col_side:
        st.markdown('**🎯 Outcome Distribution**')
        if tracked:
            outcomes = [r['outcome'] for r in tracked]
            oc = Counter(outcomes)
            labels = ['Win', 'Loss', 'Hold']
            values = [oc.get('win', 0), oc.get('loss', 0), oc.get('hold', 0)]
            colors = ['#22c55e', '#ef4444', '#f59e0b']
            fig = px.pie(values=values, names=labels, color_discrete_sequence=colors, template=get_template())
            fig.update_traces(textinfo='label+percent', hole=0.4)
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('No tracked data')
        st.markdown('**📊 Score Distribution**')
        if recs:
            scores = [r['score'] for r in recs if r.get('score')]
            if scores:
                fig = px.histogram(scores, nbins=10, color_continuous_scale='Viridis', template=get_template())
                fig.update_layout(xaxis_title='Score', yaxis_title='Count', height=200)
                st.plotly_chart(fig, use_container_width=True)

# Tab 3: History
with tab_history:
    st.markdown('---')
    st.markdown('**🔍 History**')
    all_recs = get_deduped_records()
    df_hist = pd.DataFrame(all_recs)
    if df_hist.empty:
        st.info('No history')
    else:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            search = st.text_input('Search', placeholder='Enter symbol or note...', key='hist_search')
        with col_s2:
            filter_res = st.multiselect('Outcome', ['win', 'loss', 'hold', 'recommended', 'watch'], key='hist_outcome')
        with col_s3:
            filter_rat = st.multiselect('Rating', ['Buy', 'Overweight', 'Underweight', 'Hold'], key='hist_rating')
        with col_s4:
            filter_et = st.multiselect('Entry', ['现价入场', '回调入场', '突破入场'], key='hist_entry')
        if search:
            df_hist = df_hist[df_hist['symbol'].str.contains(search, case=False, na=False) | df_hist['note'].str.contains(search, case=False, na=False)]
        if filter_res:
            df_hist = df_hist[df_hist['outcome'].isin(filter_res)]
        if filter_rat:
            df_hist = df_hist[df_hist['rating'].isin(filter_rat)]
        if filter_et:
            df_hist = df_hist[df_hist['entry_type'].isin(filter_et)]
        sort_col = st.selectbox('Sort by', ['scan_date', 'score', 'current_price', 'outcome_pnl_pct'], key='hist_sort')
        sort_dir = st.radio('Direction', ['Descending', 'Ascending'], horizontal=True, key='hist_dir')
        df_hist = df_hist.sort_values(sort_col, ascending=(sort_dir == 'Ascending'))
        display = df_hist.copy()
        display['Price'] = display['current_price'].apply(lambda x: '$' + str(round(x, 2)) if pd.notna(x) else '-')
        display['SL'] = display['stop_loss'].apply(lambda x: '$' + str(round(x, 2)) if pd.notna(x) else '-')
        display['T1'] = display['target1'].apply(lambda x: '$' + str(round(x, 2)) if pd.notna(x) else '-')
        display['T2'] = display['target2'].apply(lambda x: '$' + str(round(x, 2)) if pd.notna(x) else '-')
        display['PnL'] = display['outcome_pnl_pct'].apply(lambda x: ('+' if x > 0 else '') + str(round(x, 1)) + '%' if pd.notna(x) else '-')
        display = display[['scan_date', 'symbol', 'rating', 'entry_type', 'Price', 'SL', 'T1', 'T2', 'outcome', 'PnL']]
        display.columns = ['Date', 'Symbol', 'Rating', 'Entry', 'Price', 'SL', 'T1', 'T2', 'Outcome', 'PnL%']
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.markdown('---')
        st.markdown('**📄 Details / Edit Notes**')
        for _, r in df_hist.head(20).iterrows():
            with st.expander(outcome_icon(r['outcome']) + ' ** ' + r['symbol'] + ' **  ' + r['scan_date'] + '  ' + r['rating'] + '  ' + r['entry_type']):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown('**Score:** ' + str(r.get('score', '-')) + ' | **Resonance:** ' + str(r.get('resonance', '-')))
                    st.markdown('**Trend:** ' + str(r.get('trend_phase', '-')) + ' | **Hold Period:** ' + str(r.get('hold_period', '-')))
                    st.markdown('**SL:** $' + str(round(r.get('stop_loss', 0), 2)) + ' | **T1:** $' + str(round(r.get('target1', 0), 2)) + ' | **T2:** $' + str(round(r.get('target2', 0), 2)))
                    st.markdown('**RR:** ' + str(round(r.get('rr_ratio', 0), 2)) + ':1')
                with col_b:
                    if r.get('outcome'):
                        st.markdown('**Outcome:** ' + r['outcome'] + ' | **PnL:** ' + str(round(r.get('outcome_pnl_pct', 0), 1)) + '%')
                    else:
                        st.markdown('**Outcome:** Pending')
                    new_note = st.text_area('Note', value=r.get('note', ''), key='note_' + str(r['id']), height=60)
                    if new_note != r.get('note', ''):
                        if st.button('Save', key='save_' + str(r['id'])):
                            conn = sqlite3.connect(os.path.expanduser('~/.tech-signal-FUTU-skill/journal.db'))
                            conn.execute('UPDATE recommendations SET note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (new_note, r['id']))
                            conn.commit()
                            conn.close()
                            st.success('Saved')
                            st.rerun()
        if len(df_hist) > 20:
            st.caption('Showing top 20 of ' + str(len(df_hist)) + ' records')

# Tab 2: Daily
with tab_daily:
    st.markdown('---')
    st.markdown('**📅 Daily Recommendations**')
    all_dates = get_all_dates()
    selected_date = st.selectbox('Select Date', all_dates if all_dates else [datetime.now().strftime('%Y-%m-%d')])
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_rating = st.multiselect('Rating', ['Buy', 'Overweight', 'Underweight', 'Hold'])
    with col_f2:
        filter_entry = st.multiselect('Entry Type', ['现价入场', '回调入场', '突破入场'])
    with col_f3:
        filter_outcome = st.selectbox('Outcome', ['全部', 'recommended', 'watch', 'win', 'loss', 'hold'])
    day_recs = [r for r in get_deduped_records() if r['scan_date'] == selected_date]
    if filter_rating:
        day_recs = [r for r in day_recs if r.get('rating') in filter_rating]
    if filter_entry:
        day_recs = [r for r in day_recs if r.get('entry_type') in filter_entry]
    if filter_outcome != '全部':
        day_recs = [r for r in day_recs if r.get('outcome') == filter_outcome]
    recs_df = pd.DataFrame(day_recs)
    if not recs_df.empty:
        display_cols = ['symbol', 'rating', 'entry_type', 'current_price', 'stop_loss', 'target1', 'target2', 'rr_ratio', 'outcome', 'outcome_pnl_pct']
        df_show = recs_df[display_cols].copy()
        df_show.columns = ['Symbol', 'Rating', 'Entry', 'Price', 'SL', 'T1', 'T2', 'RR', 'Outcome', 'PnL%']
        df_show['Price'] = df_show['Price'].apply(lambda x: '$' + str(round(x, 2)) if x else '-')
        df_show['SL'] = df_show['SL'].apply(lambda x: '$' + str(round(x, 2)) if x else '-')
        df_show['T1'] = df_show['target1'].apply(lambda x: '$' + str(round(x, 2)) if x else '-')
        df_show['T2'] = df_show['target2'].apply(lambda x: '$' + str(round(x, 2)) if x else '-')
        df_show['PnL%'] = df_show['PnL%'].apply(lambda x: ('+' if x > 0 else '') + str(round(x, 1)) + '%' if pd.notna(x) else '-')
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        tracked_in_day = recs_df[recs_df['outcome'].isin(['win', 'loss', 'hold'])]
        untracked_in_day = recs_df[recs_df['outcome'].isin(['recommended', 'watch'])]
        if not tracked_in_day.empty:
            st.markdown('**✅ Tracked**')
            for _, r in tracked_in_day.iterrows():
                icon = outcome_icon(r['outcome'])
                pnl_str = ('+' if r.get('outcome_pnl_pct', 0) > 0 else '') + str(round(r.get('outcome_pnl_pct', 0), 1)) + '%' if r.get('outcome_pnl_pct') else ''
                st.markdown(icon + ' ** ' + r['symbol'] + ' **  ' + r['rating'] + ' | ' + r['entry_type'] + ' | $' + str(round(r['current_price'], 2)) + pnl_str)
                st.caption('SL: $' + str(round(r['stop_loss'], 2)) + ' | T1: $' + str(round(r['target1'], 2)) + ' | T2: $' + str(round(r['target2'], 2)))
                if r.get('note'):
                    st.caption('Note: ' + r['note'])
                st.divider()
        if not untracked_in_day.empty:
            st.markdown('**📋 Pending**')
            for _, r in untracked_in_day.iterrows():
                icon = outcome_icon(r['outcome'])
                st.markdown(icon + ' ** ' + r['symbol'] + ' **  ' + r['rating'] + ' | $' + str(round(r['current_price'], 2)))
                st.caption('SL: $' + str(round(r['stop_loss'], 2)) + ' | T1: $' + str(round(r['target1'], 2)) + ' | T2: $' + str(round(r['target2'], 2)) + ' | RR: ' + str(round(r['rr_ratio'], 2)) + ':1')
                if r.get('note'):
                    st.caption('Note: ' + r['note'])
                st.divider()
    else:
        st.info('No data for ' + selected_date)

# Tab 5: Calendar
with tab_calendar:
    st.markdown('---')
    st.markdown('**🗓️ Calendar Heatmap**')
    all_recs = get_deduped_records()
    df_cal = pd.DataFrame(all_recs)
    if df_cal.empty:
        st.info('No data')
    else:
        df_cal['scan_date'] = pd.to_datetime(df_cal['scan_date'])
        df_cal['month'] = df_cal['scan_date'].dt.to_period('M')
        daily_count = df_cal.groupby('scan_date').size().reset_index(name='count')
        tracked_cal = df_cal[df_cal['outcome'].isin(['win', 'loss', 'hold'])]
        daily_pnl = tracked_cal.groupby('scan_date')['outcome_pnl_pct'].mean().reset_index(name='pnl')
        cal_df = daily_count.merge(daily_pnl, on='scan_date', how='left')
        st.markdown('**Daily recommendation count**')
        if not cal_df.empty:
            fig = px.bar(cal_df, x='scan_date', y='count', color='count', color_continuous_scale='Blues', template=get_template())
            fig.update_layout(height=200, xaxis_title='', yaxis_title='Count')
            st.plotly_chart(fig, use_container_width=True)
        if not daily_pnl.empty:
            st.markdown('**Daily average PnL**')
            fig2 = px.bar(daily_pnl, x='scan_date', y='pnl', color='pnl', color_continuous_scale='RdYlGn', template=get_template())
            fig2.update_layout(height=200, xaxis_title='', yaxis_title='Avg PnL (%)')
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown('---')
        st.markdown('**📅 Monthly Breakdown**')
        for period in sorted(cal_df['month'].dropna().unique()):
            p_df = cal_df[cal_df['month'] == period]
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown('**' + str(period) + ' Count**')
                fig3 = px.bar(p_df, x='scan_date', y='count', template=get_template(), color='count', color_continuous_scale='Blues')
                fig3.update_layout(height=180, xaxis_title='', yaxis_title='Count')
                st.plotly_chart(fig3, use_container_width=True)
            with col_c2:
                p_pnl = p_df[p_df['pnl'].notna()]
                if not p_pnl.empty:
                    st.markdown('**' + str(period) + ' Avg PnL**')
                    fig4 = px.bar(p_pnl, x='scan_date', y='pnl', template=get_template(), color='pnl', color_continuous_scale='RdYlGn')
                    fig4.update_layout(height=180, xaxis_title='', yaxis_title='Avg PnL (%)')
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info('No tracked data for this period')

# Tab 4: Analytics
with tab_stats:
    st.markdown('---')
    st.markdown('**📈 Deep Analytics**')
    recs = get_deduped_records()
    tracked = [r for r in recs if r.get('outcome') in ('win', 'loss', 'hold')]
    df = pd.DataFrame(tracked) if tracked else pd.DataFrame()
    if df.empty:
        st.info('No tracked data for analytics')
    else:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown('**By Entry Type**')
            es = df.groupby('entry_type').agg(total=('outcome', 'count'), wins=('outcome', lambda x: (x=='win').sum()), avg_pnl=('outcome_pnl_pct', 'mean')).reset_index()
            es['win_rate'] = (es['wins'] / es['total'] * 100).round(1).astype(str) + '%'
            st.dataframe(es, use_container_width=True, hide_index=True)
        with col_b:
            st.markdown('**By Rating**')
            rs = df.groupby('rating').agg(total=('outcome', 'count'), wins=('outcome', lambda x: (x=='win').sum()), avg_pnl=('outcome_pnl_pct', 'mean')).reset_index()
            rs['win_rate'] = (rs['wins'] / rs['total'] * 100).round(1).astype(str) + '%'
            st.dataframe(rs, use_container_width=True, hide_index=True)
        with col_c:
            st.markdown('**By Trend Phase**')
            ts = df.groupby('trend_phase').agg(total=('outcome', 'count'), wins=('outcome', lambda x: (x=='win').sum()), avg_pnl=('outcome_pnl_pct', 'mean')).reset_index()
            ts['win_rate'] = (ts['wins'] / ts['total'] * 100).round(1).astype(str) + '%'
            st.dataframe(ts, use_container_width=True, hide_index=True)
        st.markdown('---')
        st.markdown('**📊 PnL Distribution**')
        pnl_vals = df['outcome_pnl_pct'].dropna()
        if not pnl_vals.empty:
            fig = px.histogram(pnl_vals, nbins=15, color=pnl_vals, color_continuous_scale='RdYlGn', template=get_template())
            fig.update_layout(xaxis_title='PnL (%)', yaxis_title='Count', height=280)
            st.plotly_chart(fig, use_container_width=True)
        col_h, col_i = st.columns(2)
        with col_h:
            st.markdown('**Score vs PnL**')
            df_score = df[df['score'].notna() & df['outcome_pnl_pct'].notna()]
            if not df_score.empty:
                fig = px.scatter(df_score, x='score', y='outcome_pnl_pct', color='outcome', size='score', hover_data=['symbol', 'entry_type'], template=get_template())
                fig.update_layout(height=280)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info('No cross data')
        with col_i:
            st.markdown('**Entry Type vs Win Rate**')
            df_entry = df[df['entry_type'].notna()]
            if not df_entry.empty:
                ep = df_entry.groupby('entry_type').agg(total=('outcome', 'count'), wins=('outcome', lambda x: (x=='win').sum())).reset_index()
                ep['win_rate'] = (ep['wins'] / ep['total'] * 100).round(1)
                fig = px.bar(ep, x='entry_type', y='win_rate', color='win_rate', color_continuous_scale='RdYlGn', template=get_template())
                fig.update_layout(height=280, xaxis_title='Entry Type', yaxis_title='Win Rate (%)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info('No data')
        st.markdown('**⏱️ Hold Period vs PnL**')
        if 'hold_period' in df.columns:
            df_hp = df[df['hold_period'].notna() & df['outcome_pnl_pct'].notna()]
            if not df_hp.empty:
                fig = px.scatter(df_hp, x='hold_period', y='outcome_pnl_pct', color='outcome', hover_data=['symbol', 'rating'], template=get_template())
                fig.update_layout(height=260)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info('No hold period data')
        st.markdown('**📅 This Week vs Last Week**')
        today = datetime.now()
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(weeks=1)
        this_week = df[df['scan_date'] >= this_monday.strftime('%Y-%m-%d')]
        last_week = df[(df['scan_date'] >= last_monday.strftime('%Y-%m-%d')) & (df['scan_date'] < this_monday.strftime('%Y-%m-%d'))]
        col_w1, col_w2, col_w3, col_w4 = st.columns(4)
        col_w1.metric('This Week', len(this_week))
        col_w2.metric('Last Week', len(last_week))
        this_pnl = this_week['outcome_pnl_pct'].mean() if not this_week.empty else None
        last_pnl = last_week['outcome_pnl_pct'].mean() if not last_week.empty else None
        col_w3.metric('This Avg PnL', ('+' if this_pnl else '') + str(round(this_pnl, 1)) + '%' if this_pnl is not None else 'N/A')
        col_w4.metric('Last Avg PnL', ('+' if last_pnl else '') + str(round(last_pnl, 1)) + '%' if last_pnl is not None else 'N/A')
        if not this_week.empty and not last_week.empty:
            cmp = pd.DataFrame([{'Week': 'This', 'Count': len(this_week), 'Avg PnL': this_pnl}, {'Week': 'Last', 'Count': len(last_week), 'Avg PnL': last_pnl}])
            fig = px.bar(cmp, x='Week', y=['Count', 'Avg PnL'], barmode='group', template=get_template())
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('---')
        st.markdown('**🏆 Best / Worst**')
        bw = get_best_worst()
        col_best, col_worst = st.columns(2)
        with col_best:
            if bw['best']:
                for r in bw['best'][:3]:
                    st.markdown('🟢 ** ' + r['symbol'] + ' **  +' + str(r['outcome_pnl_pct']) + '%  (' + r['rating'] + ')')
            else:
                st.info('No data')
        with col_worst:
            if bw['worst']:
                for r in bw['worst'][:3]:
                    st.markdown('🔴 ** ' + r['symbol'] + ' **  ' + str(r['outcome_pnl_pct']) + '%  (' + r['rating'] + ')')
            else:
                st.info('No data')

# Tab 6: Review
with tab_review:
    st.markdown('---')
    st.markdown('**✅ Auto Review**')
    review_date = st.date_input('Review Date', datetime.now() - timedelta(days=1))
    rd_str = review_date.strftime('%Y-%m-%d')
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button('🔄 Start Review', type='primary', use_container_width=True):
            with st.spinner('Fetching prices for ' + rd_str + '...'):
                result = auto_review(rd_str)
            st.session_state['_review_result'] = result
            st.session_state['_review_date'] = rd_str
            st.rerun()
    stored = st.session_state.get('_review_date')
    if stored and stored == rd_str:
        result = st.session_state['_review_result']
        cnt = len(result.get('recs', []))
        st.markdown('**Review Date: ' + result['date'] + '**  (Total: ' + str(cnt) + ' stocks)')
        if result.get('recs'):
            for r in result['recs']:
                pnl = r.get('pnl_pct')
                cur = r.get('current_price', 0)
                entry = r.get('entry_price') or r.get('current_price') or 0
                if pnl is not None:
                    pnl_color = 'green' if pnl > 0 else 'red'
                    pnl_icon = '+' if pnl > 0 else ''
                    pnl_str = pnl_icon + str(round(pnl, 1)) + '%'
                else:
                    pnl_str = 'N/A'
                st.markdown('** ' + r['symbol'] + ' **  ' + r['rating'] + ' | Entry: $' + str(round(entry, 2)) + ' -> $' + str(round(cur, 2)) + '  ' + pnl_str)
                st.caption('SL: $' + str(round(r.get('stop_loss', 0), 2)) + ' | T1: $' + str(round(r.get('target1', 0), 2)) + ' | T2: $' + str(round(r.get('target2', 0), 2)))
                cols_btn = st.columns([2, 1, 1, 1])
                with cols_btn[0]:
                    if st.button('Hold', key='hold_' + str(r['id']), use_container_width=True):
                        update_outcome(r['id'], 'hold', cur, pnl)
                        st.session_state['_review_result'] = auto_review(rd_str)
                        st.success(r['symbol'] + ' -> Hold')
                        st.rerun()
                with cols_btn[1]:
                    if st.button('Win', key='win_' + str(r['id']), use_container_width=True):
                        update_outcome(r['id'], 'win', cur, pnl)
                        st.session_state['_review_result'] = auto_review(rd_str)
                        st.success(r['symbol'] + ' -> Win')
                        st.rerun()
                with cols_btn[2]:
                    if st.button('Loss', key='stop_' + str(r['id']), use_container_width=True):
                        update_outcome(r['id'], 'loss', cur, pnl)
                        st.session_state['_review_result'] = auto_review(rd_str)
                        st.warning(r['symbol'] + ' -> Loss')
                        st.rerun()
                st.divider()
        else:
            st.info(result.get('message', 'No review data'))
    else:
        st.caption('Select a date and click Start Review to fetch prices and calculate PnL')

# Tab 7: Sync
with tab_sync:
    st.markdown('---')
    st.markdown('**📮 Cloud Sync**')
    st.caption('Two-way sync with GitHub for multi-device data sharing')
    st.markdown('---')
    _st = sync_status()
    total, unique = dedup_count()
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric('Local Records', unique)
    col_s2.metric('Original', total)
    col_s3.metric('GitHub', 'Connected' if _st.get('last_sync') else 'Not synced')
    last = _st.get('last_sync') or 'Never'
    col_s4.metric('Last Sync', last[:16] if len(last) > 16 else last)
    st.markdown('---')
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button('Sync to Cloud', type='primary', use_container_width=True):
            with st.spinner('Syncing...'):
                _r = sync_to_github()
            st.session_state['_sync_result'] = _r
            st.rerun()
    with col_btn2:
        if st.button('Pull from Cloud', use_container_width=True):
            with st.spinner('Pulling...'):
                _r = pull_from_github()
            st.session_state['_sync_result'] = _r
            st.rerun()
    if st.session_state.get('_sync_result'):
        _r = st.session_state['_sync_result']
        if _r.get('success'):
            st.success(_r.get('message', 'Success'))
        else:
            st.error(_r.get('message', 'Failed'))
    st.markdown('---')
    st.caption('Data backed up as JSON to GitHub data branch. Code on main branch. Auto sync on startup.')
    st.markdown('**GitHub Repo**: https://github.com/SailorChina/tech-signal-FUTU-skill')
    st.markdown('**Data Branch**: https://github.com/SailorChina/tech-signal-FUTU-skill/tree/data')

# Tab 8: Export
with tab_export:
    st.markdown('---')
    st.markdown('**📮 Export Data**')
    st.markdown('**📄 CSV Export**')
    export_btn = st.button('Export CSV')
    if export_btn:
        filepath = export_csv(os.path.join(os.path.expanduser('~'), 'Desktop', 'tech_signal_journal_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'))
        if filepath:
            st.success('Exported: ' + filepath)
            with open(filepath, 'rb') as f:
                st.download_button('Download CSV', data=f, file_name=os.path.basename(filepath), mime='text/csv')
        else:
            st.error('Export failed, database is empty')
    st.markdown('---')
    st.markdown('**📑 PDF Report Export**')
    st.caption('Generate PDF trading report with statistics and details')
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        report_type = st.selectbox('Report Type', ['Weekly', 'Monthly', 'All'], key='report_type')
    with col_pdf2:
        report_date = st.date_input('Report Date', datetime.now(), key='report_date')
    pdf_btn = st.button('Generate PDF Report', type='primary')
    if pdf_btn:
        try:
            from fpdf import FPDF
            recs = get_deduped_records()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Helvetica', size=12)
            pdf.set_font('Helvetica', 'B', size=18)
            pdf.cell(0, 10, 'Tech-Signal Trading Report', new_x='LMARGIN', new_y='NEXT', align='C')
            pdf.set_font('Helvetica', size=10)
            pdf.cell(0, 6, 'Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M'), new_x='LMARGIN', new_y='NEXT', align='C')
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', size=14)
            pdf.cell(0, 8, 'Statistics', new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', size=11)
            stats = get_stats()
            pdf.cell(0, 6, 'Total: ' + str(stats['total']) + ' | Tracked: ' + str(stats['tracked']) + ' | Win Rate: ' + str(stats['win_rate']) + '% | Avg PnL: ' + str(stats['avg_pnl_pct']) + '%', new_x='LMARGIN', new_y='NEXT')
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', size=14)
            pdf.cell(0, 8, 'Records', new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', size=9)
            headers = ['Date', 'Symbol', 'Rating', 'Entry', 'Price', 'SL', 'T1', 'Outcome', 'PnL%']
            col_widths = [25, 20, 18, 22, 18, 18, 18, 18, 20]
            for i, h in enumerate(headers):
                pdf.cell(col_widths[i], 6, h, border=1)
            pdf.ln()
            for r in recs:
                row_data = [
                    str(r.get('scan_date', '')),
                    str(r.get('symbol', '')),
                    str(r.get('rating', '')),
                    str(r.get('entry_type', '')),
                    '$' + str(round(r.get('current_price', 0), 2)) if r.get('current_price') else '-',
                    '$' + str(round(r.get('stop_loss', 0), 2)) if r.get('stop_loss') else '-',
                    '$' + str(round(r.get('target1', 0), 2)) if r.get('target1') else '-',
                    str(r.get('outcome', '-')),
                    ('+' if r.get('outcome_pnl_pct', 0) > 0 else '') + str(round(r.get('outcome_pnl_pct', 0), 1)) + '%' if r.get('outcome_pnl_pct') else '-',
                ]
                for i, val in enumerate(row_data):
                    pdf.cell(col_widths[i], 5, val[:10], border=1, max_line_height=5)
                pdf.ln()
            out_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'tech_signal_report_' + report_date.strftime('%Y%m%d') + '.pdf')
            pdf.output(out_path)
            st.success('PDF generated: ' + out_path)
            with open(out_path, 'rb') as f:
                st.download_button('Download PDF', data=f, file_name=os.path.basename(out_path), mime='application/pdf')
        except ImportError:
            st.error('Please install fpdf2: pip install fpdf2')
        except Exception as e:
            st.error('PDF generation failed: ' + str(e))
