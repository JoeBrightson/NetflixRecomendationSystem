from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

app = Flask(__name__)

# Load dataset
df = pd.read_csv('data/netflix_titles.csv')

# Optional: load IMDb ratings if available
imdb_df = None
if 'imdb_score' in df.columns:
    imdb_df = df[['title', 'imdb_score']]
else:
    # Fake IMDb score if not present, for sort simulation
    import numpy as np
    df['imdb_score'] = np.random.uniform(6, 9, size=len(df))

# Clean & preprocess
df['director'].fillna('Unknown', inplace=True)
df['cast'].fillna('Unknown', inplace=True)
df['country'].fillna('Unknown', inplace=True)
df['description'].fillna('No Description', inplace=True)
df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
df['year_added'] = df['date_added'].dt.year
df['month_added'] = df['date_added'].dt.month

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visualize')
def show_chart():
    chart = request.args.get('chart')
    plt.clf()
    filename = None
    text = None

    try:
        if chart == 'type':
            # Type distribution as distplot style
            plt.figure(figsize=(6, 4))
            sns.set_style("darkgrid")
            sns.histplot(data=df, x="type", shrink=0.2, palette="rocket", kde=True)
            plt.title('Type Distribution (Movie vs TV Show)')
            plt.xlabel('Content Type')
            plt.ylabel('Count')
            filename = 'type.png'

        elif chart == 'genre':
            genres = df['listed_in'].str.split(', ')
            data = genres.explode().value_counts().head(10)
            data.plot(kind='barh', color='crimson')
            plt.title('Top Genres')
            filename = 'genre.png'

        elif chart == 'country':
            countries = df['country'].str.split(', ')
            data = countries.explode().value_counts().head(10)
            data.plot(kind='bar', color='green')
            plt.title('Top Countries')
            filename = 'country.png'

        elif chart == 'rating':
            data = df['rating'].value_counts().head(10)
            data.plot(kind='bar', color='orange')
            plt.title('Top Ratings')
            filename = 'rating.png'

        elif chart == 'year':
            data = df['year_added'].value_counts().sort_index()
            data.plot(kind='line', marker='o', color='teal')
            plt.title('Yearly Content Added')
            filename = 'year.png'

        elif chart == 'duration':
            durations = df['duration'].dropna().value_counts()
            text = durations.head(20).to_string()

        elif chart == 'release':
            releases = df['release_year'].dropna().astype(int).value_counts().sort_index()
            text = releases.tail(30).to_string()

        elif chart == 'title':
            titles = df['title'].dropna().unique()
            text = '\n'.join(titles[:100])

        elif chart == 'director':
            directors_df = df[['director', 'title', 'imdb_score']].dropna()
            grouped = directors_df.groupby(['director', 'title']).mean().reset_index()
            sorted_df = grouped.sort_values(by='imdb_score', ascending=False)
            lines = [f"{row['director']} - {row['title']} (IMDb: {row['imdb_score']:.1f})" for _, row in sorted_df.head(100).iterrows()]
            text = '\n'.join(lines)

        elif chart == 'cast':
            cast_list = df['cast'].dropna().unique()
            text = '\n'.join(cast_list[:100])

        elif chart == 'description':
            descs = df[['title', 'description']].dropna()
            lines = [f"{row['title']}: {row['description']}" for _, row in descs.head(30).iterrows()]
            text = '\n\n'.join(lines)

        elif chart == 'missing':
            nulls = df.isnull().sum()
            missing_info = nulls[nulls > 0].sort_values(ascending=False)
            if missing_info.empty:
                text = "✅ No missing values in the dataset."
            else:
                text = "Missing Values (by column):\n\n" + missing_info.to_string()

        else:
            text = "❌ Invalid option selected."

        # Return response
        if filename:
            filepath = os.path.join('static', filename)
            plt.tight_layout()
            plt.savefig(filepath)
            return render_template('visualize.html', title=chart.upper(), image=filename, text=None)
        else:
            return render_template('visualize.html', title=chart.upper(), image=None, text=text)

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
