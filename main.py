import streamlit as st
import pandas as pd
import requests
import datetime


@st.cache_data(ttl="1day")
def get_selic():
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json()['conteudo'])

    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(datetime.datetime.today().date())
    
    return df

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

def main_metas():
        
    col1, col2 = st.columns(2)

    data_inicio_meta = col1.date_input("Inicio de meta", max_value=df_stats.index.max())
    
    data_filtrada = df_stats.index[df_stats.index <= data_inicio_meta][-1]

    custos_fixos = col1.number_input("Custos Fixos", min_value=0., format="%.2f")
    salario_bruto = col2.number_input("Salário Bruto", min_value=0., format="%.2f")
    salario_liquido = col2.number_input("Salário Líquido", min_value=0., format="%.2f")

    valor_inicio = df_stats.loc[data_filtrada]["Valor"]
    col1.markdown(f"**Patrimônio no início da Meta**: R$ {valor_inicio: .2f}")

    selic_gov = get_selic()
    filter_selic_date = (selic_gov["DataInicioVigencia"] < data_inicio_meta) & (selic_gov["DataFimVigencia"] > data_inicio_meta)
    selic_default = selic_gov[filter_selic_date]["MetaSelic"].iloc[0]

    selic = st.number_input("Selic", min_value=0., value=selic_default, format="%.2f")
    selic_ano = selic / 100
    selic_mes = (selic_ano + 1) ** (1/12) - 1

    rendimento_ano = valor_inicio * selic_ano
    rendimento_mes = valor_inicio * selic_mes
    
    col1_pot, col2_pot = st.columns(2)
    mensal = salario_liquido - custos_fixos + rendimento_mes
    anual = (salario_liquido - custos_fixos)* 12 + rendimento_ano
    
    with col1_pot.container(border=True):
        st.markdown(f"**Potencial arrecadação mês**:\n\n R$ {mensal: .2f}", help= f"{salario_liquido:.2f} + (-{custos_fixos:.2f}) + {rendimento_mes:.2f}")    
    with col2_pot.container(border=True):
        st.markdown(f"**Potencial arrecadação ano**:\n\n R$ {anual: .2f}", help=f"12 * ({salario_liquido:.2f} + (-{custos_fixos:.2f})) + {rendimento_ano:.2f}")

    with st.container(border=True):
        col1_meta, col2_meta = st.columns(2)
        with col1_meta:
            meta_estipulada = st.number_input("Meta Estipulada: ", min_value=-9999999., format="%.2f", value=anual)

        with col2_meta:
            patrimonio_final = meta_estipulada + valor_inicio
            st.markdown(f"Patrimônio Estimado pós meta:\n\n R$ {patrimonio_final: .2f}")

    return data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final

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

    with st.expander("Metas"):
        
        tab_main, tab_data, tab_grafico = st.tabs(tabs=["Configuração", "Dados", "Gráficos"])

        with tab_main:
            data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final = main_metas()
        
        with tab_data:

            meses = pd.DataFrame({"Data Referência":[data_inicio_meta + pd.DateOffset(months=i) for i in range(1,13)],
                                "Meta Mensal": [valor_inicio + round(meta_estipulada/12, 2) * i for i in range(1, 13)],
                                })
            meses["Data Referência"] = meses["Data Referência"].dt.strftime("%Y-%m")        
            df_patrimonio = df_stats.reset_index()[["Data", "Valor"]]
            df_patrimonio["Data Referência"] = pd.to_datetime(df_patrimonio["Data"]).dt.strftime("%Y-%m")
            meses = meses.merge(df_patrimonio, how="left", on="Data Referência")

            meses = meses[['Data Referência', 'Meta Mensal', 'Valor']]
            meses["Atingimento (%)"] = meses["Valor"] / meses["Meta Mensal"]
            meses["Atingimento Ano"] = meses["Valor"] / patrimonio_final
            meses["Atingimento Esperado"] = meses["Meta Mensal"] / patrimonio_final
            meses = meses.set_index("Data Referência")

            columns_config = {
                "Meta Mensal": st.column_config.NumberColumn("Meta Mensal", format="R$ %.2f"),
                "Valor": st.column_config.NumberColumn("Valor Atingido", format="R$ %.2f"),
                "Atingimento (%)": st.column_config.NumberColumn("Atingimento (%)", format="percent"),
                "Atingimento Ano": st.column_config.NumberColumn("Atingimento ano", format="percent"),
                "Atingimento Esperado": st.column_config.NumberColumn("Atingimento Esperado", format="percent"),
                }


            st.dataframe(meses, column_config=columns_config)

        with tab_grafico:
            st.line_chart(meses[['Atingimento Ano', "Atingimento Esperado"]])
        

        


        

