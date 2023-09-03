from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import re
from model import generate_summary, analyze_sentiment

app = Flask(__name__)

def search_for_stock_news_urls(ticker):
    search_url = "https://www.google.com/search?q=yahoo+finance+{}&tbm=nws".format(ticker)
    r = requests.get(search_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atags = soup.find_all('a')
    hrefs = [link['href'] for link in atags]
    return hrefs

def strip_unwanted_urls(urls, exclude_list):
    val = []
    for url in urls:
        if 'https://' in url and not any(exclude_word in url for exclude_word in exclude_list):
            res = re.findall(r'(https?://\S+)', url)[0].split('&')[0]
            val.append(res)
    return list(set(val))

def scrape_and_process(urls):
  articles = []
  for url in urls:
    no = "Thank you for your patience. Our engineers are working quickly to resolve the issue."
    r = requests.get(url)
    soup = BeautifulSoup(r.text,'html.parser')
    paragraphs = soup.find_all('p')
    text = [paragraph.text for paragraph in paragraphs]
    words = ' '.join(text).split(' ')[:350]
    article = ' '.join(words)
    if article != no:
      articles.append(article)
  return articles

def create_output_array(summaries, scores, urls,monitored_tickers):
    output = []
    for ticker in monitored_tickers:
        for counter in range(len(summaries[ticker])):
            output_this = [
                ticker,
                summaries[ticker][counter],
                scores[ticker][counter]['label'],
                scores[ticker][counter]['score'],
                urls[ticker][counter]
            ]
            output.append(output_this)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker']
        exclude_list = ['maps', 'policies', 'preferences', 'accounts', 'support']
        cleaned_urls = strip_unwanted_urls(search_for_stock_news_urls(ticker), exclude_list)
        articles = scrape_and_process(cleaned_urls)

        summaries = []
        sentiment_scores = []
        monitored_tickers = [ticker]
        for article in articles:
            summary = generate_summary(article)
            sentiment_score = analyze_sentiment( summary)
            summaries.append(summary)
            sentiment_scores.append(sentiment_score)
        
        final_output = [ticker, summaries, str(sentiment_scores[0][0]['label']), str(sentiment_scores[0][0]['score']), str(cleaned_urls)]

        return render_template('index.html', final_output=final_output, ticker=ticker)


    return render_template('index.html', final_output=None, ticker=None)

if __name__ == '__main__':
    app.run(debug=True)
