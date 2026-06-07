import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd

# Configuração da página para telemóvel
st.set_page_config(page_title="DCA Semanal", page_icon="🤖", layout="centered")

# Estilo CSS para deixar os botões e cartões mais bonitos no tlm
st.markdown("""
    <style>
    .stApp {background-color: #0e1117; color: #ffffff;}
    .metric-card {
        background-color: #1f2937; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 10px;
        border-left: 5px solid #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# Valores Base Semanais Ajustados
VALOR_ETF_SEMANAL = 61.25

def obter_valor_base_acao_semanal(ticker):
    """Define o valor base de investimento SEMANAL para cada ação"""
    if ticker == "NVDA":
        return 3.75  # Ritmo reduzido semanal (0.75€ * 5)
    return 7.50      # Valor padrão semanal para as restantes (1.50€ * 5)

def analisar_tendencia(ticker_symbol, dias_atras):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=f"{dias_atras + 5}d")
        if hist.empty or len(hist) < 2:
            return None, None, "Sem dados suficientes"
        preco_atual = hist['Close'].iloc[-1]
        idx = max(0, len(hist) - 1 - dias_atras)
        preco_antigo = hist['Close'].iloc[idx]
        variacao = ((preco_atual - preco_antigo) / preco_antigo) * 100
        return preco_atual, variacao, None
    except Exception as e:
        return None, None, str(e)

def calcular_sugestao(variacao, tipo_ativo):
    if variacao is None: return "MANTER", 1.0, "Sem dados", "🟢"
    
    # Como agora tudo é semanal, usamos o limite de 2.0% para o ETF e 3.5% para as Ações
    limite = 2.0 if tipo_ativo == "ETF" else 3.5
    
    if variacao < -limite:
        return "DUPLICAR (Saldos!)", 2.0, f"Queda de {variacao:.1f}%", "🔥"
    elif variacao > limite:
        return "REDUZIR (Esticado)", 0.5, f"Subida de {variacao:.1f}%", "⚠️"
    else:
        return "MANTER (Estável)", 1.0, f"Oscilação de {variacao:+.1f}%", "🟢"

# --- INTERFACE DA APP ---
st.title("🤖 DCA Dinâmico Semanal v2.0")
st.caption(f"Atualizado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if st.button("🔄 Recarregar Dados do Mercado", use_container_width=True):
    st.rerun()

st.markdown("---")

# 1. Secção ETF (Semanal)
st.subheader("📊 Estrutura Semanal (ETF)")
etf_ticker = "SXR8.DE"

with st.spinner(f"A analisar {etf_ticker}..."):
    preco, var, erro = analisar_tendencia(etf_ticker, dias_atras=7)
    if erro:
        st.error(f"Erro no ETF: {erro}")
    else:
        decisao, mult, info_var, emoji = calcular_sugestao(var, "ETF")
        valor_final = VALOR_ETF_SEMANAL * mult
        
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {'#ef4444' if mult==2.0 else '#f59e0b' if mult==0.5 else '#10b981'}">
            <h3>{emoji} {decisao}</h3>
            <p><b>Preço:</b> {preco:.2f}€ | <b>Var. Semanal:</b> {info_var}</p>
            <h2 style="color: #60a5fa;">💰 Aporte: {valor_final:.2f}€</h2>
            <small>Valor Base Semanal: {VALOR_ETF_SEMANAL}€</small>
        </div>
        """, unsafe_allow_html=True)

# 2. Secção Ações (Agora também Semanal)
st.subheader("📱 Estrutura Semanal (Ações)")
acoes = ["META", "PLTR", "GOOG", "NVDA"]

for acao in acoes:
    with st.spinner(f"A analyzing {acao}..."):
        # Alterado de dias_atras=1 para dias_atras=7 (Análise Semanal)
        preco, var, erro = analisar_tendencia(acao, dias_atras=7)
        if erro:
            st.error(f"Erro em {acao}: {erro}")
            continue
            
        valor_base = obter_valor_base_acao_semanal(acao)
        decisao, mult, info_var, emoji = calcular_sugestao(var, "ACAO")
        valor_final = valor_base * mult
        
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {'#ef4444' if mult==2.0 else '#f59e0b' if mult==0.5 else '#10b981'}">
            <h4><b>{acao}</b> - {emoji} {decisao}</h4>
            <p><b>Preço:</b> ${preco:.2f} | <b>Var. Semanal:</b> {info_var}</p>
            <h3 style="color: #34d399;">💰 Aporte Semanal: {valor_final:.2f}€</h3>
            <small>Valor Base Semanal: {valor_base:.2f}€</small>
        </div>
        """, unsafe_allow_html=True)

