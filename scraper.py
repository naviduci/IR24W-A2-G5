import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from simhash import Simhash, SimhashIndex
from utils.response import Response
from collections import Counter
from urllib.parse import urlparse
from bs4 import BeautifulSoup
nltk.download('stopwords')

# TODO: check fronteir url log, make output unique domain alphebetical

# It is important to filter out urls that are not with ics.uci.edu domain.
# Detect and avoid crawling very large files, especially if they have low information value
#  is_valid filters a large number of such extensions, but there may be more


# global variables
TokenList = [] # contain all token found on every tokenize pages
MaxTokens = 0 # the highest number of tokens found on a url
MaxURL = "" # the url which has the highest number of tokens
UniqueUrl = set() # contain every URL checked excluding fragments
Subdomains = dict() # contain the subdomain as a key and the amount of pages in that subdomain as the value

data_processed = 0 # the currect data processed

data_threshold = 1000000  # Set the data threshold (e.g., 1 MB)

# output file Output.txt containing our report.


def scraper(url, resp):
    """Take in two parameter for scrapper

    Args:
        url (str): added to the frontier / download from the cache
        resp (Response): see utils/response.py, response given by the caching server

    Returns:
        list: urls that are scraped from the response, wil be add to and retrieve from the
        Frontier cache.
    """
    global respStats
    if resp.status != 200:
        return []
    
    # check content withint a page of code 200
    if not resp.content or len(resp.content) < 100:
        print(f"Warning: URL {url} returned a 200 status but no data")
        return []

    links = extract_next_links(url, resp)

    # TODO: check if this work as intended
    global updateOutput
    
    # keep track of the data being processed, update at data processed threshold
    data_processed += len(resp.content)
    if data_processed >= data_threshold:
        getOutput()
        data_processed = 0
    # checks the list of urls found on a page using the is_valid function to
    # decide whether or not to return each url
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status != 200:
        return False
    
    webResponse = BeautifulSoup(resp.raw_response.content, 'html.parser')
    urlTokens = tokenize(webResponse.getText())
    update_max_tokens(urlTokens, url)

    return extract_links_from_tags(webResponse.find_all('a'))

def is_valid(url):
    global UniqueUrl


    try:
        parsed = urlparse(url)
        """
        print("URL:", url)
        print("Parsed Scheme:", parsed.scheme)
        print("Parsed Hostname:", parsed.hostname)
        print("Parsed Netloc:", parsed.netloc)
        print("Parsed Path:", parsed.path)
        """
        if parsed.hostname==None or parsed.netloc==None:
            # print("Hostname or Netloc is None")
            return False
        validDomains=[".ics.uci.edu","cs.uci.edu",".informatics.uci.edu",
                      ".stat.uci.edu"]
        if parsed.scheme not in set(["http", "https"]) or (url.find("?") != -1)\
                or (url.find("&") != -1):
            # print("Invalid scheme or contains query parameters")
            return False
        
        if any(dom in parsed.hostname for dom in validDomains) \
            and not re.search(r"(css|js|bmp|gif|jpe?g|ico"
                              + r"|png|tiff?|mid|mp2|mp3|mp4"
                              + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                              + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                              + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                              + r"|epub|dll|cnf|tgz|sha1|php|z"
                              + r"|thmx|mso|arff|rtf|jar|csv"
                              + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ppt|pptx|ppsx"
                              + r"|january|february|march|april|may|june|july"
                              + r"|august|september|october|november|december"
                              + r"|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec"
                              + r"|docs|docx|css|js|blog|page|calendar|archive|"
                                r"events|event|date)", parsed.path.lower())\
            and not re.match(r'\/(19|20)[0-9]{2}/|\/(19|20)[0-9]{2}$|\/(19|20)'
                             r'[0-9]{2}-[0-9]{1,2}|\/[0-9]{1,2}-(19|20)[0-9]{2}|'
                             r'[0-9]{1,2}-[0-9]{1,2}-(19|20)[0-9]{2}',
                             parsed.path.lower()):
            if url in UniqueUrl:
                 # print("URL already in UniqueUrl set")
                return False
            else:
                UniqueUrl.add(url)
                # print("URL added to UniqueUrl set")
                return True
        else:
            return False

    except ValueError as e:
        print(f'Error validating IP address for URL: {url}. Error: {e}')
        return False


# helper methods

def update_max_tokens(tokens, url):
    # compares current webpage's token count to the highest count to see if we
    # have a new highest num of tokens
    global MaxTokens
    global MaxURL
    if len(tokens) > MaxTokens:
        MaxTokens = len(tokens)
        MaxURL = url

def extract_links_from_tags(tags):
    # takes the list of tokens created and adds them to the DBDictionary
    #updateDBD(urlTokens)
    url_list = []
    for tag in tags:
        temp_url = tag.get('href')
        # if it finds the fragment tag in url it takes it off, the it appends
        # the url to our list of urls to search
        if temp_url is not None:
            possible_ind = temp_url.find('#')
            if possible_ind != -1:
                temp_url = temp_url[:possible_ind]
            url_list.append(temp_url)
    return url_list

def updateDBD(Tokens):
    # Take list of tokens updates the DBDictionary to include these tokens
    global TokenList
    TokenList.extend(Tokens)


def print50(wordList):
    #prints the frequencies of the list of words that it is passed
    freqList=Counter(wordList)
    finalList = []

    for word in freqList.most_common(50):
        finalList.append(word[0])
    return finalList

def updateSubdomains(UniqueUrl):
    #takes the set containing all unique urls and builds a dictionary
    # and number of page as value
    global Subdomains
    Subdomains.clear()
    for url in UniqueUrl:
        parsed = urlparse(url)
        if 'ics.uci.edu' in parsed.netloc.lower():
            Subdomains[parsed.hostname] = Subdomains.get(parsed.hostname, 0) + 1
           
def getOutput():
    # returns a string with the answer to all four problems 
    # TODO: make it output to a textfile
    global UniqueUrl
    global MaxURL
    global MaxTokens
    output = "1. Number of unique pages found: " + str(len(UniqueUrl)) + "\n\n"
    output += "2. Longest page in terms of number of words is " + str(MaxURL) \
              + " with " + str(MaxTokens) + " words total\n\n"
    output += "3. 50 most common words in order of most frequent to least " \
              "frequent are \n   "
    commonWords = print50(TokenList)
    for word in commonWords:
        output += word + "\n  "
    output += "\n4. Subdomains found: \n"
    # Sort subdomains by name
    updateSubdomains(UniqueUrl)
    sorted_subdomains = sorted(Subdomains.items(), key=lambda x: x[0])
    for key, value in sorted_subdomains.items():
        output += "   subdomain name: " + str(key) + ", pages found: " \
                  + str(value) + "\n"
    try:
        f = open("output.txt", "x")
    except Exception as e:
        print(f'Error writing output to file: {e} re-trying...')
        f = open("output.txt", "w")
    finally:
        f.write(output)
        f.close()
 
def tokenize(resp):
    # Tokenizes a text file looking for an sequence of 2+ alphanumerics while
    # ignoring stop words
    urlTokens = []
    # exclusionWords is a list of words that we dont want to include in out
    # list of tokens. These include months and
    # days, which appear in disproportionatly high numbers
    exclusionWords = {'january', 'jan', 'feb', 'february', 'march', 'mar',
                      'april', 'apr', 'may', 'june', 'jun', 'jul', 'july', 'aug'
                      'august', 'september', 'sept', 'aug', 'august', 'october',
                      'oct', 'november', 'nov', 'dec', 'december', 'monday',
                      'mon', 'tues', 'tuesday', 'wednesday', 'wed', 'thursday',
                      'thurs', 'friday', 'fri', 'sat', 'saturday', 'sun',
                      'sunday'}

    # tokenizes with the pattern '[a-z]{2,}' which finds two letters or more.
    # We excluded numbers because there were
    # no instances where we found numbers to have important meaning
    myTokenizer = RegexpTokenizer('[a-z]{2,}')
    tempTokens = myTokenizer.tokenize(resp)
    sw = stopwords.words('english')

    # this loop checks if tokens are stop words or words we want to exclude,
    # if not then it adds it to the token list
    for tokens in tempTokens:
        checkToken = tokens.lower()
        if checkToken not in sw and checkToken not in exclusionWords:
            urlTokens.append(checkToken)
        else:
            continue
    # updataDBD adds all tokens found on this page to our master list
    # containing all tokens found on all pages
    updateDBD(urlTokens)
    return urlTokens
