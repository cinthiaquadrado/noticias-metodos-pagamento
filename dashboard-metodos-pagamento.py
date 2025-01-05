import feedparser
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configuração da página
st.set_page_config(page_title="Análise de Notícias", layout="wide")

# Fontes de RSS
RSS_FEEDS = [
    {"name": "Tecnologia", "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=pt-BR&gl=BR&ceid=BR:pt-150"},
    {"name": "Economia", "url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=pt-BR&gl=BR&ceid=BR:pt-150"},
    {"name": "Finanças", "url": "https://news.google.com/rss/headlines/section/topic/FINANCE?hl=pt-BR&gl=BR&ceid=BR:pt-150"},
    {"name": "BCB - Notas técnicas", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/notastecnicas"},
    {"name": "BCB - Notícias", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/noticias"},
    {"name": "BCB - Notas imprensa", "url": "https://www.bcb.gov.br/api/feed/sitebcb/sitefeeds/notasImprensa"},
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

    group_by = st.selectbox("Agrupar por:", ["Dia", "Mês", "Ano"])
    if group_by == "Dia":
        date_counts = news_df['date_parsed'].dt.date.value_counts().sort_index()
    elif group_by == "Mês":
        date_counts = news_df['date_parsed'].dt.to_period("M").value_counts().sort_index()
    else:
        date_counts = news_df['date_parsed'].dt.to_period("A").value_counts().sort_index()

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
    display_sentiment_bar_chart(sentiment_counts)

# Função para exibir o gráfico de barras da análise de sentimentos
def display_sentiment_bar_chart(sentiment_counts):
    fig, ax = plt.subplots(figsize=(7, 7))
    sentiment_counts.plot(kind="bar", color=["#FF6666", "#66FF66", "#FFD700"], ax=ax)
    ax.set_title("Análise de Sentimentos")
    ax.set_ylabel("Número de Notícias")
    ax.set_xlabel("Sentimentos")
    st.pyplot(fig)

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
    st.title("Dashboard de Notícias - Métodos de Pagamento")
    
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

        filtered_data["sentiment"] = filtered_data.apply(lambda row: analyze_sentiment_vader(row['title'] + " " + row['summary']), axis=1)

        filtered_data = filtered_data.sort_values(by="date_parsed", ascending=False)

        top_news = filtered_data.head(15)

        tab1, tab2 = st.tabs(["Notícias", "Distribuição Temporal"])

        with tab1:
            display_news(top_news)
            display_sentiment_analysis(top_news)
            display_categories(top_news)

        with tab2:
            display_distribution(filtered_data)
            
    else:
        st.error("Não foi possível carregar as notícias.")

# Execução do app
if __name__ == "__main__":
    main()
