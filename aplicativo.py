import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium import Choropleth, GeoJsonTooltip
from streamlit_folium import folium_static
import plotly.express as px
import os
import libpysal
from esda.moran import Moran_Local
from libpysal.weights import Queen

# ---------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------
st.set_page_config(page_title="Indicadores da Paraíba", layout="wide")
st.title("Análise espacial das taxas de mortalidade infantil e de óbitos por acidentes de trânsito na Paraíba")

# ---------------------------
# ESTILO VISUAL
# ---------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #1a2c5b; }
    .css-18e3th9 { background-color: #1a2c5b; color: white; }
    .css-1d391kg { color: #1a2c5b !important; }
    .stButton>button { background-color: #1a2c5b; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# CARREGAMENTO DIRETO DAS BASES
# ---------------------------
shape_path = "PB_Municipios_2023.shp"
excel_path = "dados_paraiba.xlsx"

if not os.path.exists(shape_path):
    st.error("O shapefile 'PB_Municipios_2023.shp' não foi encontrado na pasta.")
elif not os.path.exists(excel_path):
    st.error("O arquivo Excel 'Dados de área Paraiba.xlsx' não foi encontrado na pasta.")
else:
    with st.spinner("Carregando dados..."):
        gdf = gpd.read_file(shape_path)
        df = pd.read_excel(excel_path)

    col_municipio = "Município "
    col_acidentes = "Taxa de vítimas de acidentes de trânsito a óbito (2022)"
    col_mortalidade = "Mortalidade infantil - óbitos por mil nascidos vivos "
    col_pop = "População estimada "  # opcional

    colunas_necessarias = [col_municipio, col_acidentes, col_mortalidade]

    if any(col not in df.columns for col in colunas_necessarias):
        st.error("Uma ou mais colunas necessárias não foram encontradas no Excel.")
    elif "NM_MUN" not in gdf.columns:
        st.error("A coluna 'NM_MUN' não foi encontrada no shapefile.")
    else:
        shape_data = gdf.merge(df, left_on="NM_MUN", right_on=col_municipio, how="left")
        municipios_disponiveis = df[col_municipio].dropna().unique().tolist()
        municipios_selecionados = st.sidebar.multiselect("Selecione municípios para destaque", municipios_disponiveis)

    
        shape_data["selecionado"] = shape_data["NM_MUN"].isin(municipios_selecionados)

        # ---------------------------
        # ABAS PRINCIPAIS
        # ---------------------------
        tab_documentacao,materiais, tab_area, tab_acidentes_map, tab_acidentes_plot, tab_mort_map, tab_mort_plot, tab_moran, tab_lisa,tab_ref = st.tabs([
            "Documentação",
            "Materiais e métodos",
            "Área de Estudo",
            "Mapa explorátorio - Acidentes de Trânsito",
            "Boxplot e Histograma - Acidentes de Trânsito",
            "Mapa explorátorio da Mortalidade Infantil",
            "Boxplot e Histograma - Mortalidade Infantil",
            "Moran Local (Quadrantes)",
            "LISA Map (Significativo)",
            "Referências"
        ])

        # ---------------------------
        # 1. ÁREA DE ESTUDO
        # ---------------------------
        with tab_documentacao:
            st.subheader("Documentação")
    # Conteúdo será adicionado depois
            st.markdown(
        """
        <div style="text-align: justify;">
     Os dados utilizados nesta análise foram obtidos junto ao IPEA, para os óbitos por acidentes de trânsito, e ao IBGE, para a mortalidade infantil, ambos referentes ao ano de 2022.

Inicialmente, as bases passaram por etapas de organização, com ajustes nos nomes dos municípios, de forma a garantir compatibilidade com o arquivo shapefile utilizado nos mapas. Essa etapa foi essencial para permitir a correta integração entre os dados estatísticos e as informações geográficas.

Em seguida, foram calculadas taxas de óbitos por 100 mil habitantes e elaborados mapas interativos, permitindo a visualização do comportamento espacial dos indicadores. Para complementar a análise, foram construídos histogramas e boxplots, que auxiliam na compreensão da distribuição e da variabilidade dos dados.

Por fim, foram aplicadas técnicas de estatística espacial, por meio do Moran Map e dos LISA Maps, incluindo o mapa de significância, com o objetivo de identificar padrões espaciais e áreas com associação estatisticamente relevante.
        </div>
        """,
        unsafe_allow_html=True
    )

    # ===== MATERIAIS E MÉTODOS =====
        with materiais:
            st.subheader("Materiais e Métodos")
    # Conteúdo será adicionado depois
            st.markdown(
    """
    <div style="text-align: justify;">

    <b>2.1. Índice de Moran Global</b><br><br>

    O Índice de Moran Global é responsável por avaliar a relação de dependência espacial
    entre todos os polígonos da área de estudo por meio de uma estatística única.
    Sendo esta estatística denotada pela seguinte fórmula:

    $$ 
    I = \\frac{\\sum_{i=1}^{n} \\sum_{j=1}^{n} w_{ij} (Z_i - \\mu_z)(Z_j - \\mu_z)}
    {\\sum_{i=1}^{n} (Z_i - \\mu_z)^2}
    \\tag{1}
    $$

    sendo, <i>n</i> representa o número de áreas; <i>Z<sub>i</sub></i> é o valor do atributo
    considerado na área <i>i</i>; <i>μ<sub>z</sub></i> é o valor médio do atributo na região
    de estudo; e <i>w<sub>ij</sub></i> corresponde ao elemento <i>ij</i> da matriz de
    vizinhança normalizada. A estatística de Moran pode ser associada a um teste de
    hipóteses para a checagem da existência de autocorrelação espacial, cuja hipótese
    nula é de independência espacial (Câmara, 2004).

    <br><br>

    <b>2.2. Índice de Moran Local</b><br><br>

    Indicadores globais como o Índice de Moran fornecem um único valor como medida de
    associação para todo o conjunto de dados. Entretanto, quando se trabalha com um
    grande número de áreas, pode haver variações locais na associação espacial.
    Assim, utiliza-se o Índice de Moran Local para avaliar a relação de uma área com
    sua vizinhança imediata, considerando uma distância pré-determinada.

    $$
    I_i = \\frac{Z_i \\sum_{j=1}^{n} w_{ij} Z_j}
    {\\sum_{j=1}^{n} Z_j^2}
    \\tag{2}
    $$

    <b>2.3. Gráfico de Moran Map</b><br><br>

    O Moran Map consiste em uma extensão do Gráfico de Espalhamento de Moran e é utilizado
    para observar a autocorrelação espacial. As áreas são classificadas em quadrantes,
    sendo Q1 (<i>high-high</i>) e Q2 (<i>low-low</i>) indicativos de autocorrelação positiva
    e negativa, respectivamente, enquanto Q3 (<i>high-low</i>) e Q4 (<i>low-high</i>)
    representam áreas de transição ou discrepância espacial (Gómez-Rubio, 2013).

    </div>
    """,
    unsafe_allow_html=True
)

        with tab_area:
            st.subheader("Área de Estudo: Municípios da Paraíba")
            m = folium.Map(location=[-7.2, -36.5], zoom_start=7)
            folium.GeoJson(
                shape_data,
                name="Municípios",
                style_function=lambda feature: {
                    "fillColor": "#4287f5",
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.4,
                },
                tooltip=GeoJsonTooltip(fields=["NM_MUN"], aliases=["Município"])
            ).add_to(m)
            folium_static(m)

        # ---------------------------
        # FUNÇÃO PARA MAPA INTERATIVO
        # ---------------------------
        def mapa_interativo(coluna, legenda, cor):
            m = folium.Map(location=[-7.2, -36.5], zoom_start=7)
            Choropleth(
                geo_data=shape_data,
                name="choropleth",
                data=shape_data,
                columns=["NM_MUN", coluna],
                key_on="feature.properties.NM_MUN",
                fill_color=cor,
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name=legenda
            ).add_to(m)

            folium.GeoJson(
                shape_data,
                name="Indicadores",
                style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
                tooltip=GeoJsonTooltip(
                    fields=["NM_MUN", coluna],
                    aliases=["Município", legenda],
                    localize=True
                )
            ).add_to(m)

            for _, row in shape_data.iterrows():
                if row["selecionado"]:
                    folium.GeoJson(
                        row["geometry"],
                        style_function=lambda x: {'fillColor': 'none', 'color': 'yellow', 'weight': 3},
                        tooltip=folium.Tooltip(f"{row['NM_MUN']}: {row[coluna]}")
                    ).add_to(m)

            folium_static(m)

        # ---------------------------
        # 2. MAPA ACIDENTES
        # ---------------------------
        with tab_acidentes_map:
            st.subheader("Mapa Interativo - Taxa de acidentes de Trânsito")
            mapa_interativo(col_acidentes, "Taxa de vítimas de acidentes de trânsito a óbito (2022)", "PuBuGn")

        # ---------------------------
        # 3. BOX E HISTOGRAMA ACIDENTES
        # ---------------------------
        with tab_acidentes_plot:
            st.subheader("Boxplot e Histograma - Taxa de acidentes de Trânsito")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Histograma")
                fig_hist = px.histogram(df, x=col_acidentes, nbins=20, color_discrete_sequence=["#1a2c5b"])
                fig_hist.update_layout(xaxis_title="Taxa de vítimas de acidentes de trânsito", yaxis_title="Frequência")
                st.plotly_chart(fig_hist, use_container_width=True)
            with col2:
                st.markdown("### Boxplot")
                fig_box = px.box(df, y=col_acidentes, color_discrete_sequence=["#1a2c5b"])
                fig_box.update_layout(yaxis_title="Taxa de vítimas de acidentes de trânsito")
                st.plotly_chart(fig_box, use_container_width=True)

        # ---------------------------
        # 4. MAPA MORTALIDADE
        # ---------------------------
        with tab_mort_map:
            st.subheader("Mapa Interativo - Taxa da Mortalidade Infantil")
            mapa_interativo(col_mortalidade, "Mortalidade infantil (óbitos por mil nascidos vivos)", "YlOrRd")

        # ---------------------------
        # 5. BOX E HISTOGRAMA MORTALIDADE
        # ---------------------------
        with tab_mort_plot:
            st.subheader("Boxplot e Histograma - Taxa da Mortalidade Infantil")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Histograma")
                fig_hist = px.histogram(df, x=col_mortalidade, nbins=20, color_discrete_sequence=["#b33430"])
                fig_hist.update_layout(xaxis_title="Mortalidade Infantil", yaxis_title="Frequência")
                st.plotly_chart(fig_hist, use_container_width=True)
            with col2:
                st.markdown("### Boxplot")
                fig_box = px.box(df, y=col_mortalidade, color_discrete_sequence=["#b33430"])
                fig_box.update_layout(yaxis_title="Mortalidade infantil (óbitos por mil nascidos vivos)")
                st.plotly_chart(fig_box, use_container_width=True)

        # ---------------------------
        # 6. MORAN LOCAL (QUADRANTES)
        # ---------------------------
        with tab_moran:
            st.subheader("Moran Local - Quadrantes (Acidentes e Mortalidade)")

            w = Queen.from_dataframe(shape_data)
            w.transform = 'r'

            for col, nome in [(col_acidentes, "Acidentes"), (col_mortalidade, "Mortalidade")]:
                st.markdown(f"### {nome}")
                y = shape_data[col].fillna(0).values
                moran_loc = Moran_Local(y, w)
                
                shape_data[f'{col}_quadrante'] = moran_loc.q
                shape_data[f'{col}_sig'] = moran_loc.p_sim < 0.05

                colors = {1: 'red', 2: 'blue', 3: 'lightblue', 4: 'pink'}

                m = folium.Map(location=[-7.2, -36.5], zoom_start=7)
                for _, row in shape_data.iterrows():
                    if row[f'{col}_sig']:
                        folium.GeoJson(
                            row['geometry'],
                            style_function=lambda x, q=row[f'{col}_quadrante']: {'fillColor': colors[q], 'color': 'black', 'weight': 1, 'fillOpacity':0.7},
                            tooltip=folium.Tooltip(f"{row['NM_MUN']}: Quadrante {row[f'{col}_quadrante']}")
                        ).add_to(m)
                    else:
                        folium.GeoJson(
                            row['geometry'],
                            style_function=lambda x: {'fillColor': 'lightgrey', 'color': 'black', 'weight': 1, 'fillOpacity':0.4}
                        ).add_to(m)
                folium_static(m)

        # ---------------------------
        # 7. LISA MAP (SIGNIFICATIVO)
        # ---------------------------
        with tab_lisa:
            st.subheader("LISA Map - Municípios Significativos")

            for col, nome in [(col_acidentes, "Acidentes"), (col_mortalidade, "Mortalidade")]:
                st.markdown(f"### {nome}")
                y = shape_data[col].fillna(0).values
                moran_loc = Moran_Local(y, w)
                
                shape_data[f'{col}_sig'] = moran_loc.p_sim < 0.05

                m = folium.Map(location=[-7.2, -36.5], zoom_start=7)
                for _, row in shape_data.iterrows():
                    if row[f'{col}_sig']:
                        folium.GeoJson(
                            row['geometry'],
                            style_function=lambda x: {'fillColor': 'yellow', 'color': 'black', 'weight': 2, 'fillOpacity':0.7},
                            tooltip=folium.Tooltip(f"{row['NM_MUN']}: Significativo")
                        ).add_to(m)
                    else:
                        folium.GeoJson(
                            row['geometry'],
                            style_function=lambda x: {'fillColor': 'lightgrey', 'color': 'black', 'weight': 1, 'fillOpacity':0.3}
                        ).add_to(m)
                folium_static(m)
     

        # ---------------------------
        # 8. REFS
        # ---------------------------
with tab_ref:
    st.subheader("Referência")

    st.markdown(
        """
        <div style="text-align: justify;">

        1. BRASIL. Ministério da Saúde. <b>Sistema de Informação sobre Mortalidade – SIM</b>. 
        Brasília, 2023. Disponível em: 
        https://www.gov.br/saude/pt-br/composicao/svsa/sistemas-de-informacao/sim. 
        Acesso em: 15 set. 2025.

       

        2. SILVA, A. R.; ALMEIDA, P. L. Análise espacial da mortalidade por acidentes de trânsito 
        no Nordeste brasileiro. <i>Revista Brasileira de Epidemiologia</i>, v. 25, p. 1-12, 2022. 
        Disponível em: 
        https://journalmbr.com.br/index.php/jmbr/article/view/316. 
        Acesso em: 15 set. 2025.

     

        3. CARVALHO, J. F.; PEREIRA, M. S. Fatores associados aos acidentes de trânsito: uma revisão 
        da literatura. <i>Cadernos de Saúde Pública</i>, v. 37, n. 4, p. 1-15, 2021. 
        Disponível em: 
        https://www.scielo.br/j/csc/a/QF7kcZyHkKbZVx8rnQQ8dGf/. 
        Acesso em: 15 set. 2025.

   

        4. SOUZA, L. H.; COSTA, R. A.; MENDES, F. V. Mortalidade por acidentes de trânsito e 
        predominância de motociclistas: evidências do Nordeste brasileiro. 
        <i>Revista de Saúde Coletiva</i>, v. 30, n. 2, p. 55-68, 2022. 
        Disponível em: 
        https://www.researchgate.net/publication/358112074_Avaliacao_dos_acidentes_com_motocicletas_no_Brasil. 
        Acesso em: 15 set. 2025.

   

        5. SPRINGER. <i>Handbook of Regional Science</i>. [S.l.]: Springer, 2014. 
        Disponível em: https://link.springer.com/book/10.1007/978-1-4614-7618-4.

       

        6. MORAGA, P. <i>Spatial Epidemiology: Methods and Applications</i>. [S.l.]: CRC Press, 2022. 
        Disponível em: https://www.paulamoraga.com/book-spatial/spatial-autocorrelation.html.

      

        7. CÂMARA, G. et al. <i>Análise de dados geoespaciais</i>. INPE – Instituto Nacional de 
        Pesquisas Espaciais. Capítulo 5 – Análise em áreas. 
        Disponível em: http://www.dpi.inpe.br/gilberto/livro/analise/cap5-areas.pdf.

      

        8. BAILEY, T. C.; GATRELL, A. C. Spatial Autocorrelation. 
        <i>Wiley StatsRef: Statistics Reference Online</i>, 2014. 
        Disponível em: https://onlinelibrary.wiley.com/.

       

        9. BRASIL. Ministério da Saúde. Secretaria de Vigilância em Saúde. 
        <b>Sistema de Informação de Agravos de Notificação – SINAN</b>. Brasília: Ministério da Saúde. 
        Disponível em: https://www.gov.br/saude/pt-br/composicao/svs/sinan.

    

        10. IBGE – Instituto Brasileiro de Geografia e Estatística. 
        <i>Indicadores e dados estatísticos</i>. Rio de Janeiro: IBGE, 2023. 
        Disponível em: https://www.ibge.gov.br/.

   

        11. RSTUDIO TEAM. <i>RStudio: Integrated Development for R</i>. 
        Boston, MA: RStudio, PBC, 2023. Disponível em: https://posit.co/.

   

        12. CÂMARA, G. et al. <i>Análise espacial e geoprocessamento</i>. 
        Brasília: EMBRAPA, p. 21-54, 2004.

     

        13. ALMEIDA, E. S. <i>Econometria Espacial Aplicada</i>. 
        Campinas: Alínea, 2012.

       

        14. OLIVEIRA-FRIESTINO, J. K. et al. Spatial distribution of mortality from land traffic 
        accidents in Santa Catarina: ecological study (2000–2016). 
        <i>Journal of Contemporary Nursing</i>, v. 12, e5026, 2023. 
        DOI: 10.17267/2317-3378rec.2023.e5026.

     
        15. SANTOS, M. M. Q. et al. Spatial distribution of cancer diagnostic equipment in Brazilian 
        microregions (2019). <i>Revista Brasileira de Gestão e Desenvolvimento Regional</i>, 
        v. 20, n. 3, p. 550-571, 2024.

   

        16. DANTAS, W. L. R. Robustez do modelo na análise espacial de acidentes: consideração da 
        superdispersão e modelos espaciais em Pernambuco.

    

        17. PYTHON SOFTWARE FOUNDATION. <i>Python Language Reference</i>. 
        Disponível em: https://www.python.org/. Acesso em: 2025.

    

        18. STREAMLIT INC. <i>Streamlit Documentation</i>. 
        Disponível em: https://docs.streamlit.io/. Acesso em: 2025.

      

        19. IBGE – Instituto Brasileiro de Geografia e Estatística. 
        <i>API de dados e malhas territoriais</i>. 
        Disponível em: https://servicodados.ibge.gov.br/. Acesso em: 2025.

        </div>
        """,
        unsafe_allow_html=True
    )
