"""
Stock Market News & Watchlist Tool
Tägliche Benachrichtigungen über Aktienmarktbewegungen, News, Live-Watchlist und Analyse-Tools
Nutzt Finnhub API für Echtzeit-Daten
"""

import streamlit as st
import finnhub
import requests
from datetime import datetime, timedelta
import pandas as pd
import json
import time

# Seitenkonfiguration
st.set_page_config(
    page_title="Stock Market News & Watchlist",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS für besseres Design
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e88e5;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive {
        color: #2e7d32;
        font-weight: bold;
    }
    .negative {
        color: #c62828;
        font-weight: bold;
    }
    .news-card {
        background-color: #fff3e0;
        padding: 1rem;
        border-left: 4px solid #ff9800;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar für API-Key und Einstellungen
with st.sidebar:
    st.header("⚙️ Einstellungen")

    # API-Key eingabe
    api_key = st.text_input(
        "Finnhub API-Key",
        type="password",
        help="Dein Finnhub API-Key (kostenlos unter: https://finnhub.io/register)"
    )

    if api_key:
        st.session_state['api_key'] = api_key
        st.success("API-Key gespeichert!")

    st.divider()

    # Watchlist Management
    st.header("📝 Watchlist")

    if 'watchlist' not in st.session_state:
        st.session_state['watchlist'] = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN']

    st.info(f"Wachlist hat {len(st.session_state['watchlist'])} Aktien")

    # Neue Aktie hinzufügen
    new_stock = st.text_input(
        "Neue Aktie hinzufügen (Ticker)",
        placeholder="z.B. NVDA",
        key="new_stock_input"
    )

    if st.button("➕ Zur Watchlist hinzufügen", key="add_stock_btn"):
        if new_stock.upper() not in st.session_state['watchlist'] and new_stock.strip():
            st.session_state['watchlist'].append(new_stock.upper())
            st.success(f"{new_stock.upper()} hinzugefügt!")
            st.rerun()

    # Watchlist anzeigen und bearbeiten
    st.subheader("Aktuelle Watchlist")
    for i, ticker in enumerate(st.session_state['watchlist']):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"📌 {ticker}")
        with col2:
            if st.button("🗑️", key=f"remove_{i}"):
                st.session_state['watchlist'].pop(i)
                st.rerun()

    st.divider()

    # Benachrichtigungseinstellungen
    st.header("🔔 Benachrichtigungen")

    notify_until = st.checkbox(
        "Tägliche Marktupdates aktivieren",
        value=True,
        key="daily_notify"
    )

    notify_news = st.checkbox(
        "Wichtige News-API aktivieren",
        value=True,
        key="news_notify"
    )

    st/info("""
    **Hinweis**: Dieses Tool zeigt nur Analysen und Informationen. 
    Es ist **keine Kaufberatung**.
    """)

# Haupt-Funktionen
def get_finnhub_client():
    """Erstellt Finnhub Client aus gespeichertem API-Key"""
    api_key = st.session_state.get('api_key', '')
    if not api_key:
        st.error("❌ Bitte zuerst Finnhub API-Key in der Sidebar eingeben!")
        return None
    return finnhub.Client(api_key=api_key)

def get_stock_quote(ticker):
    """Holt aktuellen Kurs für eine Aktie"""
    client = get_finnhub_client()
    if not client:
        return None
    try:
        quote = client.quote(ticker)
        return quote
    except Exception as e:
        st.warning(f"Konnte {ticker} nicht laden: {str(e)}")
        return None

def get_stock_news(ticker, days=7):
    """Holt News für eine spezifische Aktie"""
    client = get_finnhub_client()
    if not client:
        return []
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        news = client.company_news(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        return news[:20]  # Max 20 News
    except Exception as e:
        st.warning(f"Konnte News für {ticker} nicht laden: {str(e)}")
        return []

def get_general_market_news(days=1):
    """Holt allgemeine Markt-News"""
    client = get_finnhub_client()
    if not client:
        return []
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        # Allgemeine Markt-News (ohne spezifischen Ticker)
        news = client.general_news(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        return news[:30]  # Max 30 News
    except Exception as e:
        st.warning(f"Konnte Markt-News nicht laden: {str(e)}")
        return []

def get_recommendations(ticker):
    """Holt Analysten-Empfehlungen"""
    client = get_finnhub_client()
    if not client:
        return None
    try:
        rec = client.stock_recommendations(ticker)
        if rec:
            return rec[-1]  # Neueste Empfehlung
        return None
    except Exception as e:
        return None

def calculate_buy_recommendation(current_price, ticker):
    """Analysiert beste Kaufoption basierend auf Volatilität"""
    # Einfache Analyse basierend auf typischen Mustern
    quote = get_stock_quote(ticker)
    if not quote or quote['c'] == 0:
        return None

    current = quote['c']
    change = quote['d']
    change_percent = quote['dp']

    recommendations = {
        'current_price': current,
        'change': change,
        'change_percent': change_percent,
        'analysis': []
    }

    # Analyse der Kaufoptionen
    if change_percent > 2:
        recommendations['analysis'].append({
            'option': 'Limit Order',
            'reason': f"Aktie steigt stark ({change_percent:.2f}%). Limit Order bei {current*0.97:.2f} könnte besseren Einstiegspreis bieten.",
            'confidence': 'medium',
            'price_suggestion': current * 0.97
        })
        recommendations['analysis'].append({
            'option': 'Warten auf Rücksetzer',
            'reason': f"Starker Anstieg könnte Korrektur folgen. Warte auf Rücksetzer zu {current*0.95:.2f}.",
            'confidence': 'high',
            'price_suggestion': current * 0.95
        })
    elif change_percent < -2:
        recommendations['analysis'].append({
            'option': 'Market Order',
            'reason': f"Aktie fällt stark ({change_percent:.2f}%). Guter Einstiegspreis könnte erreicht werden.",
            'confidence': 'medium',
            'price_suggestion': current
        })
        recommendations['analysis'].append({
            'option': 'Limit Order',
            'reason': f"Setze Limit bei {current*0.98:.2f} für noch besseren Preis.",
            'confidence': 'low',
            'price_suggestion': current * 0.98
        })
    else:
        recommendations['analysis'].append({
            'option': 'Limit Order',
            'reason': f"Seitwärtsbewegung. Limit Order bei {current*0.99:.2f} ist sicher.",
            'confidence': 'high',
            'price_suggestion': current * 0.99
        })
        recommendations['analysis'].append({
            'option': 'Market Order',
            'reason': "Wenn du sofort einsteigen willst, nutze Market Order.",
            'confidence': 'medium',
            'price_suggestion': current
        })

    return recommendations

# Haupt-Seite
st.markdown('<p class="main-header">📈 Stock Market News & Watchlist Tool</p>', unsafe_allow_html=True)
st.markdown("Tägliche Marktupdates, Live-Watchlist und Analyse-Tools")

if 'api_key' not in st.session_state:
    st.warning("⚠️ **Bitte Finnhub API-Key in der Sidebar eingehen**, um fortzufahren.")
    st.info("📌 Du kannst einen kostenlosen API-Key bei [Finnhub.io](https://finnhub.io/register) erhalten.")
    st.stop()

# Tabs für verschiedene Funktionen
tab1, tab2, tab3, tab4 = st.tabs([
    "🔥 Tägliches Markt-Update",
    "📊 Live Watchlist",
    "💡 Aktie/Krypto Tipps",
    "🎯 Kaufoptionen-Analyse"
])

# TAB 1: Tägliches Markt-Update
with tab1:
    st.header("📰 Tägliches Markt-Update")
    st.markdown("Die wichtigsten Marktnews und Kursbewegungen für today")

    if st.button("🔄 Markt-Updates aktualisieren", key="refresh_market_news"):
        st.session_state['market_news_loaded'] = False
        st.rerun()

    if 'market_news_loaded' not in st.session_state or not st.session_state['market_news_loaded']:
        with st.spinner("Lade Markt-News..."):
            general_news = get_general_market_news(days=1)
            st.session_state['general_news'] = general_news
            st.session_state['market_news_loaded'] = True

    general_news = st.session_state.get('general_news', [])

    if general_news:
        st.success(f"✅ {len(general_news)} News gefunden")

        # Wichtige News hervorheben (mit sentiment)
        important_news = []
        for news in general_news[:15]:
            sentiment = news.get('sentiment', 'neutral')
            if sentiment in ['positive', 'veryPositive'] or news['priceSensitive']:
                important_news.append(news)

        if important_news:
            st.subheader("🚨 Potenziell kursrelevante News")
            for news in important_news[:10]:
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <strong>{news['headline']}</strong><br>
                        <small>{news['summary'][:200]}...</small><br>
                        <small>📊 Sammlung: {news.get('symbol', 'N/A')} | ⏰ {news['datetime']}</small><br>
                        <small>Emotion: <strong>{news.get('sentiment', 'neutral')}</strong></small>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button("📖 Vollständiger Artikel", news['url'])
                    st.divider()

        st.subheader("📰 Alle Markt-News")
        for news in general_news[10:25]:
            with st.expander(f"{news['headline']}"):
                st.write(news['summary'])
                st.link_button("📖 Zum Artikel", news['url'])
                st.write(f"**Semantik:** {news.get('sentiment', 'neutral')} | **Zeitraum:** {news['datetime']}")
    else:
        st.info("Noch keine News geladen. Klicke auf "Markt-Updates aktualisieren".")

# TAB 2: Live Watchlist
with tab2:
    st.header("📊 Live Watchlist")
    st.markdown("Echtzeit-Kurse und Analysen deiner Watchlist")

    if st.button("🔄 Watchlist aktualisieren", key="refresh_watchlist"):
        st.session_state['watchlist_data'] = None
        st.rerun()

    if 'watchlist' not in st.session_state or len(st.session_state['watchlist']) == 0:
        st.info("📝 Deine Watchlist ist leer. Füge Aktiew in der Sidebar hinzu.")
        st.stop()

    if 'watchlist_data' not in st.session_state or st.session_state['watchlist_data'] is None:
        with st.spinner("Lade Watchlist-Daten..."):
            watchlist_data = []
            for ticker in st.session_state['watchlist']:
                quote = get_stock_quote(ticker)
                news = get_stock_news(ticker, days=7)
                rec = get_recommendations(ticker)

                if quote:
                    watchlist_data.append({
                        'ticker': ticker,
                        'quote': quote,
                        'news': news,
                        'recommendations': rec
                    })

            st.session_state['watchlist_data'] = watchlist_data

    watchlist_data = st.session_state.get('watchlist_data', [])

    if watchlist_data:
        # Übersichtstabelle
        st.subheader("📈 Watchlist Überblick")

        df_data = []
        for item in watchlist_data:
            quote = item['quote']
            df_data.append({
                'Ticker': item['ticker'],
                'Preis ($)': f"{quote['c']:.2f}",
                'Änderung ($)': f"{quote['d']:.2f}",
                'Änderung (%)': f"{quote['dp']:.2f}%",
                'Volumen': f"{quote['v']:,}",
                'Hohe ($)': f"{quote['h']:.2f}",
                'Niedrige ($)': f"{quote['l']:.2f}"
            })

        df = pd.DataFrame(df_data)

        # Farbige Änderungsspalte
        def color_change(val):
            if '%' in val:
                num = float(val.replace('%', ''))
                if num > 0:
                    return 'color: green; font-weight: bold;'
                elif num < 0:
                    return 'color: red; font-weight: bold;'
            return ''

        st.dataframe(
            df.style.applymap(color_change, subset=['Änderung (%)']),
            use_container_width=True,
            hide_index=True
        )

        # Einzelne Aktien Details
        st.subheader("🔍 Aktie Details")

        for item in watchlist_data:
            with st.expander(f"📌 {item['ticker']} - ${item['quote']['c']:.2f}"):
                quote = item['quote']

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Aktueller Preis", f"${quote['c']:.2f}")
                with col2:
                    change_color = "positive" if quote['d'] > 0 else "negative"
                    st.markdown(f"""
                    <div class="{change_color}">
                        Änderung: ${quote['d']:.2f} ({quote['dp']:.2f}%)
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.metric("Volumen", f"{quote['v']:,}")

                # Analysten-Empfehlungen
                if item['recommendations']:
                    st.subheader("👨‍💼 Analysten-Empfehlungen")
                    rec = item['recommendations']
                    st.write(f"**Period:** {rec['period']}")
                    st.write(f"**Strong Buy:** {rec['strongBuy']}")
                    st.write(f"**Buy:** {rec['buy']}")
                    st.write(f"**Hold:** {rec['hold']}")
                    st.write(f"**Sell:** {rec['sell']}")
                    st.write(f"**Strong Sell:** {rec['strongSell']}")

                # News für diese Aktie
                if item['news']:
                    st.subheader(f"📰 Latest News für {item['ticker']}")
                    for news in item['news'][:5]:
                        st.write(f"**{news['headline']}**")
                        st.write(f"{news['summary'][:150]}...")
                        st.link_button("📖 Vollständiger Artikel", news['url'])
                        st.write(f"*{news['datetime']} | Semantik: {news.get('sentiment', 'neutral')}*")
                        st.divider()
    else:
        st.warning("Konnte Watchlist-Daten nicht laden.")

# TAB 3: Aktie/Krypto Tipps
with tab3:
    st.header("💡 Potenzielle Gewinner dieser Woche")
    st.markdown("""
    **Hinweis**: Dies sind Analysen basierend auf aktuellen Marktdaten und News. 
    **Keine Kaufberatung**. Immer eigene Recherche durchführen.
    """)

    st.subheader("🔥 Heute/Woche: Potenzielle Gewinner")

    if st.button("🔄 Tipps aktualisieren", key="refresh_tips"):
        st.session_state['tips_loaded'] = False
        st.rerun()

    if 'tips_loaded' not in st.session_state or not st.session_state['tips_loaded']:
        with st.spinner("Analysiere Markt für potenzielle Gewinner..."):
            # Suche nach Aktien mit positiven News und starken Kursbewegungen
            potential_winners = []

            # Überprüfe Watchlist-Aktien
            for ticker in st.session_state.get('watchlist', []):
                quote = get_stock_quote(ticker)
                news = get_stock_news(ticker, days=3)

                if quote and quote['dp'] > 1:  # Mehr als 1% Steigung
                    positive_news = [n for n in news if n.get('sentiment') in ['positive', 'veryPositive']]
                    if positive_news or quote['dp'] > 2:
                        potential_winners.append({
                            'ticker': ticker,
                            'change_percent': quote['dp'],
                            'current_price': quote['c'],
                            'positive_news_count': len(positive_news),
                            'reason': f"Starker Anstieg ({quote['dp']:.2f}%) {'+ positive News' if positive_news else ''}"
                        })

            # Allgemeine News durchsuchen für potenzielle Gewinner
            general_news = get_general_market_news(days=1)
            for news in general_news:
                if news.get('sentiment') in ['positive', 'veryPositive'] and news.get('priceSensitive'):
                    symbols = news.get('symbol', '')
                    if symbols:
                        for symbol in symbols.split(','):
                            symbol = symbol.strip()
                            if symbol and len(symbol) < 6:
                                quote = get_stock_quote(symbol)
                                if quote and quote['dp'] > 0:
                                    potential_winners.append({
                                        'ticker': symbol,
                                        'change_percent': quote['dp'],
                                        'current_price': quote['c'],
                                        'positive_news_count': 1,
                                        'reason': f"Positive News + {quote['dp']:.2f}% Steigung"
                                    })

            # Sortieren nach stärkstem Anstieg
            potential_winners = sorted(potential_winners, key=lambda x: x['change_percent'], reverse=True)
            st.session_state['potential_winners'] = potential_winners[:15]
            st.session_state['tips_loaded'] = True

    potential_winners = st.session_state.get('potential_winners', [])

    if potential_winners:
        st.success(f"✅ {len(potential_winners)} potenzielle Gewinner gefunden")

        for winner in potential_winners[:10]:
            with st.container():
                change_color = "positive" if winner['change_percent'] > 0 else "negative"
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
        st.info("Keine klaren Gewinner gefunden. Überprüfe später erneut oder füge mehr Aktien zur Watchlist hinzu.")

    st.divider()
    st.subheader("🎯 Was du heute genauer ansehen solltest")
    st.markdown("""
    **Kriterien für Aufmerksamkeit**:
    - Aktie mit >2% Kursänderung heute
    - Positive News mit "priceSensitive" Flag
    - Hohe Volatilität (große Spanne zwischen High/Low)
    - Starke Analysten-Empfehlungen (mehr Buy als Sell)
    """)

# TAB 4: Kaufoptionen-Analyse
with tab4:
    st.header("🎯 Beste Kaufoption für deine Watchlist")
    st.markdown("""
    **Analyse welcher Order-Typ** (Limit, Market, Stop-Loss) für jede Aktie in deiner Watchlist 
    die höchsten Gewinnchancen bietet.

    **Hinweis**: Dies ist **keine Kaufberatung**, sondern nur analytische Information.
    """)

    if st.button("🔄 Kaufoptionen analysieren", key="analyze_buy_options"):
        st.session_state['buy_analysis'] = None
        st.rerun()

    if 'buy_analysis' not in st.session_state or st.session_state['buy_analysis'] is None:
        with st.spinner("Analysiere Kaufoptionen..."):
            buy_analysis = {}

            for ticker in st.session_state.get('watchlist', []):
                analysis = calculate_buy_recommendation(None, ticker)
                if analysis:
                    buy_analysis[ticker] = analysis

            st.session_state['buy_analysis'] = buy_analysis

    buy_analysis = st.session_state.get('buy_analysis', {})

    if buy_analysis:
        for ticker, analysis in buy_analysis.items():
            with st.expander(f"📊 {ticker} - ${analysis['current_price']:.2f} ({analysis['change_percent']:.2f}%)"):
                st.subheader("Kursänderung")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Änderung ($)", f"${analysis['change']:.2f}")
                with col2:
                    change_color = "positive" if analysis['change_percent'] > 0 else "negative"
                    st.markdown(f"""
                    <div class="{change_color}">
                        Änderung (%): {analysis['change_percent']:.2f}%
                    </div>
                    """, unsafe_allow_html=True)

                st.subheader("Empfohlene Kaufoptionen")

                for i, rec in enumerate(analysis['analysis']):
                    confidence_emoji = {
                        'high': '✅',
                        'medium': '⚠️',
                        'low': '🔻'
                    }.get(rec['confidence'], '❓')

                    st.markdown(f"""
                    **{confidence_emoji} {rec['option']}** (Vertrauen: {rec['confidence']})
                    """)
                    st.write(f"*Grund: {rec['reason']}*")
                    if rec['price_suggestion']:
                        st.write(f"*Vorgeschlagener Preis: ${rec['price_suggestion']:.2f}*")
                    st.divider()
    else:
        st.info("Klicke auf "Kaufoptionen analysieren" um zu starten.")

# Footer
st.divider()
st.markdown("""
---
**⚠️ Haftungsausschluss**: Dieses Tool bietet nur Analysen und Informationen. 
Es ist **keine Kaufberatung**. Investiere nur Geld, das du verlieren kannst. 
Führe immer eigene Recherche durch (**DYOR**).

**Datenquelle**: [Finnhub.io](https://finnhub.io) - Institutional-grade Financial Data
""")
