import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
from requests_ratelimiter import LimiterSession

warnings.filterwarnings("ignore")

session = LimiterSession(per_second=0.5)

# Configuração da página para telemóvel
st.set_page_config(page_title="Stock Scorer", page_icon="📈", layout="centered")

# Estilo CSS para melhorar o visual no ecrã do tlm
st.markdown("""
    <style>
    .stApp {background-color: #0e1117; color: #ffffff;}
    .metric-card {
        background-color: #1f2937; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 12px;
    }
    .score-title {
        font-size: 20px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def get_score_label(score):
    if score >= 80: return "⭐⭐⭐⭐⭐ EXCELENTE"
    elif score >= 65: return "⭐⭐⭐⭐ MUITO BOM"
    elif score >= 50: return "⭐⭐⭐ BOM"
    elif score >= 35: return "⭐⭐ RAZOÁVEL"
    else: return "⭐ FRACO"

def safe_get(d, key, default=None):
    val = d.get(key, default)
    if val is None or val != val:
        return default
    return val

def calcular_dados_ticker(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol, session=session)
        info = ticker.info

        if not info or "symbol" not in info:
            return {"error": "Ticker não encontrado ou sem dados na API."}

        scores = {}
        details = {}

        # 1. CRESCIMENTO (20 pts)
        rev_growth = safe_get(info, "revenueGrowth")
        earnings_growth = safe_get(info, "earningsGrowth")
        
        surprise_avg = None
        try:
            calendar = ticker.get_earnings_dates(limit=4)
            if calendar is not None and "Surprise(%)" in calendar.columns:
                surprises = calendar["Surprise(%)"].dropna().values
                if len(surprises) > 0:
                    surprise_avg = float(np.mean(surprises))
        except:
            pass

        g = 0
        if rev_growth is not None:
            if rev_growth > 0.30: g += 10
            elif rev_growth > 0.15: g += 7
            elif rev_growth > 0.05: g += 4
            elif rev_growth > 0:   g += 1

        if earnings_growth is not None:
            if earnings_growth > 0.30: g += 6
            elif earnings_growth > 0.15: g += 4
            elif earnings_growth > 0:   g += 1

        if surprise_avg is not None and surprise_avg > 0:
            if surprise_avg > 10.0: g += 4
            elif surprise_avg > 2.0: g += 2
            else: g += 1

        scores["crescimento"] = min(g, 20)
        details["revenue_growth"]   = f"{rev_growth*100:.1f}%"   if rev_growth   is not None else "N/A"
        details["earnings_growth"]  = f"{earnings_growth*100:.1f}%" if earnings_growth is not None else "N/A"
        details["earnings_surprise"] = f"{surprise_avg:+.1f}%" if surprise_avg is not None else "N/A"

        # 2. RENTABILIDADE (20 pts)
        gross_margin  = safe_get(info, "grossMargins")       
        op_margin     = safe_get(info, "operatingMargins")
        profit_margin = safe_get(info, "profitMargins")
        roe           = safe_get(info, "returnOnEquity")
        roa           = safe_get(info, "returnOnAssets")

        r = 0
        if gross_margin is not None:
            if gross_margin > 0.60: r += 6  
            elif gross_margin > 0.40: r += 4
            elif gross_margin > 0.20: r += 2

        if op_margin is not None:
            if op_margin > 0.30: r += 6
            elif op_margin > 0.15: r += 4
            elif op_margin > 0.05: r += 2

        if profit_margin is not None:
            if profit_margin > 0.25: r += 4
            elif profit_margin > 0.15: r += 2
            elif profit_margin > 0.05: r += 1

        roe_roa_bonus = 0
        if roe is not None and roe > 0.15: roe_roa_bonus += 2
        if roa is not None and roa > 0.08: roe_roa_bonus += 2
        r += min(roe_roa_bonus, 4)

        scores["rentabilidade"] = min(r, 20)
        details["gross_margin"]    = f"{gross_margin*100:.1f}%" if gross_margin is not None else "N/A"
        details["operating_margin"]= f"{op_margin*100:.1f}%"  if op_margin     is not None else "N/A"
        details["profit_margin"]   = f"{profit_margin*100:.1f}%" if profit_margin is not None else "N/A"
        details["roe"]             = f"{roe*100:.1f}%"        if roe           is not None else "N/A"
        details["roa"]             = f"{roa*100:.1f}%"        if roa           is not None else "N/A"

        # 3. VALORAÇÃO (20 pts)
        peg        = safe_get(info, "trailingPegRatio")
        ev_ebitda  = safe_get(info, "enterpriseToEbitda")
        pe         = safe_get(info, "trailingPE")
        ps         = safe_get(info, "priceToSalesTrailing12Months")

        v = 0
        if peg is not None and peg > 0:
            if peg < 1.0: v += 7
            elif peg < 1.5: v += 5
            elif peg < 2.5: v += 3
            elif peg < 4.0: v += 1

        if ev_ebitda is not None and ev_ebitda > 0:
            if ev_ebitda < 12:  v += 6
            elif ev_ebitda < 20: v += 4
            elif ev_ebitda < 30: v += 2
            elif ev_ebitda < 50: v += 1

        if pe is not None and pe > 0:
            if pe < 20:  v += 4
            elif pe < 35: v += 3
            elif pe < 60: v += 1

        if ps is not None and ps > 0:
            if ps < 4:   v += 3
            elif ps < 8:  v += 2
            elif ps < 15: v += 1

        scores["valoracao"] = min(v, 20)
        details["peg_ratio"]  = f"{peg:.2f}"        if peg       and peg > 0       else "N/A"
        details["ev_ebitda"]  = f"{ev_ebitda:.1f}x" if ev_ebitda and ev_ebitda > 0 else "N/A"
        details["pe_ratio"]   = f"{pe:.1f}x"       if pe        and pe > 0        else "N/A"
        details["price_to_sales"] = f"{ps:.1f}x"   if ps        and ps > 0        else "N/A"

        # 4. SOLIDEZ FINANCEIRA (20 pts)
        debt_equity   = safe_get(info, "debtToEquity")
        current_ratio = safe_get(info, "currentRatio")
        fcf           = safe_get(info, "freeCashflow")
        mkt_cap       = safe_get(info, "marketCap")

        s = 0
        if debt_equity is not None:
            if debt_equity < 0.3:  s += 7
            elif debt_equity < 0.8: s += 5
            elif debt_equity < 1.5: s += 3
            elif debt_equity < 3.0: s += 1
        else:
            s += 4

        if current_ratio is not None:
            if current_ratio > 2.0:  s += 6
            elif current_ratio > 1.5: s += 4
            elif current_ratio > 1.0: s += 2

        if fcf is not None and mkt_cap and mkt_cap > 0:
            fcf_yield = fcf / mkt_cap
            if fcf_yield > 0.05:  s += 7
            elif fcf_yield > 0.02: s += 4
            elif fcf_yield > 0:    s += 1

        scores["solidez"] = min(s, 20)
        details["debt_to_equity"] = f"{debt_equity:.2f}" if debt_equity   is not None else "N/A"
        details["current_ratio"]  = f"{current_ratio:.2f}" if current_ratio is not None else "N/A"
        details["fcf_yield"] = f"{(fcf/mkt_cap)*100:.1f}%" if (fcf and mkt_cap) else "N/A"

        # 5. QUALIDADE E SENTIMENTO (20 pts)
        r40_val = None
        if rev_growth is not None and profit_margin is not None:
            r40_val = (rev_growth * 100) + (profit_margin * 100)

        q = 0
        if r40_val is not None:
            if r40_val >= 60:  q += 8
            elif r40_val >= 40: q += 6
            elif r40_val >= 25: q += 4
            elif r40_val >= 10: q += 1
        details["rule_of_40"] = f"{r40_val:.1f}" if r40_val is not None else "N/A"

        insiders = safe_get(info, "heldPercentInsiders")
        if insiders is not None:
            if insiders > 0.10: q += 6
            elif insiders > 0.05: q += 4
            elif insiders > 0.01: q += 2
        details["insider_ownership"] = f"{insiders*100:.1f}%" if insiders is not None else "N/A"

        institutions = safe_get(info, "heldPercentInstitutions")
        if institutions is not None:
            if 0.50 <= institutions <= 0.88: q += 6  
            elif institutions > 0.88: q += 4         
            elif institutions > 0.20: q += 2         
        details["institutional_hold"] = f"{institutions*100:.1f}%" if institutions is not None else "N/A"

        try:
            shares_history = ticker.get_shares_full(start="2025-01-01")
            if shares_history is not None and len(shares_history) > 1:
                dilution_rate = (shares_history.iloc[-1] / shares_history.iloc[0]) - 1
                if dilution_rate > 0.04: q -= 2    
                elif dilution_rate > 0.02: q -= 1  
                details["share_dilution_1y"] = f"{dilution_rate*100:+.1f}%"
            else:
                details["share_dilution_1y"] = "0.0% (Estável)"
        except:
            details["share_dilution_1y"] = "N/A"

        short_float = safe_get(info, "shortPercentOfFloat")
        if short_float is not None:
            if short_float > 0.15: q -= 2    
            elif short_float > 0.10: q -= 1  
            details["short_float"] = f"{short_float*100:.1f}%"
        else:
            details["short_float"] = "N/A"

        scores["qualidade"] = max(0, min(q, 20)) 

        # Finalização dos dados básicos
        total = sum(scores.values())
        name = safe_get(info, "longName", ticker_symbol)
        sector = safe_get(info, "sector", "N/A")
        industry = safe_get(info, "industry", "N/A")
        price = safe_get(info, "currentPrice") or safe_get(info, "regularMarketPrice")
        target = safe_get(info, "targetMeanPrice")
        upside = ((target - price) / price * 100) if (target and price and price > 0) else None
        beta = safe_get(info, "beta")
        market_cap = safe_get(info, "marketCap")

        if market_cap:
            if market_cap >= 1e12:  mc_str = f"${market_cap/1e12:.1f}T"
            elif market_cap >= 1e9:  mc_str = f"${market_cap/1e9:.1f}B"
            else:                    mc_str = f"${market_cap/1e6:.0f}M"
        else:
            mc_str = "N/A"

        return {
            "ticker": ticker_symbol.upper(), "name": name, "sector": sector, "industry": industry,
            "price": f"${price:.2f}" if price else "N/A", "market_cap": mc_str, "beta": f"{beta:.2f}" if beta else "N/A",
            "analyst_target": f"${target:.2f}" if target else "N/A",
            "upside": f"+{upside:.1f}%" if upside and upside > 0 else (f"{upside:.1f}%" if upside else "N/A"),
            "total_score": total, "score_label": get_score_label(total), "category_scores": scores, "metrics": details
        }
    except Exception as e:
        return {"error": str(e)}

# --- INTERFACE STREAMLIT ---
st.title("📈 Stock Fundamental Scorer")
st.caption("Sistema de Avaliação de Ações v4.1 (5 Categorias × 20 Pts)")

# Caixa de texto para introduzir o ticker
ticker_input = st.text_input("Introduz o Ticker da Ação (ex: PLTR, NVDA, AAPL):", "").strip().upper()

if st.button("🔍 Analisar Empresa", use_container_width=True) and ticker_input:
    with st.spinner(f"A descarregar dados e a pontuar {ticker_input}..."):
        res = calcular_dados_ticker(ticker_input)
        
        if "error" in res:
            st.error(f"Erro: {res['error']}")
        else:
            st.markdown("---")
            st.header(f"{res['name']} ({res['ticker']})")
            st.caption(f"{res['sector']} | {res['industry']}")
            
            # Bloco de Preço e Target
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Preço Atual", res['price'])
                st.metric("Market Cap", res['market_cap'])
            with col2:
                st.metric("Target Analistas", res['analyst_target'], delta=res['upside'])
                st.metric("Beta (Volatilidade)", res['beta'])
                
            st.markdown("---")
            
            # Score Total Gigante
            st.markdown(f"""
            <div style="background-color: #1f2937; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #3b82f6;">
                <span style="font-size: 16px; color: #9ca3af; text-transform: uppercase;">Score de Robustez</span>
                <h1 style="margin: 5px 0; color: #60a5fa; font-size: 48px;">{res['total_score']} <span style="font-size: 24px; color: #9ca3af;">/ 100</span></h1>
                <span style="font-weight: bold; font-size: 18px;">{res['score_label']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Scores por Categoria com Barras Visuais
            st.subheader("📊 Pontuação por Categoria")
            cs = res['category_scores']
            cats = [("📈", "Crescimento", "crescimento"), ("💹", "Rentabilidade", "rentabilidade"), 
                    ("💲", "Valoração", "valoracao"), ("🛡️", "Solidez", "solidez"), ("🔬", "Qualidade", "qualidade")]
            
            for icon, label, key in cats:
                score_v = cs[key]
                st.write(f"{icon} **{label}:** {score_v}/20")
                st.progress(score_v / 20)
                
            st.markdown("---")
            
            # Métricas Detalhadas
            m = res['metrics']
            st.subheader("👔 Estrutura Acionista & Sentimento")
            st.markdown(f"""
            <div class="metric-card">
                • <b>Insiders (Skin in the Game):</b> {m['insider_ownership']}<br>
                • <b>Institucionais (Smart Money):</b> {m['institutional_hold']}<br>
                • <b>Short Float (Aposta na queda):</b> {m['short_float']}<br>
                • <b>Diluição de Ações (1 Ano):</b> {m['share_dilution_1y']}<br>
                • <b>Média de Surpresa de Lucros:</b> {m['earnings_surprise']}
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("💎 Saúde Financeira & Margens")
            st.markdown(f"""
            <div class="metric-card">
                • <b>Gross Margin:</b> {m['gross_margin']}<br>
                • <b>Operating Margin:</b> {m['operating_margin']}<br>
                • <b>Net Margin:</b> {m['profit_margin']}<br>
                • <b>Revenue Growth (YoY):</b> {m['revenue_growth']}<br>
                • <b>EPS Growth (YoY):</b> {m['earnings_growth']}<br>
                • <b>Rule of 40:</b> {m['rule_of_40']}<br>
                • <b>Dívida / Equity:</b> {m['debt_to_equity']}<br>
                • <b>Current Ratio (Liquidez):</b> {m['current_ratio']}<br>
                • <b>Free Cash Flow Yield:</b> {m['fcf_yield']}
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("💸 Múltiplos de Avaliação")
            st.markdown(f"""
            <div class="metric-card">
                • <b>P/E Ratio (Preço/Lucro):</b> {m['pe_ratio']}<br>
                • <b>PEG Ratio:</b> {m['peg_ratio']}<br>
                • <b>EV/EBITDA:</b> {m['ev_ebitda']}<br>
                • <b>P/S Ratio (Preço/Vendas):</b> {m['price_to_sales']}
            </div>
            """, unsafe_allow_html=True)
