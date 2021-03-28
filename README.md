**POST /rss** <br>
body: feed <br>
Return posts from RSS feed with entries for `article_text`, `summary` and `summary_parsed`.
    
**POST /keywords** <br>
body: article <br>
Return keywords for a given articles

**POST /similarities** <br>
body: ??? <br>
Where max_sim is the minimum threshold for two news to be grouped together. 
Returns the associated news for each news. 
