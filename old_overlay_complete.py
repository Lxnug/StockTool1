import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import finnhub
from deep_translator import GoogleTranslator

st.set_page_config(page_title='Stock Tool', layout='wide')

if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = []
if 'watchlist_data' not in st.session_state:
    st.session_state['watchlist_data'] = None
if 'general_news' not in st.session_state:
    st.session_state['general_news'] = []
if 'market_news_loaded' not in st.session_state:
    st.session_state['market_news_loaded'] = False
if 'watchlist_search_results' not in st.session_state:
    st.session_state['watchlist_search_results'] = []
if 'watchlist_search_term' not in st.session_state:
    st.session_state['watchlist_search_term'] = ''
if 'api_key_input' not in st.session_state:
    st.session_state['api_key_input'] = ''
if 'api_key_saved' not in st.session_state:
    st.session_state['api_key_saved'] = ''


def get_api_key():
    if st.session_state.get('api_key_saved'):
        return st.session_state['api_key_saved']
    if st.session_state.get('api_key_input'):
        return st.session_state['api_key_input']
    if os.environ.get('FINNHUB_API_KEY'):
        return os.environ.get('FINNHUB_API_KEY')
    try:
        return st.secrets.get('FINNHUB_API_KEY', '')
    except Exception:
        return ''


def get_finnhub_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return finnhub.Client(api_key=api_key)


def safe_num(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def search_symbols(query):
    client = get_finnhub_client()
    if not client:
        return []
    try:
        res = client.symbol_lookup(query)
        return res.get('result', []) if isinstance(res, dict) else []
    except Exception:
        return []


def get_stock_quote(symbol):
    client = get_finnhub_client()
    if not client:
        return None
    try:
        return client.quote(symbol)
    except Exception:
        return None


def get_stock_news(symbol, days=7):
    client = get_finnhub_client()
    if not client:
        return []
    try:
        to_date = date.today()
        from_date = to_date - timedelta(days=days)
        return client.company_news(symbol, _from=from_date.isoformat(), to=to_date.isoformat())
    except Exception:
        return []


def get_recommendations(symbol):
    client = get_finnhub_client()
    if not client:
        return None
    try:
        recs = client.recommendation_trends(symbol)
        return recs[0] if recs else None
    except Exception:
        return None


def get_general_market_news(days=1):
    client = get_finnhub_client()
    if not client:
        return []
    try:
        to_date = date.today()
        from_date = to_date - timedelta(days=days)
        return client.general_news('general', _from=from_date.isoformat(), to=to_date.isoformat())
    except Exception:
        return []


def translate_to_german(text):
    if not text:
        return ''
    try:
        return GoogleTranslator(source='auto', target='de').translate(text)
    except Exception:
        return text


def get_symbols(item):
    raw = item.get('symbol', '') or item.get('symbols', '') or ''
    if isinstance(raw, list):
        raw = ', '.join([str(x) for x in raw if x])
    raw = str(raw).strip()
    if not raw or raw.lower() == 'n/a':
        return '—'
    return raw


def translate_market_impact(item):
    headline = str(item.get('headline', '')).strip()
    summary = str(item.get('summary', '')).strip()
    text = (headline + ' ' + summary).lower()
    positive = ['beat', 'beats', 'upgrade', 'raises', 'strong', 'profit', 'growth', 'record', 'buyback', 'guidance up', 'acquisition', 'approval', 'approved', 'surge', 'rally', 'higher', 'bullish', 'outperforms']
    negative = ['miss', 'downgrade', 'cuts', 'lower', 'loss', 'lawsuit', 'probe', 'investigation', 'delay', 'warning', 'recall', 'fall', 'drop', 'slump', 'recession', 'rates higher', 'bearish']
    pos_hits = [w for w in positive if w in text]
    neg_hits = [w for w in negative if w in text]
    if len(pos_hits) > len(neg_hits):
        direction = 'positiv'
        impact = 'kann den Kurs eher stützen oder kurzfristig antreiben.'
        color = '🟢'
    elif len(neg_hits) > len(pos_hits):
        direction = 'negativ'
        impact = 'kann Druck auf den Kurs ausüben oder Volatilität erhöhen.'
        color = '🔴'
    else:
        direction = 'neutral'
        impact = 'dürfte eher geringe direkte Kurswirkung haben.'
        color = '🟡'
    german_headline = translate_to_german(headline) if headline else ''
    german_summary = translate_to_german(summary) if summary else ''
    if german_headline and german_summary:
        short_de = f'{german_headline}. {german_summary[:240]}'
    elif german_headline:
        short_de = german_headline
    elif german_summary:
        short_de = german_summary[:240]
    else:
        short_de = 'Keine verwertbare Meldung vorhanden.'
    if pos_hits:
        reason = f'Positive Schlagwörter gefunden: {", ".join(pos_hits[:4])}'
    elif neg_hits:
        reason = f'Negative Schlagwörter gefunden: {", ".join(neg_hits[:4])}'
    else:
        reason = 'Keine klaren Kurs-Treiber erkannt; eher neutrale Meldung.'
    return {'direction': direction, 'impact': impact, 'color': color, 'short_de': short_de, 'reason': reason}


with st.sidebar:
    st.header('🔑 Finnhub API')
    st.caption('Hier kannst du deinen Finnhub API Key eingeben.')
    st.text_input('Finnhub API Key', type='password', key='api_key_input')
    if st.button('API Key speichern', key='save_api_key_btn'):
        st.session_state['api_key_saved'] = st.session_state.get('api_key_input', '').strip()
        st.success('API Key gespeichert.')
        st.rerun()
    if st.session_state.get('api_key_saved'):
        st.success('API Key aktiv')
    elif os.environ.get('FINNHUB_API_KEY') or (hasattr(st, 'secrets') and 'FINNHUB_API_KEY' in st.secrets):
        st.info('API Key aus Umgebung/Secrets verfügbar')
    else:
        st.warning('Kein API Key gesetzt')

    st.divider()
    st.header('➕ Aktie hinzufügen')
    st.caption('Gib Ticker oder Firmennamen ein')
    new_stock = st.text_input('Neue Aktie hinzufügen', placeholder='z.B. NVDA oder Rheinmetall', key='watchlist_search_input')
    if st.button('🔎 Suchen', key='watchlist_search_btn'):
        st.session_state['watchlist_search_results'] = search_symbols(new_stock.strip()) if new_stock.strip() else []
        st.session_state['watchlist_search_term'] = new_stock.strip()
    results = st.session_state.get('watchlist_search_results', [])
    term = st.session_state.get('watchlist_search_term', '')
    if term:
        st.write(f'**Suche für:** {term}')
    if results:
        st.subheader('Vorschläge')
        for r in results[:5]:
            sym = r.get('symbol', '—')
            desc = r.get('description', '—')
            exchange = r.get('mic', '') or r.get('exchange', '') or r.get('type', '')
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(f'**{sym}** — {desc} ({exchange})')
            with cols[1]:
                if st.button('Übernehmen', key=f'use_{sym}'):
                    if sym not in st.session_state['watchlist']:
                        st.session_state['watchlist'].append(sym)
                    st.session_state['watchlist_search_results'] = []
                    st.session_state['watchlist_search_term'] = ''
                    st.rerun()
    elif term:
        st.warning(f'Keine passende Aktie gefunden für: {term}')
    st.divider()
    st.subheader('Aktuelle Watchlist')
    for i, ticker in enumerate(st.session_state['watchlist']):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.write(ticker)
        with c2:
            if st.button('✖', key=f'remove_{ticker}_{i}'):
                st.session_state['watchlist'].pop(i)
                st.rerun()


tab1, tab2, tab3, tab4, tab5 = st.tabs(['📰 News', '📊 Watchlist', '⚡ Gewinner', '🔥 Verlierer', 'ℹ️ Info'])

with tab1:
    st.header('📰 Tägliches Markt-Update')
    st.markdown('Die wichtigsten Marktnews und Kursbewegungen für heute')
    if st.button('🔄 Markt-Updates aktualisieren', key='refresh_market_news'):
        st.session_state['market_news_loaded'] = False
        st.rerun()
    if 'market_news_loaded' not in st.session_state or not st.session_state['market_news_loaded']:
        with st.spinner('Lade Markt-News...'):
            st.session_state['general_news'] = get_general_market_news(days=1)
            st.session_state['market_news_loaded'] = True
    general_news = st.session_state.get('general_news', [])
    if general_news:
        st.success(f'✅ {len(general_news)} News gefunden')
        important_news = []
        for news in general_news[:20]:
            impact = translate_market_impact(news)
            if impact['direction'] != 'neutral' or news.get('priceSensitive'):
                important_news.append((news, impact))
        if important_news:
            st.subheader('🚨 Potenziell kursrelevante News')
            for news, impact in important_news[:10]:
                title = news.get('headline', 'Ohne Titel')
                symbol = get_symbols(news)
                source = news.get('source', '—')
                date_raw = news.get('datetime', '')
                st.markdown(f"""
                <div class="news-card">
                    <strong>{impact['color']} {translate_to_german(title)}</strong><br>
                    <small><b>Deutsch:</b> {impact['short_de'][:260]}...</small><br>
                    <small><b>Marktwirkung:</b> {impact['direction']} – {impact['impact']}</small><br>
                    <small><b>Begründung:</b> {impact['reason']}</small><br>
                    <small><b>Symbol:</b> {symbol} | <b>Quelle:</b> {source} | <b>Zeit:</b> {date_raw}</small>
                </div>
                """, unsafe_allow_html=True)
                if news.get('url'):
                    st.link_button('📖 Zum Originalartikel', news['url'])
                st.divider()
        st.subheader('📰 Alle Markt-News')
        for news in general_news[10:25]:
            impact = translate_market_impact(news)
            title = news.get('headline', 'Ohne Titel')
            symbol = get_symbols(news)
            source = news.get('source', '—')
            with st.expander(f"{impact['color']} {translate_to_german(title)}"):
                st.write(f"**Kurz auf Deutsch:** {impact['short_de']}")
                st.write(f"**Mögliche Marktwirkung:** {impact['direction']} – {impact['impact']}")
                st.write(f"**Begründung:** {impact['reason']}")
                st.write(f"**Symbol:** {symbol} | **Quelle:** {source}")
                if news.get('url'):
                    st.link_button('📖 Zum Artikel', news['url'])
    else:
        st.info('Noch keine News geladen. Klicke auf "Markt-Updates aktualisieren".')

with tab2:
    st.header('📊 Live Watchlist')
    st.markdown('Echtzeit-Kurse und Analysen deiner Watchlist')
    if st.button('🔄 Watchlist aktualisieren', key='refresh_watchlist'):
        st.session_state['watchlist_data'] = None
        st.rerun()
    if len(st.session_state.get('watchlist', [])) == 0:
        st.info('📝 Deine Watchlist ist leer. Füge Aktien in der Sidebar hinzu.')
    else:
        if 'watchlist_data' not in st.session_state or st.session_state['watchlist_data'] is None:
            with st.spinner('Lade Watchlist-Daten...'):
                watchlist_data = []
                for ticker in st.session_state['watchlist']:
                    quote = get_stock_quote(ticker)
                    news = get_stock_news(ticker, days=7)
                    rec = get_recommendations(ticker)
                    if quote and isinstance(quote, dict):
                        watchlist_data.append({'ticker': ticker, 'quote': quote, 'news': news, 'recommendations': rec})
                st.session_state['watchlist_data'] = watchlist_data
        watchlist_data = st.session_state.get('watchlist_data', [])
        if watchlist_data:
            st.subheader('📈 Watchlist Überblick')
            rows = []
            for item in watchlist_data:
                q = item.get('quote', {})
                rows.append({
                    'Ticker': item.get('ticker', ''),
                    'Preis ($)': f"{safe_num(q.get('c')):.2f}",
                    'Änderung ($)': f"{safe_num(q.get('d')):.2f}",
                    'Änderung (%)': f"{safe_num(q.get('dp')):.2f}%",
                    'Volumen': f"{int(safe_num(q.get('v'))):,}",
                    'High ($)': f"{safe_num(q.get('h')):.2f}",
                    'Low ($)': f"{safe_num(q.get('l')):.2f}"
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.subheader('🔍 Aktie Details')
            for item in watchlist_data:
                q = item.get('quote', {})
                ticker = item.get('ticker', '')
                current_price = safe_num(q.get('c'))
                change = safe_num(q.get('d'))
                change_percent = safe_num(q.get('dp'))
                volume = int(safe_num(q.get('v')))
                with st.expander(f'📌 {ticker} - ${current_price:.2f}'):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric('Aktueller Preis', f'${current_price:.2f}')
                    with c2:
                        st.markdown(f"<div class={'positive' if change > 0 else 'negative'}>Änderung: ${change:.2f} ({change_percent:.2f}%)</div>", unsafe_allow_html=True)
                    with c3:
                        st.metric('Volumen', f'{volume:,}')
                    if item.get('recommendations'):
                        st.subheader('👨‍💼 Analysten-Empfehlungen')
                        rec = item['recommendations']
                        st.write(f"**Period:** {rec.get('period', '')}")
                        st.write(f"**Strong Buy:** {rec.get('strongBuy', '')}")
                        st.write(f"**Buy:** {rec.get('buy', '')}")
                        st.write(f"**Hold:** {rec.get('hold', '')}")
                        st.write(f"**Sell:** {rec.get('sell', '')}")
                        st.write(f"**Strong Sell:** {rec.get('strongSell', '')}")
                    if item.get('news'):
                        st.subheader(f'📰 Latest News für {ticker}')
                        for news in item['news'][:5]:
                            st.write(f"**{news.get('headline', '')}**")
                            st.write(f"{str(news.get('summary', ''))[:150]}...")
                            if news.get('url'):
                                st.link_button('📖 Vollständiger Artikel', news['url'])
                            st.write(f"*{news.get('datetime', '')} | Semantik: {news.get('sentiment', 'neutral')}*")
                            st.divider()
        else:
            st.warning('Konnte Watchlist-Daten nicht laden.')

with tab3:
    st.header('⚡ Gewinner')
    st.write('Hier kannst du später die stärksten Kursgewinner anzeigen.')
    st.info('Dieser Tab ist vorbereitet und kann mit den Top-Performern gefüllt werden.')

with tab4:
    st.header('🔥 Verlierer')
    st.write('Hier kannst du später die stärksten Kursverlierer anzeigen.')
    st.info('Dieser Tab ist vorbereitet und kann mit den stärksten Minus-Aktien gefüllt werden.')

with tab5:
    st.header('ℹ️ Info')
    st.write('Dieses Tool zeigt Markt-News, Watchlist-Kurse und einfache Kursanalysen.')
    st.write('News werden ins Deutsche übersetzt.')
    st.write('Die Marktwirkung basiert auf einer einfachen Schlagwort-Analyse.')
    st.write('Die API kann in der Sidebar eingegeben werden.')
