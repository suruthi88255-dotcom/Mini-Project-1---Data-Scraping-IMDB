import pandas as pd
import numpy as np
import re
import warnings
warnings.filterwarnings('ignore')

def load_imdb_csv(file_path):
    """
    Load and preprocess IMDb CSV data for analysis
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: Processed dataframe ready for analysis
    """
    
    try:
        print(f"📂 Loading data from: {file_path}")
        
        # Load the CSV file
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"✅ Successfully loaded {len(df)} rows")
        
        # Display basic info about the dataset
        print(f"\n📊 Dataset Overview:")
        print(f"   • Columns: {list(df.columns)}")
        print(f"   • Shape: {df.shape}")
        print(f"   • Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Clean and process the data
        print("\n🔧 Processing data...")
        
        # 1. Convert rating to numeric
        df['IMDb Rating'] = pd.to_numeric(df['IMDb Rating'], errors='coerce')
        
        # 2. Process runtime to hours
        def runtime_to_hours(runtime_str):
            """Convert runtime string to hours (float)"""
            if pd.isna(runtime_str) or runtime_str == 'N/A':
                return None
            
            hours = 0
            minutes = 0
            
            # Match patterns like "2h 30m", "1h", "90m"
            hour_match = re.search(r'(\d+)h', str(runtime_str))
            min_match = re.search(r'(\d+)m', str(runtime_str))
            
            if hour_match:
                hours = int(hour_match.group(1))
            if min_match:
                minutes = int(min_match.group(1))
            
            total_hours = hours + (minutes / 60)
            return round(total_hours, 2) if total_hours > 0 else None
        
        df['Duration_Hours'] = df['Runtime'].apply(runtime_to_hours)
        
        # 3. Extract and assign genres (simplified approach)
        def extract_genres(title):
            """Extract genres based on title keywords"""
            if pd.isna(title):
                return 'Drama'
                
            title_lower = str(title).lower()
            genres = []
            
            # Genre keyword mapping
            genre_keywords = {
                'Action': ['action', 'fight', 'war', 'battle', 'combat', 'martial'],
                'Romance': ['love', 'romance', 'wedding', 'romantic', 'heart'],
                'Horror': ['horror', 'scary', 'fear', 'dark', 'evil', 'ghost', 'zombie'],
                'Comedy': ['comedy', 'funny', 'laugh', 'humor', 'fun'],
                'Drama': ['drama', 'life', 'story', 'human', 'family'],
                'Sci-Fi': ['sci-fi', 'space', 'future', 'robot', 'alien', 'time'],
                'Crime': ['crime', 'murder', 'detective', 'police', 'criminal'],
                'Adventure': ['adventure', 'journey', 'quest', 'treasure', 'exploration'],
                'Thriller': ['thriller', 'suspense', 'mystery', 'dangerous'],
                'Fantasy': ['fantasy', 'magic', 'wizard', 'dragon', 'fairy'],
                'Animation': ['animation', 'animated', 'cartoon'],
                'Documentary': ['documentary', 'real', 'true', 'documentary'],
                'Biography': ['biography', 'bio', 'life of', 'story of'],
                'History': ['history', 'historical', 'war', 'ancient'],
                'Music': ['music', 'musical', 'song', 'band', 'concert'],
                'Sport': ['sport', 'football', 'basketball', 'baseball', 'olympic'],
                'Western': ['western', 'cowboy', 'frontier'],
                'Family': ['family', 'kids', 'children', 'kid']
            }
            
            # Check for genre keywords in title
            for genre, keywords in genre_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    genres.append(genre)
            
            # Default to Drama if no genre found
            if not genres:
                genres = ['Drama']
            
            return ', '.join(genres)
        
        df['Genres'] = df['Title'].apply(extract_genres)
        df['Primary_Genre'] = df['Genres'].str.split(',').str[0].str.strip()
        
        # 4. Clean votes column - ensure it's numeric
        df['Votes_Numeric'] = pd.to_numeric(df['Votes_Numeric'], errors='coerce')
        
        # 5. Add duration categories
        def duration_category(hours):
            """Categorize movies by duration"""
            if pd.isna(hours):
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
        
        # 6. Add rating categories
        def rating_category(rating):
            """Categorize movies by rating"""
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
        
        # 7. Remove rows with missing critical data
        original_count = len(df)
        df = df.dropna(subset=['Title', 'IMDb Rating'])
        dropped_count = original_count - len(df)
        
        if dropped_count > 0:
            print(f"⚠️  Dropped {dropped_count} rows with missing critical data")
        
        # 8. Clean year column
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        
        # Display processing results
        print(f"✅ Data processing complete!")
        print(f"\n📈 Processed Dataset Summary:")
        print(f"   • Final rows: {len(df)}")
        print(f"   • Movies with ratings: {df['IMDb Rating'].notna().sum()}")
        print(f"   • Movies with duration: {df['Duration_Hours'].notna().sum()}")
        print(f"   • Average rating: {df['IMDb Rating'].mean():.2f}")
        print(f"   • Average duration: {df['Duration_Hours'].mean():.1f} hours")
        print(f"   • Unique genres: {df['Primary_Genre'].nunique()}")
        print(f"   • Year range: {df['Year'].min():.0f} - {df['Year'].max():.0f}")
        
        # Display genre distribution
        print(f"\n🎭 Genre Distribution:")
        genre_counts = df['Primary_Genre'].value_counts()
        for genre, count in genre_counts.head(10).items():
            print(f"   • {genre}: {count} movies ({count/len(df)*100:.1f}%)")
        
        # Display rating distribution
        print(f"\n⭐ Rating Distribution:")
        rating_counts = df['Rating_Category'].value_counts()
        for category, count in rating_counts.items():
            print(f"   • {category}: {count} movies ({count/len(df)*100:.1f}%)")
        
        # Display duration distribution
        print(f"\n⏱️ Duration Distribution:")
        duration_counts = df['Duration_Category'].value_counts()
        for category, count in duration_counts.items():
            print(f"   • {category}: {count} movies ({count/len(df)*100:.1f}%)")
        
        # Display top movies
        print(f"\n🏆 Top 10 Movies by Rating:")
        top_movies = df.nlargest(10, 'IMDb Rating')[['Title', 'IMDb Rating', 'Primary_Genre', 'Year']]
        for idx, movie in top_movies.iterrows():
            print(f"   {movie['Title'][:40]:<40} | {movie['IMDb Rating']} | {movie['Primary_Genre']} | {movie['Year']:.0f}")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ Error: File not found at {file_path}")
        print("Please check the file path and try again.")
        return None
        
    except pd.errors.EmptyDataError:
        print(f"❌ Error: The file at {file_path} is empty or invalid.")
        return None
        
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return None

def save_processed_data(df, output_path):
    """
    Save the processed dataframe to a new CSV file
    
    Args:
        df (pandas.DataFrame): Processed dataframe
        output_path (str): Path where to save the processed data
    """
    try:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ Processed data saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")
        return False

def quick_analysis(df):
    """
    Perform quick analysis on the dataset
    
    Args:
        df (pandas.DataFrame): Processed dataframe
    """
    print("\n" + "="*60)
    print("📊 QUICK ANALYSIS REPORT")
    print("="*60)
    
    # Basic statistics
    print(f"\n📈 Basic Statistics:")
    print(f"   • Total Movies: {len(df):,}")
    print(f"   • Average Rating: {df['IMDb Rating'].mean():.2f}")
    print(f"   • Median Rating: {df['IMDb Rating'].median():.2f}")
    print(f"   • Highest Rating: {df['IMDb Rating'].max():.1f}")
    print(f"   • Lowest Rating: {df['IMDb Rating'].min():.1f}")
    
    # Voting statistics
    if df['Votes_Numeric'].notna().any():
        print(f"   • Total Votes: {df['Votes_Numeric'].sum():,.0f}")
        print(f"   • Average Votes per Movie: {df['Votes_Numeric'].mean():,.0f}")
        print(f"   • Most Voted Movie: {df.loc[df['Votes_Numeric'].idxmax(), 'Title']}")
    
    # Duration statistics
    if df['Duration_Hours'].notna().any():
        print(f"   • Average Duration: {df['Duration_Hours'].mean():.1f} hours")
        print(f"   • Shortest Movie: {df.loc[df['Duration_Hours'].idxmin(), 'Title']} ({df['Duration_Hours'].min():.1f}h)")
        print(f"   • Longest Movie: {df.loc[df['Duration_Hours'].idxmax(), 'Title']} ({df['Duration_Hours'].max():.1f}h)")
    
    # Genre insights
    print(f"\n🎭 Genre Insights:")
    print(f"   • Most Popular Genre: {df['Primary_Genre'].mode().iloc[0]}")
    print(f"   • Total Genres: {df['Primary_Genre'].nunique()}")
    
    # Find highest rated genre
    genre_ratings = df.groupby('Primary_Genre')['IMDb Rating'].mean().sort_values(ascending=False)
    print(f"   • Highest Rated Genre: {genre_ratings.index[0]} (avg: {genre_ratings.iloc[0]:.2f})")
    
    # Year insights
    if df['Year'].notna().any():
        print(f"\n📅 Year Insights:")
        year_counts = df['Year'].value_counts().sort_index()
        most_productive_year = year_counts.idxmax()
        print(f"   • Most Productive Year: {most_productive_year:.0f} ({year_counts.max()} movies)")
        print(f"   • Year Range: {df['Year'].min():.0f} - {df['Year'].max():.0f}")
    
    # Quality insights
    high_quality_movies = len(df[df['IMDb Rating'] >= 8.0])
    print(f"\n⭐ Quality Insights:")
    print(f"   • High Quality Movies (8.0+): {high_quality_movies} ({high_quality_movies/len(df)*100:.1f}%)")
    
    if df['Votes_Numeric'].notna().any():
        popular_and_quality = len(df[(df['IMDb Rating'] >= 8.0) & (df['Votes_Numeric'] >= 10000)])
        print(f"   • Popular & High Quality: {popular_and_quality} movies")

# ========================
# EXAMPLE USAGE
# ========================

if __name__ == "__main__":
    # Example usage of the loader
    print("🎬 IMDb CSV Data Loader")
    print("="*50)
    
    # Set your CSV file path here
    csv_file_path = r"C:\Users\surut\OneDrive\Desktop\IMDB\outcsv.csv"  # Update this path
    
    # Load and process the data
    df = load_imdb_csv(csv_file_path)
    
    if df is not None:
        # Perform quick analysis
        quick_analysis(df)
        
        # Optional: Save processed data
        save_choice = input("\n💾 Would you like to save the processed data? (y/n): ").lower()
        if save_choice == 'y':
            output_path = csv_file_path.replace('.csv', '_processed.csv')
            save_processed_data(df, output_path)
        
        print("\n✅ Data loading complete! The dataframe 'df' is ready for analysis.")
        print("\n🚀 Next steps:")
        print("   1. Run the Streamlit dashboard: streamlit run dashboard.py")
        print("   2. Or use the dataframe 'df' for custom analysis")
        print("   3. Available columns:", list(df.columns))
        
    else:
        print("\n❌ Failed to load data. Please check your file path and try again.")