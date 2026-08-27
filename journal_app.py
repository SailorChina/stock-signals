# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stock_signals'))
from stock_signals.tracker import init_db, get_recommendations, get_all_dates, get_stats, update_outcome, export_csv

st.set_page_config(page_title='交易记录', layout='wide')
init_db()

st.title('\U0001f4c8 Tech-Signal 交易记录')
st.caption('美股技术分析推荐记录')

tab1, tab2, tab3, tab4 = st.tabs([
    '\U0001f4c5 每日记录', '\U0001f4c8 历史记录', '\U0001f4ca 统计分析', '\U0001f4e4 导出'
])

with tab1:
    st.subheader('\U0001f4c5 今日推荐')
    today = datetime.now().strftime('%Y-%m-%d')
    today_recs = get_recommendations(date=today)
    if today_recs:
        df_today = pd.DataFrame(today_recs)
        recs = df_today[df_today['outcome'] == 'recommended']
        watches = df_today[df_today['outcome'] == 'watch']
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'**推荐 ({len(recs)} 只)**')
            for _, r in recs.iterrows():
                sym = r['symbol']
                rat = r['rating']
                sc = r['score']
                with st.expander(f'{sym} - {rat} (评分: {sc})'):
                    st.metric('现价', f"{r['current_price']:.2f}")
                    st.metric('入场价', f"{r['entry_price']:.2f}")
                    st.metric('止损', f"{r['stop_loss']:.2f}")
                    st.metric('目标1', f"{r['target1']:.2f}")
                    st.metric('目标2', f"{r['target2']:.2f}")
                    rr = f"{r['rr_ratio']:.1f}:1" if r['rr_ratio'] else 'N/A'
                    st.metric('风险回报', rr)
                    st.markdown(f"**入场方式:** {r['entry_type']}")
                    st.markdown(f"**交易计划:** {r['buy_strategy']}")
                    st.markdown(f"**止损策略:** {r['sell_strategy']}")
                    st.markdown(f"**趋势:** {r['trend_phase']} | **共振:** {r['resonance']}")
                    res = st.selectbox('结果', ['--', 'win', 'loss', 'hold'], key=f"res_{r['id']}")
                    op = st.number_input('平仓价', min_value=0.0, format='%.2f', key=f"price_{r['id']}", value=0.0)
                    pnl = st.number_input('盈亏%', min_value=-100.0, max_value=1000.0, format='%.2f', key=f"pnl_{r['id']}", value=0.0)
                    if st.button('保存', key=f"save_{r['id']}"):
                        update_outcome(r['id'], res, op if op > 0 else None, pnl if pnl != 0.0 else None)
                        st.success('已保存')
        with col2:
            st.markdown(f'**观察 ({len(watches)} 只)**')
            for _, r in watches.iterrows():
                sym = r['symbol']
                rat = r['rating']
                with st.expander(f'{sym} - {rat}'):
                    st.metric('现价', f"{r['current_price']:.2f}")
                    st.metric('入场价', f"{r['entry_price']:.2f}")
                    st.metric('止损', f"{r['stop_loss']:.2f}")
                    st.metric('目标1', f"{r['target1']:.2f}")
                    st.metric('目标2', f"{r['target2']:.2f}")
                    rr = f"{r['rr_ratio']:.1f}:1" if r['rr_ratio'] else 'N/A'
                    st.metric('风险回报', rr)
                    st.markdown(f"**入场方式:** {r['entry_type']}")
                    st.markdown(f"**交易计划:** {r['buy_strategy']}")
                    res = st.selectbox('结果', ['--', 'win', 'loss', 'hold'], key=f"res_w_{r['id']}")
                    op = st.number_input('平仓价', min_value=0.0, format='%.2f', key=f"price_w_{r['id']}", value=0.0)
                    pnl = st.number_input('盈亏%', min_value=-100.0, max_value=1000.0, format='%.2f', key=f"pnl_w_{r['id']}", value=0.0)
                    if st.button('保存', key=f"save_w_{r['id']}"):
                        update_outcome(r['id'], res, op if op > 0 else None, pnl if pnl != 0.0 else None)
                        st.success('已保存')
    else:
        st.info('今日暂无记录。运行 scan 后自动保存。')

with tab2:
    st.subheader('历史记录')
    dates = get_all_dates()
    if dates:
        selected = st.selectbox('选择日期', dates)
        recs = get_recommendations(date=selected)
        if recs:
            df = pd.DataFrame(recs)
            cols = ['symbol','rating','score','current_price','entry_price','entry_type','stop_loss','target1','target2','rr_ratio','position_pct','outcome']
            df_d = df[cols].copy()
            df_d.columns = ['代码','评级','分数','现价','入场价','入场类型','止损','目标1','目标2','RR','仓位%','结果']
            st.dataframe(df_d, use_container_width=True)
    else:
        st.info('暂无历史记录')

with tab3:
    st.subheader('Statistics')
    stats = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('总记录', stats['total'])
    c2.metric('已追踪', stats['tracked'])
    wr = f"{stats['win_rate']}%" if stats['win_rate'] else 'N/A'
    c3.metric('胜率', wr)
    ap = f"{stats['avg_pnl_pct']}%" if stats['avg_pnl_pct'] else 'N/A'
    c4.metric('平均盈亏', ap)
    if stats['tracked'] > 0:
        df_s = pd.DataFrame([
            {'结果': 'win', 'Count': stats['wins']},
            {'结果': 'loss', 'Count': stats['losses']},
            {'结果': 'hold', 'Count': stats['holds']}
        ])
        fig = px.pie(df_s, values='Count', names='结果', title='结果分布')
        st.plotly_chart(fig, use_container_width=True)
    if stats['recent_days']:
        df_d = pd.DataFrame(stats['recent_days'], columns=['日期', '记录数'])
        fig2 = px.bar(df_d, x='Date', y='Count', title='每日推荐数量')
        st.plotly_chart(fig2, use_container_width=True)
    if stats['top_stocks']:
        df_t = pd.DataFrame(stats['top_stocks'], columns=['代码', '出现次数', '平均评分'])
        st.dataframe(df_t, use_container_width=True)

with tab4:
    st.subheader('导出')
    if st.button('导出 CSV'):
        fp = os.path.join(os.path.expanduser('~'), 'Desktop', 'trading_journal.csv')
        result = export_csv(fp)
        if result:
            st.success(f'已导出到: {result}')
            with open(result, 'rb') as ff:
                st.download_button('下载 CSV', data=ff, file_name='trading_journal.csv', mime='text/csv')
        else:
            st.info('暂无数据可导出')
