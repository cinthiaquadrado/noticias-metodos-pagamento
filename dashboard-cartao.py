# Configuração da página (mover para o início do código)
streamlit.set_page_config(page_title="Análise de Notícias", layout="wide")

# Fontes de RSS
RSS_FEEDS = [
    {"name": "G1 Economia", "url": "https://g1.globo.com/rss/g1/economia/"},
    {"name": "BCB - Notas técnicas", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/notastecnicas"},
    {"name": "BCB - Notícias", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/noticias?ano=2024"},
    {"name": "BCB - Notas imprensa", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/notasImprensa?ano=2021"},
    {"name": "BCB - Estatísticas monetárias e de crédito", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/historicomonetariascredito"},
    {"name": "Relatório de Pesquisa em Economia e Finanças", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/relatorioeconofinancas"},
    {"name": "CreditCards.com", "url": "https://www.creditcards.com/news/rss/"},
    {"name": "Finsiders Brasil", "url": "https://finsidersbrasil.com.br/feed"},
]

# Função para buscar e processar as notícias de múltiplas fontes
def fetch_news_from_feeds(feeds):
    all_news = []
    for feed in feeds:
        feed_data = feedparser.parse(feed["url"])

        for entry in feed_data.entries:
            all_news.append({
                "title": entry.get("title", "Sem título"),
                "date": entry.get("published", "Data desconhecida"),
                "summary": entry.get("summary", "Sem resumo"),
                "link": entry.get("link", "Sem link"),
                "source": feed["name"]
            })
    return pd.DataFrame(all_news)

# Função para análise de sentimentos com VADER
def analyze_sentiment_vader(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(text)
    if sentiment_score['compound'] > 0.05:
        return "Positivo"
    elif sentiment_score['compound'] < -0.05:
        return "Negativo"
    else:
        return "Neutro"

# Função para exibir as notícias no dashboard
def display_news(news_df):
    for _, row in news_df.iterrows():
        st.markdown(f"### [{row['title']}]({row['link']})")
        st.markdown(f"**Data:** {row['date']}")
        st.markdown(f"**Fonte:** {row['source']}")
        st.markdown(f"**Sentimento:** {row['sentiment']}")
        st.write("---")

# Função para exibir a distribuição das notícias
def display_distribution(news_df):
    st.header("Distribuição Temporal de Notícias")
    news_df['date_parsed'] = pd.to_datetime(news_df['date'], errors='coerce')
    news_df['date_parsed'] = news_df['date_parsed'].fillna(datetime.now())

    group_by = st.selectbox("Agrupar por:", ["Dia", "Semana", "Mês"])
    if group_by == "Dia":
        date_counts = news_df['date_parsed'].dt.date.value_counts().sort_index()
    elif group_by == "Semana":
        date_counts = news_df['date_parsed'].dt.to_period("W").value_counts().sort_index()
    else:
        date_counts = news_df['date_parsed'].dt.to_period("M").value_counts().sort_index()

    plt.figure(figsize=(10, 6))
    date_counts.plot(kind="bar", color="skyblue", alpha=0.7)
    plt.title("Distribuição de Notícias")
    plt.ylabel("Número de Notícias")
    plt.xlabel(group_by)
    plt.xticks(rotation=45)
    st.pyplot(plt)

    st.subheader("Nuvem de Palavras")
    all_text = " ".join(news_df["title"].fillna("") + " " + news_df["summary"].fillna(""))
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)

# Função para exibir a análise de sentimentos das notícias
def display_sentiment_analysis(news_df):
    st.header("Análise de Sentimentos das Notícias")
    sentiment_counts = news_df["sentiment"].value_counts()
    st.bar_chart(sentiment_counts)

# Função para categorizar as notícias
categories = {
    "Cashback": ["cashback", "dinheiro de volta", "recompensas"],
    "Travel Rewards": ["milhas", "viagem", "aéreas"],
    "Crédito Corporativo": ["empresarial", "corporativo", "business"],
    "Fintechs": ["fintech", "bancos digitais", "plataformas"]
}

def categorize_news(news_df):
    category_counts = {cat: 0 for cat in categories}
    for _, row in news_df.iterrows():
        text = (row['title'] + " " + row['summary']).lower()
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                category_counts[category] += 1
    return category_counts

# Exibir as categorias no dashboard
def display_categories(news_df):
    st.subheader("Categorias de Notícias por Tema")
    categories = categorize_news(news_df)
    st.bar_chart(pd.DataFrame.from_dict(categories, orient='index', columns=["Quantidade"]))

# Função principal para criar o dashboard
def main():
    st.title("Dashboard de Notícias - Cartões de Crédito")
    
    news_data = fetch_news_from_feeds(RSS_FEEDS)

    if not news_data.empty:
        st.sidebar.header("Filtros")
        sources = st.sidebar.multiselect("Selecione a fonte", options=news_data["source"].unique(), default=news_data["source"].unique())
        start_date = st.sidebar.date_input("Data inicial", value=datetime(2023, 1, 1))
        end_date = st.sidebar.date_input("Data final", value=datetime.now())
        keywords = st.sidebar.text_area("Palavras-chave (separadas por vírgulas)", value="Digite o seu termo de busca")

        news_data["date_parsed"] = pd.to_datetime(news_data["date"], errors='coerce')
        filtered_data = news_data[
            (news_data["source"].isin(sources)) &  
            (news_data["date_parsed"].dt.date >= start_date) &  
            (news_data["date_parsed"].dt.date <= end_date)
        ]

        if keywords:
            keyword_list = [kw.strip().lower() for kw in keywords.split(",")]
            filtered_data = filtered_data[ 
                filtered_data["title"].str.lower().str.contains("|".join(keyword_list)) |
                filtered_data["summary"].str.lower().str.contains("|".join(keyword_list))
            ]

        filtered_data["sentiment"] = filtered_data["title"].apply(analyze_sentiment_vader)

        filtered_data = filtered_data.sort_values(by="date_parsed", ascending=False)

        top_news = filtered_data.head(15)

        tab1, tab2 = st.tabs(["Notícias", "Distribuição Temporal"])

        with tab1:
            if not top_news.empty:
                display_news(top_news)
            else:
                st.write("Nenhuma notícia encontrada para os filtros aplicados.")

        with tab2:
            if not filtered_data.empty:
                display_distribution(filtered_data)
                display_sentiment_analysis(filtered_data)
                display_categories(filtered_data)
            else:
                st.write("Nenhuma informação para exibir na distribuição temporal.")
    else:
        st.write("Não foi possível buscar as notícias.")

if __name__ == "__main__":
    main()
