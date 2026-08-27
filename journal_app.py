# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stock_signals'))
from stock_signals.tracker import init_db, get_recommendations, get_all_dates, get_stats, update_outcome, export_csv

st.set_page_config(page_title='Trading Journal', layout='wide')
init_db()

st.title('\U0001f4c8 Tech-Signal Trading Journal')
st.caption('US Stock Technical Analysis Journal')

tab1, tab2, tab3, tab4 = st.tabs([
    '\U0001f4c5 Daily Log', '\U0001f4c8 History', '\U0001f4ca Stats', '\U0001f4e4 Export'
])

with tab1:
    st.subheader('\U0001f4c5 Today Recommendations')
    today = datetime.now().strftime('%Y-%m-%d')
    today_recs = get_recommendations(date=today)
    if today_recs:
        df_today = pd.DataFrame(today_recs)
        recs = df_today[df_today['outcome'] == 'recommended']
        watches = df_today[df_today['outcome'] == 'watch']
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'**Recommended ({len(recs)} stocks)**')
            for _, r in recs.iterrows():
                sym = r['symbol']
                rat = r['rating']
                sc = r['score']
                with st.expander(f'{sym} - {rat} (Score: {sc})'):
                    st.metric('Current', f"{r['current_price']:.2f}")
                    st.metric('Entry', f"{r['entry_price']:.2f}")
                    st.metric('Stop Loss', f"{r['stop_loss']:.2f}")
                    st.metric('Target 1', f"{r['target1']:.2f}")
                    st.metric('Target 2', f"{r['target2']:.2f}")
                    rr = f"{r['rr_ratio']:.1f}:1" if r['rr_ratio'] else 'N/A'
                    st.metric('RR', rr)
                    st.markdown(f"**Entry type:** {r['entry_type']}")
                    st.markdown(f"**Buy strategy:** {r['buy_strategy']}")
                    st.markdown(f"**Sell strategy:** {r['sell_strategy']}")
                    st.markdown(f"**Trend:** {r['trend_phase']} | **Resonance:** {r['resonance']}")
                    res = st.selectbox('Result', ['--', 'win', 'loss', 'hold'], key=f"res_{r['id']}")
                    op = st.number_input('Exit Price', min_value=0.0, format='%.2f', key=f"price_{r['id']}", value=0.0)
                    pnl = st.number_input('PnL %', min_value=-100.0, max_value=1000.0, format='%.2f', key=f"pnl_{r['id']}", value=0.0)
                    if st.button('Save', key=f"save_{r['id']}"):
                        update_outcome(r['id'], res, op if op > 0 else None, pnl if pnl != 0.0 else None)
                        st.success('Saved')
        with col2:
            st.markdown(f'**Watch ({len(watches)} stocks)**')
            for _, r in watches.iterrows():
                sym = r['symbol']
                rat = r['rating']
                with st.expander(f'{sym} - {rat}'):
                    st.metric('Current', f"{r['current_price']:.2f}")
                    st.metric('Entry', f"{r['entry_price']:.2f}")
                    st.metric('Stop Loss', f"{r['stop_loss']:.2f}")
                    st.metric('Target 1', f"{r['target1']:.2f}")
                    st.metric('Target 2', f"{r['target2']:.2f}")
                    rr = f"{r['rr_ratio']:.1f}:1" if r['rr_ratio'] else 'N/A'
                    st.metric('RR', rr)
                    st.markdown(f"**Entry type:** {r['entry_type']}")
                    st.markdown(f"**Buy strategy:** {r['buy_strategy']}")
                    res = st.selectbox('Result', ['--', 'win', 'loss', 'hold'], key=f"res_w_{r['id']}")
                    op = st.number_input('Exit Price', min_value=0.0, format='%.2f', key=f"price_w_{r['id']}", value=0.0)
                    pnl = st.number_input('PnL %', min_value=-100.0, max_value=1000.0, format='%.2f', key=f"pnl_w_{r['id']}", value=0.0)
                    if st.button('Save', key=f"save_w_{r['id']}"):
                        update_outcome(r['id'], res, op if op > 0 else None, pnl if pnl != 0.0 else None)
                        st.success('Saved')
    else:
        st.info('No records for today. Run scan to save.')

with tab2:
    st.subheader('History')
    dates = get_all_dates()
    if dates:
        selected = st.selectbox('Select Date', dates)
        recs = get_recommendations(date=selected)
        if recs:
            df = pd.DataFrame(recs)
            cols = ['symbol','rating','score','current_price','entry_price','entry_type','stop_loss','target1','target2','rr_ratio','position_pct','outcome']
            df_d = df[cols].copy()
            df_d.columns = ['Symbol','Rating','Score','Current','Entry','Entry Type','Stop Loss','Target1','Target2','RR','Pos%','Outcome']
            st.dataframe(df_d, use_container_width=True)
    else:
        st.info('No history yet')

with tab3:
    st.subheader('Statistics')
    stats = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Total Records', stats['total'])
    c2.metric('Tracked', stats['tracked'])
    wr = f"{stats['win_rate']}%" if stats['win_rate'] else 'N/A'
    c3.metric('Win Rate', wr)
    ap = f"{stats['avg_pnl_pct']}%" if stats['avg_pnl_pct'] else 'N/A'
    c4.metric('Avg PnL', ap)
    if stats['tracked'] > 0:
        df_s = pd.DataFrame([
            {'Result': 'win', 'Count': stats['wins']},
            {'Result': 'loss', 'Count': stats['losses']},
            {'Result': 'hold', 'Count': stats['holds']}
        ])
        fig = px.pie(df_s, values='Count', names='Result', title='Result Distribution')
        st.plotly_chart(fig, use_container_width=True)
    if stats['recent_days']:
        df_d = pd.DataFrame(stats['recent_days'], columns=['Date', 'Count'])
        fig2 = px.bar(df_d, x='Date', y='Count', title='Records per Day')
        st.plotly_chart(fig2, use_container_width=True)
    if stats['top_stocks']:
        df_t = pd.DataFrame(stats['top_stocks'], columns=['Symbol', 'Appearances', 'Avg Score'])
        st.dataframe(df_t, use_container_width=True)

with tab4:
    st.subheader('Export')
    if st.button('Export CSV'):
        fp = os.path.join(os.path.expanduser('~'), 'Desktop', 'trading_journal.csv')
        result = export_csv(fp)
        if result:
            st.success(f'Exported to: {result}')
            with open(result, 'rb') as ff:
                st.download_button('Download CSV', data=ff, file_name='trading_journal.csv', mime='text/csv')
        else:
            st.info('No data to export')
