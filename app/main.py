from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import feedparser
from newspaper import Article

from bs4 import BeautifulSoup

from flashtext import KeywordProcessor
import tensorflow_hub as hub
import numpy as np

class RSSFeed(BaseModel):
    url: str

class Keyword(BaseModel):
    name: str
    keywords: List[str] = []

class ArticleContent(BaseModel):
    text: str
    keywords: List[Keyword] = []

class ArticleClass(BaseModel):
    id: str
    fulltext: str

class Similarities(BaseModel):
    articles: List[ArticleClass] = []

app = FastAPI()

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")

@app.post("/rss")
async def get_rss_entries(feed: RSSFeed):
    posts = feedparser.parse(feed.url)["entries"]

    for post in posts:
        article = Article(post["link"])
        article.download()
        article.parse()
        post["article_text"] = article.text

        if not bool(BeautifulSoup(post["summary"], "html.parser").find()):
            soup = BeautifulSoup(post["summary"], "html.parser")
            post["summary_parsed"] = soup.getText() 
        else:
            post["summary_parsed"] = post["summary"]

    return posts
    
@app.post("/keywords")
async def extract_keywords(article: ArticleContent):
    keyword_processor = KeywordProcessor()

    keyword_dict = {}
    for keyword in article.keywords:
        keyword_dict[keyword.name] = keyword.keywords

    keyword_processor.add_keywords_from_dict(keyword_dict)

    found_keywords = keyword_processor.extract_keywords(article.text)

    return found_keywords

@app.post("/similarities")
async def compute_similarities(input: Similarities):
    embeddings = embed([article.fulltext for article in input.articles]) 

    similarities = np.inner(embeddings, embeddings)

    results = {}

    for idx, article in enumerate(input.articles):
        similarity_by_index = np.argsort(similarities[idx])[::-1]

        max_sim = 0.75
        max_sidx = 0
        
        for sidx in similarity_by_index[1:]:          
            sim = float(similarities[idx][sidx])

            if sim <= max_sim:
                continue

            max_sim = sim
            max_sidx = sidx          

        if max_sim > 0.75:
            results[article.id] = input.articles[max_sidx].id

    return results