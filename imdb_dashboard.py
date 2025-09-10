import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ========================
# PAGE CONFIG
# ========================
st.set_page_config(
    page_title="IMDb 2024 Movies Analysis",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #f5c518;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #f5c518;
        margin: 0.5rem 0;
    }
    .filter-section {
        background-color: #2d2d2d;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# DATA LOADING AND PROCESSING
# ========================
@st.cache_data
def load_and_process_data(file_path):
    """Load CSV data and process for analysis"""
    try:
        # Load the CSV file
        if hasattr(file_path, 'read'):
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        df = df.copy()
        
        # Convert rating to numeric
        df['IMDb Rating'] = pd.to_numeric(df['IMDb Rating'], errors='coerce')
        
        # Convert runtime string to hours
        def runtime_to_hours(runtime_str):
            if pd.isna(runtime_str) or runtime_str in ['N/A', '']:
                return None
            hours, minutes = 0, 0
            try:
                hour_match = re.search(r'(\d+)h', str(runtime_str))
                min_match = re.search(r'(\d+)m', str(runtime_str))
                if hour_match:
                    hours = int(hour_match.group(1))
                if min_match:
                    minutes = int(min_match.group(1))
                total_hours = hours + (minutes / 60)
                return round(total_hours, 2) if total_hours > 0 else None
            except:
                return None
        
        df['Duration_Hours'] = df['Runtime'].apply(runtime_to_hours)
        
        # Extract genres from title keywords
        def extract_genres(title, year):
            if pd.isna(title):
                return 'Drama'
            title_lower = str(title).lower()
            genres = []
            genre_keywords = {
                'Action': ['action', 'fight', 'war', 'battle', 'combat', 'martial', 'warrior'],
                'Romance': ['love', 'romance', 'wedding', 'romantic', 'heart'],
                'Horror': ['horror', 'scary', 'fear', 'dark', 'evil', 'ghost', 'zombie', 'demon'],
                'Comedy': ['comedy', 'funny', 'laugh', 'humor', 'fun', 'comic'],
                'Drama': ['drama', 'life', 'story', 'human', 'family', 'emotional'],
                'Sci-Fi': ['sci-fi', 'space', 'future', 'robot', 'alien', 'time', 'science'],
                'Crime': ['crime', 'murder', 'detective', 'police', 'criminal', 'investigation'],
                'Adventure': ['adventure', 'journey', 'quest', 'treasure', 'exploration', 'expedition'],
                'Thriller': ['thriller', 'suspense', 'mystery', 'dangerous', 'tension'],
                'Fantasy': ['fantasy', 'magic', 'wizard', 'dragon', 'fairy', 'mythical'],
                'Animation': ['animation', 'animated', 'cartoon', 'anime'],
                'Documentary': ['documentary', 'real', 'true', 'documentary', 'factual'],
                'Biography': ['biography', 'bio', 'life of', 'story of', 'based on'],
                'History': ['history', 'historical', 'ancient', 'period', 'era'],
                'Music': ['music', 'musical', 'song', 'band', 'concert', 'singer'],
                'Sport': ['sport', 'football', 'basketball', 'baseball', 'olympic', 'athlete'],
                'Western': ['western', 'cowboy', 'frontier', 'wild west'],
                'Family': ['family', 'kids', 'children', 'kid', 'child']
            }
            for genre, keywords in genre_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    genres.append(genre)
            if not genres:
                genres = ['Drama']
            return ', '.join(genres)
        
        df['Genres'] = df.apply(lambda x: extract_genres(x.get('Title', ''), x.get('Year', '')), axis=1)
        df['Primary_Genre'] = df['Genres'].str.split(',').str[0].str.strip()
        
        # Clean votes column
        def clean_votes(votes_val):
            if pd.isna(votes_val) or votes_val in ['N/A', '']:
                return 0
            try:
                return pd.to_numeric(votes_val, errors='coerce')
            except:
                return 0
        
        df['Votes_Numeric'] = df.get('Votes_Numeric', df.get('Votes', 0)).apply(clean_votes)
        
        # Drop invalid rows
        df = df.dropna(subset=['Title'])
        df = df[df['Title'].notna() & (df['Title'] != '') & (df['Title'] != 'N/A')]
        
        if df['IMDb Rating'].isna().all():
            st.error("No valid ratings found in the data.")
            return None
        
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(2024)
        
        # Duration categories
        def duration_category(hours):
            if pd.isna(hours) or hours == 0:
                return 'Unknown'
            elif hours < 1.5:
                return 'Short (< 1.5h)'
            elif hours < 2.5:
                return 'Medium (1.5-2.5h)'
            elif hours < 3.5:
                return 'Long (2.5-3.5h)'
            else:
                return 'Very Long (> 3.5h)'
        df['Duration_Category'] = df['Duration_Hours'].apply(duration_category)
        
        # Rating categories
        def rating_category(rating):
            if pd.isna(rating):
                return 'Unrated'
            elif rating < 6.0:
                return 'Poor (< 6.0)'
            elif rating < 7.0:
                return 'Average (6.0-7.0)'
            elif rating < 8.0:
                return 'Good (7.0-8.0)'
            elif rating < 9.0:
                return 'Excellent (8.0-9.0)'
            else:
                return 'Masterpiece (9.0+)'
        df['Rating_Category'] = df['IMDb Rating'].apply(rating_category)
        
        df = df[df['Primary_Genre'].notna()].reset_index(drop=True)
        
        if len(df) == 0:
            st.error("No valid data found after processing.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# ========================
# VISUALIZATION FUNCTIONS
# ========================
def plot_top_movies_rating(df, n=10):
    df_filtered = df[df['Votes_Numeric'] > 1000].nlargest(n, 'IMDb Rating')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_filtered['Votes_Numeric'],
        y=df_filtered['IMDb Rating'],
        mode='markers+text',
        marker=dict(
            size=15,
            color=df_filtered['IMDb Rating'],
            colorscale='Viridis',
            colorbar=dict(title='IMDb Rating'),
            line=dict(width=2, color='white')
        ),
        text=df_filtered['Title'].str[:20] + '...',
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Rating: %{y}<br>Votes: %{x:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        title=f'Top {n} Movies by Rating (with significant votes)',
        xaxis_title='Number of Votes',
        yaxis_title='IMDb Rating',
        height=500,
        template='plotly_dark'
    )
    return fig

def plot_genre_distribution(df):
    genre_counts = df['Primary_Genre'].value_counts()
    fig = px.bar(
        x=genre_counts.index,
        y=genre_counts.values,
        title='Movie Distribution by Genre',
        labels={'x': 'Genre', 'y': 'Number of Movies'},
        color=genre_counts.values,
        color_continuous_scale='viridis'
    )
    fig.update_layout(template='plotly_dark', height=500, xaxis_tickangle=-45)
    return fig

def plot_avg_duration_by_genre(df):
    avg_duration = df.groupby('Primary_Genre')['Duration_Hours'].mean().sort_values(ascending=True)
    fig = px.bar(
        x=avg_duration.values,
        y=avg_duration.index,
        orientation='h',
        title='Average Movie Duration by Genre',
        labels={'x': 'Average Duration (Hours)', 'y': 'Genre'},
        color=avg_duration.values,
        color_continuous_scale='plasma'
    )
    fig.update_layout(template='plotly_dark', height=500)
    return fig

def plot_voting_trends_by_genre(df):
    voting_stats = df.groupby('Primary_Genre')['Votes_Numeric'].agg(['mean', 'median', 'sum']).reset_index()
    fig = px.bar(
        voting_stats,
        x='Primary_Genre',
        y='mean',
        title='Average Voting Counts by Genre',
        labels={'mean': 'Average Votes', 'Primary_Genre': 'Genre'},
        color='mean',
        color_continuous_scale='blues'
    )
    fig.update_layout(template='plotly_dark', height=500, xaxis_tickangle=-45)
    return fig

def plot_rating_distribution(df):
    fig = px.histogram(
        df,
        x='IMDb Rating',
        nbins=30,
        title='Distribution of IMDb Ratings',
        labels={'count': 'Number of Movies'},
        color_discrete_sequence=['#f5c518']
    )
    fig.add_vline(
        x=df['IMDb Rating'].mean(),
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {df['IMDb Rating'].mean():.2f}"
    )
    fig.update_layout(template='plotly_dark', height=400)
    return fig

def create_genre_rating_leaders_table(df):
    genre_leaders = df.loc[df.groupby('Primary_Genre')['IMDb Rating'].idxmax()]
    return genre_leaders[['Primary_Genre', 'Title', 'IMDb Rating', 'Votes_Numeric', 'Year']].sort_values('IMDb Rating', ascending=False)

def plot_popular_genres_pie(df):
    genre_votes = df.groupby('Primary_Genre')['Votes_Numeric'].sum().sort_values(ascending=False)
    fig = px.pie(
        values=genre_votes.values,
        names=genre_votes.index,
        title='Most Popular Genres by Total Votes',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(template='plotly_dark', height=500)
    return fig

def create_duration_extremes_table(df):
    df_clean = df.dropna(subset=['Duration_Hours'])
    shortest = df_clean.nsmallest(5, 'Duration_Hours')[['Title', 'Duration_Hours', 'IMDb Rating', 'Primary_Genre']]
    longest = df_clean.nlargest(5, 'Duration_Hours')[['Title', 'Duration_Hours', 'IMDb Rating', 'Primary_Genre']]
    return shortest, longest

def plot_genre_ratings_heatmap(df):
    genre_year_ratings = df.groupby(['Primary_Genre', 'Year'])['IMDb Rating'].mean().unstack(fill_value=0)
    fig = px.imshow(
        genre_year_ratings.values,
        x=genre_year_ratings.columns,
        y=genre_year_ratings.index,
        color_continuous_scale='RdYlBu_r',
        title='Average Ratings by Genre and Year',
        labels={'color': 'Average Rating'}
    )
    fig.update_layout(template='plotly_dark', height=500)
    return fig

def plot_correlation_analysis(df):
    """Correlation between ratings and voting counts"""
    df_clean = df.dropna(subset=['IMDb Rating', 'Votes_Numeric']).copy()
    missing_durations = df_clean['Duration_Hours'].isna().sum()
    if missing_durations > 0:
        st.warning(f"⚠️ {missing_durations} movies without duration were skipped in this scatter plot.")
    df_clean = df_clean.dropna(subset=['Duration_Hours'])
    fig = px.scatter(
        df_clean,
        x='Votes_Numeric',
        y='IMDb Rating',
        color='Primary_Genre',
        size='Duration_Hours',
        hover_data=['Title', 'Year'],
        title='Correlation: Ratings vs Voting Counts',
        labels={'Votes_Numeric': 'Number of Votes', 'IMDb Rating': 'IMDb Rating'}
    )
    if len(df_clean) > 1:
        fig.add_trace(go.Scatter(
            x=df_clean['Votes_Numeric'],
            y=np.poly1d(np.polyfit(df_clean['Votes_Numeric'], df_clean['IMDb Rating'], 1))(df_clean['Votes_Numeric']),
            mode='lines',
            name='Trendline',
            line=dict(color='red', dash='dash')
        ))
    fig.update_layout(template='plotly_dark', height=500)
    return fig

# ========================
# MAIN APP
# ========================
def main():
    st.markdown('<h1 class="main-header">🎬 IMDb 2024 Movies Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload your IMDb CSV file", type=['csv'])
    if not uploaded_file:
        default_path = st.text_input("Or enter the CSV file path:", value=r"C:\Users\surut\OneDrive\Desktop\IMDB\outcsv.csv")
        if st.button("Load Data from Path") and default_path:
            df = load_and_process_data(default_path)
            st.session_state['df'] = df
    else:
        df = load_and_process_data(uploaded_file)
        st.session_state['df'] = df
    
    if 'df' not in st.session_state or st.session_state['df'] is None:
        st.warning("Please upload a CSV file or provide a valid file path.")
        st.stop()
    
    df = st.session_state['df']
    st.success(f"✅ Data loaded successfully! {len(df)} movies found.")
    
    # Sidebar filters
    st.sidebar.header("🔍 Filter Options")
    duration_options = ['All'] + sorted(df['Duration_Category'].unique().tolist())
    selected_duration = st.sidebar.selectbox("Duration Category", duration_options)
    min_rating = st.sidebar.slider("Minimum IMDb Rating", float(df['IMDb Rating'].min()), float(df['IMDb Rating'].max()), float(df['IMDb Rating'].min()), step=0.1)
    min_votes = st.sidebar.number_input("Minimum Votes", min_value=0, max_value=int(df['Votes_Numeric'].max()), value=0, step=1000)
    genre_options = ['All'] + sorted(df['Primary_Genre'].unique().tolist())
    selected_genre = st.sidebar.selectbox("Genre", genre_options)
    
    filtered_df = df.copy()
    if selected_duration != 'All':
        filtered_df = filtered_df[filtered_df['Duration_Category'] == selected_duration]
    filtered_df = filtered_df[filtered_df['IMDb Rating'] >= min_rating]
    filtered_df = filtered_df[filtered_df['Votes_Numeric'] >= min_votes]
    if selected_genre != 'All':
        filtered_df = filtered_df[filtered_df['Primary_Genre'] == selected_genre]
    
    st.sidebar.markdown(f"**Filtered Results: {len(filtered_df)} movies**")
    if len(filtered_df) == 0:
        st.warning("No movies match your filters.")
        st.stop()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Movies", len(filtered_df))
    with col2:
        st.metric("Average Rating", f"{filtered_df['IMDb Rating'].mean():.2f}")
    with col3:
        st.metric("Total Votes", f"{filtered_df['Votes_Numeric'].sum():,.0f}")
    with col4:
        st.metric("Avg Duration", f"{filtered_df['Duration_Hours'].mean():.1f}h")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🎭 Genre Analysis", "⭐ Rating Analysis", "📈 Advanced Analytics", "📋 Data Table"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_top_movies_rating(filtered_df, 10), use_container_width=True)
        with col2:
            st.plotly_chart(plot_genre_distribution(filtered_df), use_container_width=True)
        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(plot_rating_distribution(filtered_df), use_container_width=True)
        with col4:
            st.plotly_chart(plot_popular_genres_pie(filtered_df), use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_avg_duration_by_genre(filtered_df), use_container_width=True)
        with col2:
            st.plotly_chart(plot_voting_trends_by_genre(filtered_df), use_container_width=True)
    
    with tab3:
        st.plotly_chart(plot_genre_ratings_heatmap(filtered_df), use_container_width=True)
        st.subheader("Top Rated Movies by Genre")
        st.dataframe(create_genre_rating_leaders_table(filtered_df), use_container_width=True)
    
    with tab4:
        st.plotly_chart(plot_correlation_analysis(filtered_df), use_container_width=True)
        st.subheader("Shortest and Longest Movies")
        shortest, longest = create_duration_extremes_table(filtered_df)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🎬 Shortest Movies")
            st.dataframe(shortest, use_container_width=True)
        with col2:
            st.markdown("### 🎬 Longest Movies")
            st.dataframe(longest, use_container_width=True)
    
    with tab5:
        st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
