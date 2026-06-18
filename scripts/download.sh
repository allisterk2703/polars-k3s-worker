mkdir -p data
wget https://www.dropbox.com/s/cn2utnr5ipathhh/all-the-news-2-1.zip -P data
unzip -p data/all-the-news-2-1.zip all-the-news-2-1.csv > data/all-the-news.csv
# rm data/all-the-news-2-1.zip