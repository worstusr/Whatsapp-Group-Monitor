import streamlit as st
import pandas as pd
import json
import os
import time
import matplotlib.pyplot as plt
import re

# Apenas UMA chamada, logo após os imports!
st.set_page_config(
    page_title="WhatsApp Group Monitor",
    page_icon="📊",
    layout="wide"
)


# CSS customizado para visual moderno
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .block-container {padding-top: 2rem;}
    .css-1d391kg {background: #fff !important;}
    .metric-label, .metric-value {font-size: 1.2em;}
    .msg-bubble {
        background: #e1ffc7;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px #0001;
    }
    .msg-meta {
        color: #888;
        font-size: 0.85em;
        margin-bottom: 2px;
    }
    .msg-body {
        font-size: 1.1em;
        color: #222;
    }
    hr {margin: 0.5em 0;}
    .stMetric {background: #fff; border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

st.title("📲 WhatsApp Group Monitor")
st.markdown(
    """
    <span style='font-size:1.1em'>
    Visualização em tempo real de mensagens do WhatsApp.<br>
    <span style='color:gray;font-size:0.95em'>
    Certifique-se de que o cliente WhatsApp está rodando e conectado.<br>
    O dashboard atualiza automaticamente a cada intervalo definido.
    </span>
    </span>
    """,
    unsafe_allow_html=True
)

MESSAGES_FILE = "../data/messages.json"

@st.cache_data(ttl=5)
def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return pd.DataFrame()
    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        else:
            df['datetime'] = pd.NaT
        return df
    except Exception as e:
        st.error(f"Erro ao carregar mensagens: {e}")
        return pd.DataFrame()

# Sidebar
st.sidebar.header("Configurações")
auto_refresh = st.sidebar.checkbox("Atualização Automática", True)
refresh_interval = st.sidebar.slider("Intervalo de Atualização (seg)", 5, 60, 10)

# Layout principal
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Estatísticas Gerais")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
    df = load_messages()
    if df.empty:
        st.warning("Nenhuma mensagem capturada ainda. Conecte o cliente WhatsApp para começar.")
    else:
        total_messages = len(df)
        group_messages = df[df.get('isGroup', False) == True].shape[0] if 'isGroup' in df.columns else 0
        direct_messages = total_messages - group_messages
        unique_senders = df['fromName'].nunique() if 'fromName' in df.columns else 0

        metrics_cols = st.columns(4)
        metrics_cols[0].metric("Total de Mensagens", total_messages)
        metrics_cols[1].metric("Mensagens de Grupo", group_messages)
        metrics_cols[2].metric("Mensagens Diretas", direct_messages)
        metrics_cols[3].metric("Participantes Únicos", unique_senders)

        # Disparos de mensagens por participante
        if 'fromName' in df.columns:
            st.subheader("🚀 Disparos de Mensagem por Participante")
            disparos = df['fromName'].value_counts()
            st.bar_chart(disparos.head(10))

        # Atividade por hora
        if 'datetime' in df.columns and not df['datetime'].isnull().all():
            st.subheader("📈 Atividade por Hora")
            df['hour'] = df['datetime'].dt.hour
            hourly_counts = df['hour'].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.bar(hourly_counts.index, hourly_counts.values, color='#25D366')
            ax.set_xlabel('Hora do Dia')
            ax.set_ylabel('Nº de Mensagens')
            ax.set_xticks(range(0, 24))
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)

        # Top participantes
        if 'fromName' in df.columns:
            st.subheader("👥 Top Participantes")
            participants = df['fromName'].value_counts().head(10)
            st.table(participants)

with col2:
    st.subheader("💬 Mensagens Recentes")
    df = load_messages()
    if not df.empty and 'datetime' in df.columns and 'body' in df.columns:
        recent_msgs = df.sort_values('datetime', ascending=False).head(20)
        for _, msg in recent_msgs.iterrows():
            msg_time = msg['datetime'].strftime('%d/%m %H:%M:%S') if pd.notnull(msg['datetime']) else "?"
            sender = msg.get('fromName', 'Desconhecido')
            group = f"[{msg.get('groupName', 'Direto')}] " if msg.get('isGroup') else ""
            st.markdown(
                f"<div class='msg-bubble'>"
                f"<div class='msg-meta'><b>{group}{sender}</b> <span>({msg_time})</span></div>"
                f"<div class='msg-body'>{msg['body']}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("Aguardando mensagens...")

# Auto-refresh
if auto_refresh:
    st.experimental_rerun = getattr(st, "experimental_rerun", st.rerun)  # compatibilidade
    time.sleep(refresh_interval)
    st.experimental_rerun()
