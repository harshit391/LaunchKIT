import requests
from bs4 import BeautifulSoup

url = "https://www.coursera.org/programs/cse-batch-2022-3rd-year-ailn5/learn/ibm-ai-workflow-business-priorities-data-ingestion?specialization=ibm-ai-workflow"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

quotes = soup.find_all("span", class_="text")
authors = soup.find_all("small", class_="author")

for i in range(len(quotes)):
    print(f"Quote: {quotes[i].get_text()}")
    print(f"Author: {authors[i].get_text()}")
    print("-" * 50)
