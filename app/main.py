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
    text: str

class Similarities(BaseModel):
    articles: List[ArticleClass] = []

class Similarity(BaseModel):
    text1: str
    text2: str

app = FastAPI()

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")

@app.post("/rss")
async def get_rss_entries(feed: RSSFeed):
    try:
        posts = feedparser.parse(feed.url)["entries"]

        for post in posts:
            article = Article(post["link"])
            article.download()
            article.parse()
            post["article_text"] = article.text

            if bool(BeautifulSoup(post["summary"], "html.parser").find()):
                soup = BeautifulSoup(post["summary"], "html.parser")
                post["summary_parsed"] = soup.getText() 
            else:
                post["summary_parsed"] = post["summary"]

        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    
@app.post("/keywords")
async def extract_keywords(article: ArticleContent):
    try:
        keyword_processor = KeywordProcessor()

        keyword_dict = {}
        for keyword in article.keywords:
            keyword_dict[keyword.name] = keyword.keywords

        keyword_processor.add_keywords_from_dict(keyword_dict)

        found_keywords = keyword_processor.extract_keywords(article.text)

        return found_keywords
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

@app.post("/similarities")
async def compute_similarities(input: Similarities):
    try:
        embeddings = embed([article.text for article in input.articles]) 

        similarities = np.inner(embeddings, embeddings)

        results = {}

        for idx, article in enumerate(input.articles):
            similarity_by_index = np.argsort(similarities[idx])[::-1]

            result = {}
            
            for sidx in similarity_by_index[0:]:          
                sim = float(similarities[idx][sidx])

                if input.articles[sidx].id == article.id:
                    continue

                result[input.articles[sidx].id] = sim
                
            results[article.id] = result
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)

@app.post("/similarity")
async def compute_similarity(input: Similarity):
    try:
        embeddings = embed([input.text1, input.text2]) 

        similarities = np.inner(embeddings, embeddings)

        return float(similarities[0][1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
