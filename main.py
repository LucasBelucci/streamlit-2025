import streamlit as st
import pandas as pd


def calc_general_stats(df):
    df_data= df.groupby(by="Data")[["Valor"]].sum()
    df_data['lag_1'] = df_data["Valor"].shift(1)
    df_data['Diferença Mensal Abs.'] = df_data['Valor']-df_data["lag_1"]
    df_data["Média 6M Diferença Mensal"] = df_data['Diferença Mensal Abs.'].rolling(6).mean()
    df_data["Média 12M Diferença Mensal"] = df_data['Diferença Mensal Abs.'].rolling(12).mean()
    df_data["Média 24M Diferença Mensal"] = df_data['Diferença Mensal Abs.'].rolling(24).mean()
    df_data["Diferença Mensal Relativa"] = df_data['Valor'] / df_data['lag_1'] - 1
    df_data["Evolução 6M Total"] = df_data["Valor"].rolling(6).apply(lambda x: x[-1] - x[0])
    df_data["Evolução 12M Total"] = df_data["Valor"].rolling(12).apply(lambda x: x[-1] - x[0])
    df_data["Evolução 24M Total"] = df_data["Valor"].rolling(24).apply(lambda x: x[-1] - x[0])
    df_data["Evolução 6M Relativa"] = df_data['Valor'].rolling(6).apply(lambda x: x[-1] / x[0] - 1)
    df_data["Evolução 12M Relativa"] = df_data['Valor'].rolling(12).apply(lambda x: x[-1] / x[0] - 1)
    df_data["Evolução 24M Relativa"] = df_data['Valor'].rolling(24).apply(lambda x: x[-1] / x[0] - 1)
    df_data= df_data.drop("lag_1", axis=1)
    
    return df_data

st.set_page_config(page_title="Finanças")

st.markdown("""
# Boas vindas!!
# 
## Nosso APP Financeiro!            
""")

# Widget de upload de dados
file_upload = st.file_uploader(label="Faça upload dos dados aqui", type=['csv'])

# Verifica se algum arquivo foi feito upload
if file_upload:
    
    # Leitura dos dados
    df = pd.read_csv(file_upload)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date

    # Exibição dos dados
    exp1 = st.expander("Dados Brutos")
    columns_fmt = {"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
    exp1.dataframe(df, hide_index=True, column_config=columns_fmt)

    # Visão Instituição
    exp2 = st.expander("Instituições")
    df_instituicao = df.pivot_table(index="Data", columns="Instituição", values="Valor")


    # Abas para diferentes visualizações
    tab_data, tab_history, tab_share = exp2.tabs(["Dados", "Histórico", "Distribuição"])

    # Exibe dataframe
    with tab_data:
        st.dataframe(df_instituicao)
    
    # Exibe histórico
    with tab_history:
        st.line_chart(df_instituicao)

    # Exibe distribuições
    with tab_share:

        # Filtro de data
        date = st.selectbox("Filtro Data", options=df_instituicao.index)

        # Gráfico de distribuição
        st.bar_chart(df_instituicao.loc[date])

    exp3 = st.expander("Estatísticas Gerais")

    df_stats = calc_general_stats(df)

    columns_config = {
    "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    "Diferença Mensal Abs.": st.column_config.NumberColumn("Diferença Mensal Abs.", format="R$ %.2f"),
    "Média 6M Diferença Mensal": st.column_config.NumberColumn("Média 6M Diferença Mensal", format="R$ %.2f"),
    "Média 12M Diferença Mensal": st.column_config.NumberColumn("Média 12M Diferença Mensal", format="R$ %.2f"), 
    "Média 24M Diferença Mensal": st.column_config.NumberColumn("Média 24M Diferença Mensal", format="R$ %.2f"), 
    "Evolução 6M Total": st.column_config.NumberColumn("Evolução 6M Total", format="R$ %.2f"), 
    "Evolução 12M Total": st.column_config.NumberColumn("Evolução 12M Total", format="R$ %.2f"), 
    "Evolução 24M Total": st.column_config.NumberColumn("Evolução 24M Total", format="R$ %.2f"),
    "Diferença Mensal Relativa": st.column_config.NumberColumn("Diferença Mensal Relativa", format="percent"),
    "Evolução 6M Relativa": st.column_config.NumberColumn("Evolução 6M Relativa", format="percent"), 
    "Evolução 12M Relativa": st.column_config.NumberColumn("Evolução 12M Relativa", format="percent"), 
    "Evolução 24M Relativa": st.column_config.NumberColumn("Evolução 24M Relativa", format="percent"), 
    }

    tab_stats, tab_abs, tab_rel = exp3.tabs(tabs=["Dados", "Histórico de Evolução", "Crescimento Relativo"])

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_abs:
        abs_cols = [
        "Diferença Mensal Abs.",
        "Média 6M Diferença Mensal",
        "Média 12M Diferença Mensal",
        "Média 24M Diferença Mensal",
        ]

        st.line_chart(df_stats[abs_cols])
    
    with tab_rel:
        rel_col = [
        "Diferença Mensal Relativa",
        "Evolução 6M Relativa",
        "Evolução 12M Relativa",
        "Evolução 24M Relativa",
        ]
        
        st.line_chart(df_stats[rel_col])