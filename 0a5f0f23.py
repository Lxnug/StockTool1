"""
Stock Market News & Watchlist Tool
"""

import streamlit as st
import finnhub
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Stock Market News & Watchlist", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; color: #1e88e5; margin-bottom: 1rem; }
.metric-card { background-color: #f5f5f5; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; }
.positive { color: #2e7d32; font-weight: bold; }
.negative { color: #c62828; font-weight: bold; }
.news-card { background-color: #fff3e0; padding: 1rem; border-left: 4px solid #ff9800; margin: 0.5rem 0; border-radius: 0.25rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Einstellungen")
    api_key = st.text_input("Finnhub API-Key", type="password")
    if api_key:
        st.session_state['api_key'] = api_key
        st.success("API-Key gespeichert!")

    st.divider()
    st.header("📝 Watchlist")
    if 'watchlist' not in st.session_state:
        st.session_state['watchlist'] = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN']

    st.info(f"Watchlist hat {len(st.session_state['watchlist'])} Aktien")
    new_stock = st.text_input("Neue Aktie hinzufügen (Ticker)", placeholder="z.B. NVDA", key="new_stock_input")
    if st.button("➕ Zur Watchlist hinzufügen", key="add_stock_btn"):
        if new_stock.strip() and new_stock.upper() not in st.session_state['watchlist']:
            st.session_state['watchlist'].append(new_stock.upper())
            st.success(f"{new_stock.upper()} hinzugefügt!")
            st.rerun()

    st.subheader("Aktuelle Watchlist")
    for i, ticker in enumerate(list(st.session_state['watchlist'])):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"📌 {ticker}")
        with c2:
            if st.button("🗑️", key=f"remove_{i}"):
                st.session_state['watchlist'].pop(i)
                st.rerun()

    st.divider()
    st.header("🔔 Benachrichtigungen")
    st.checkbox("Tägliche Marktupdates aktivieren", value=True, key="daily_notify")
    st.checkbox("Wichtige News-API aktivieren", value=True, key="news_notify")
    st.info('Dieses Tool zeigt nur Analysen und Informationen. Es ist keine Kaufberatung.')


def get_finnhub_client():
    api_key = st.session_state.get('api_key', '')
    if not api_key:
        st.error("❌ Bitte zuerst Finnhub API-Key in der Sidebar eingeben!")
        return None
    return finnhub.Client(api_key=api_key)


def get_stock_quote(ticker):
    client = get_finnhub_client()
    if not client:
        return None
    try:
        return client.quote(ticker)
    except Exception as e:
        st.warning(f"Konnte {ticker} nicht laden: {e}")
        return None


def get_stock_news(ticker, days=7):
    client = get_finnhub_client()
    if not client:
        return []
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return client.company_news(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))[:20]
    except Exception as e:
        st.warning(f"Konnte News für {ticker} nicht laden: {e}")
        return []


def get_general_market_news(days=1):
    client = get_finnhub_client()
    if not client:
        return []
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return client.general_news(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))[:30]
    except Exception as e:
        st.warning(f"Konnte Markt-News nicht laden: {e}")
        return []


def get_recommendations(ticker):
    client = get_finnhub_client()
    if not client:
        return None
    try:
        rec = client.stock_recommendations(ticker)
        return rec[-1] if rec else None
    except Exception:
        return None


def calculate_buy_recommendation(ticker):
    quote = get_stock_quote(ticker)
    if not quote or quote.get('c', 0) == 0:
        return None
    current = quote['c']
    change = quote['d']
    change_percent = quote['dp']
    result = {'current_price': current, 'change': change, 'change_percent': change_percent, 'analysis': []}

    if change_percent > 2:
        result['analysis'].append({'option': 'Limit Order', 'reason': f'Aktie steigt stark ({change_percent:.2f}%). Limit Order bei {current*0.97:.2f} könnte besseren Einstiegspreis bieten.', 'confidence': 'medium', 'price_suggestion': current * 0.97})
        result['analysis'].append({'option': 'Warten auf Rücksetzer', 'reason': f'Starker Anstieg könnte Korrektur folgen. Warte auf Rücksetzer zu {current*0.95:.2f}.', 'confidence': 'high', 'price_suggestion': current * 0.95})
    elif change_percent < -2:
        result['analysis'].append({'option': 'Market Order', 'reason': f'Aktie fällt stark ({change_percent:.2f}%). Guter Einstiegspreis könnte erreicht werden.', 'confidence': 'medium', 'price_suggestion': current})
        result['analysis'].append({'option': 'Limit Order', 'reason': f'Setze Limit bei {current*0.98:.2f} für noch besseren Preis.', 'confidence': 'low', 'price_suggestion': current * 0.98})
    else:
        result['analysis'].append({'option': 'Limit Order', 'reason': f'Seitwärtsbewegung. Limit Order bei {current*0.99:.2f} ist sicher.', 'confidence': 'high', 'price_suggestion': current * 0.99})
        result['analysis'].append({'option': 'Market Order', 'reason': 'Wenn du sofort einsteigen willst, nutze Market Order.', 'confidence': 'medium', 'price_suggestion': current})
    return result


st.markdown('<p class="main-header">📈 Stock Market News & Watchlist Tool</p>', unsafe_allow_html=True)
st.markdown('Tägliche Marktupdates, Live-Watchlist und Analyse-Tools')

if 'api_key' not in st.session_state:
    st.warning('⚠️ Bitte Finnhub API-Key in der Sidebar eingeben, um fortzufahren.')
    st.info('📌 Du kannst einen kostenlosen API-Key bei Finnhub.io erhalten.')
    st.stop()


tab1, tab2, tab3, tab4 = st.tabs(['🔥 Tägliches Markt-Update', '📊 Live Watchlist', '💡 Aktie/Krypto Tipps', '🎯 Kaufoptionen-Analyse'])

with tab1:
    st.header('📰 Tägliches Markt-Update')
    st.markdown('Die wichtigsten Marktnews und Kursbewegungen für heute')

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

        if headline and summary:
            short_de = f'{headline}. {summary[:220]}'
        elif headline:
            short_de = headline
        elif summary:
            short_de = summary[:220]
        else:
            short_de = 'Keine verwertbare Meldung vorhanden.'

        if pos_hits:
            reason = f'Positive Schlagwörter gefunden: {", ".join(pos_hits[:4])}'
        elif neg_hits:
            reason = f'Negative Schlagwörter gefunden: {", ".join(neg_hits[:4])}'
        else:
            reason = 'Keine klaren Kurs-Treiber erkannt; eher neutrale Meldung.'

        return {
            'direction': direction,
            'impact': impact,
            'color': color,
            'short_de': short_de,
            'reason': reason
        }

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
                    <strong>{impact['color']} {title}</strong><br>
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
            with st.expander(f"{impact['color']} {title}"):
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
        st.stop()

    if 'watchlist_data' not in st.session_state or st.session_state['watchlist_data'] is None:
        with st.spinner('Lade Watchlist-Daten...'):
            watchlist_data = []
            for ticker in st.session_state['watchlist']:
                quote = get_stock_quote(ticker)
                news = get_stock_news(ticker, days=7)
                rec = get_recommendations(ticker)
                if quote and isinstance(quote, dict):
                    watchlist_data.append({
                        'ticker': ticker,
                        'quote': quote,
                        'news': news,
                        'recommendations': rec
                    })
            st.session_state['watchlist_data'] = watchlist_data

    watchlist_data = st.session_state.get('watchlist_data', [])
    if watchlist_data:
        st.subheader('📈 Watchlist Überblick')
        rows = []
        for item in watchlist_data:
            q = item.get('quote', {})
            rows.append({
                'Ticker': item.get('ticker', ''),
                'Preis ($)': f"{q.get('c', 0):.2f}",
                'Änderung ($)': f"{q.get('d', 0):.2f}",
                'Änderung (%)': f"{q.get('dp', 0):.2f}%",
                'Volumen': f"{q.get('v', 0):,}",
                'High ($)': f"{q.get('h', 0):.2f}",
                'Low ($)': f"{q.get('l', 0):.2f}"
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader('🔍 Aktie Details')
        for item in watchlist_data:
            q = item.get('quote', {})
            ticker = item.get('ticker', '')
            current_price = q.get('c', 0)
            change = q.get('d', 0)
            change_percent = q.get('dp', 0)
            volume = q.get('v', 0)

            with st.expander(f'📌 {ticker} - ${current_price:.2f}'):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric('Aktueller Preis', f'${current_price:.2f}')
                with c2:
                    st.markdown(
                        f"<div class={'positive' if change > 0 else 'negative'}>Änderung: ${change:.2f} ({change_percent:.2f}%)</div>",
                        unsafe_allow_html=True
                    )
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
    st.header('💡 Potenzielle Gewinner diese Woche')
    st.markdown('Analyse basierend auf aktuellen Marktdaten und News. Keine Kaufberatung.')
    if st.button('🔄 Tipps aktualisieren', key='refresh_tips'):
        st.session_state['tips_loaded'] = False
        st.rerun()
    if 'tips_loaded' not in st.session_state or not st.session_state['tips_loaded']:
        with st.spinner('Analysiere Markt für potenzielle Gewinner...'):
            potential_winners = []
            for ticker in st.session_state.get('watchlist', []):
                quote = get_stock_quote(ticker)
                news = get_stock_news(ticker, days=3)
                if quote and quote.get('dp', 0) > 1:
                    positive_news = [n for n in news if n.get('sentiment') in ['positive', 'veryPositive']]
                    if positive_news or quote['dp'] > 2:
                        potential_winners.append({'ticker': ticker, 'change_percent': quote['dp'], 'current_price': quote['c'], 'positive_news_count': len(positive_news), 'reason': f"Starker Anstieg ({quote['dp']:.2f}%) {'+ positive News' if positive_news else ''}"})
            general_news = get_general_market_news(days=1)
            for news in general_news:
                if news.get('sentiment') in ['positive', 'veryPositive'] and news.get('priceSensitive'):
                    symbols = news.get('symbol', '')
                    if symbols:
                        for symbol in symbols.split(','):
                            symbol = symbol.strip()
                            if symbol and len(symbol) < 6:
                                quote = get_stock_quote(symbol)
                                if quote and quote.get('dp', 0) > 0:
                                    potential_winners.append({'ticker': symbol, 'change_percent': quote['dp'], 'current_price': quote['c'], 'positive_news_count': 1, 'reason': f"Positive News + {quote['dp']:.2f}% Steigung"})
            st.session_state['potential_winners'] = sorted(potential_winners, key=lambda x: x['change_percent'], reverse=True)[:15]
            st.session_state['tips_loaded'] = True
    potential_winners = st.session_state.get('potential_winners', [])
    if potential_winners:
        st.success(f"✅ {len(potential_winners)} potenzielle Gewinner gefunden")
        for winner in potential_winners[:10]:
            change_color = 'positive' if winner['change_percent'] > 0 else 'negative'
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 {winner['ticker']}</h3>
                <p>Aktueller Preis: <strong>${winner['current_price']:.2f}</strong></p>
                <p class="{change_color}">Änderung: {winner['change_percent']:.2f}%</p>
                <p><em>Begründung: {winner['reason']}</em></p>
                <p>Positive News: {winner['positive_news_count']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info('Keine klaren Gewinner gefunden. Überprüfe später erneut oder füge mehr Aktien hinzu.')
    st.divider()
    st.subheader('🎯 Was du heute genauer ansehen solltest')
    st.markdown('''- Aktie mit mehr als 2% Kursänderung heute.
- Positive News mit priceSensitive Flag.
- Hohe Volatilität.
- Starke Analysten-Empfehlungen.''')

with tab4:
    st.header('🎯 Beste Kaufoption für deine Watchlist')
    st.markdown('Analyse, welcher Order-Typ für jede Aktie in deiner Watchlist am ehesten passend ist. Keine Kaufberatung.')
    if st.button('🔄 Kaufoptionen analysieren', key='analyze_buy_options'):
        st.session_state['buy_analysis'] = None
        st.rerun()
    if 'buy_analysis' not in st.session_state or st.session_state['buy_analysis'] is None:
        with st.spinner('Analysiere Kaufoptionen...'):
            buy_analysis = {}
            for ticker in st.session_state.get('watchlist', []):
                analysis = calculate_buy_recommendation(ticker)
                if analysis:
                    buy_analysis[ticker] = analysis
            st.session_state['buy_analysis'] = buy_analysis
    buy_analysis = st.session_state.get('buy_analysis', {})
    if buy_analysis:
        for ticker, analysis in buy_analysis.items():
            with st.expander(f"📊 {ticker} - ${analysis['current_price']:.2f} ({analysis['change_percent']:.2f}%)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric('Änderung ($)', f"${analysis['change']:.2f}")
                with c2:
                    st.markdown(f"<div class={'positive' if analysis['change_percent'] > 0 else 'negative'}>Änderung (%): {analysis['change_percent']:.2f}%</div>", unsafe_allow_html=True)
                st.subheader('Empfohlene Kaufoptionen')
                for rec in analysis['analysis']:
                    emoji = {'high': '✅', 'medium': '⚠️', 'low': '🔻'}.get(rec['confidence'], '❓')
                    st.markdown(f"**{emoji} {rec['option']}** (Vertrauen: {rec['confidence']})")
                    st.write(f"*Grund: {rec['reason']}*")
                    st.write(f"*Vorgeschlagener Preis: ${rec['price_suggestion']:.2f}*")
                    st.divider()
    else:
        st.info('Klicke auf "Kaufoptionen analysieren" um zu starten.')

st.divider()
st.markdown('''---
**⚠️ Haftungsausschluss**: Dieses Tool bietet nur Analysen und Informationen. Es ist keine Kaufberatung. Investiere nur Geld, das du verlieren kannst. Führe immer eigene Recherche durch (DYOR).''')
