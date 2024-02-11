import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from collections import Counter
nltk.download('stopwords')

# global variables
TokenList = [] # contain all token found on every tokenize pages
MaxTokens = 0 # the highest number of tokens found on a url
MaxURL = "" # the url which has the highest number of tokens
UniqueUrl = set() # contain every URL checked excluding fragments
Subdomains = dict() # contain the subdomain as a key and the amount of pages in that subdomain as the value
data_processed = 0 # the currect data processed
data_threshold = 5000000  # Set the data threshold (e.g., 5 MB)
frontier_empty = False # output file Output.txt containing our report.



def scraper(url, resp):
    # global respStats
    if resp.status != 200 or not resp.raw_response.content:
        return []
    
    # check content within a page of code 200

    links = extract_next_links(url, resp)

    # TODO: check if this works as intended
    # global updateOutput
    
    global data_processed
    global data_threshold
    global frontier_empty
    # keep track of the data being processed, update at data processed threshold
    data_processed = len(get_content_from_response(resp)) if get_content_from_response(resp) else 0
    if data_processed >= data_threshold:
        getOutput()
        data_processed = 0
    
    if not links:
        frontier_empty = True

    # Call getOutput() only if frontier is empty
    if frontier_empty:
        getOutput()
        frontier_empty = False
    
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

    if resp.status != 200 or not resp.raw_response.content:
        return []

    if (len(resp.raw_response.content) > 5 * 1024 * 1024):  # Set a threshold of 5 MB for testing:
        return []
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    urlTokens = tokenize(soup.getText())
    update_max_tokens(urlTokens, url)
    
    return extract_links_from_tags(soup.find_all('a'))

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global UniqueUrl
    
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]) or (url.find("?") != -1)\
                or (url.find("&") != -1):
            return False
        if parsed.hostname == None or parsed.netloc == None:
            # print("Hostname or Netloc is None")
            return False
        validDomains = [".ics.uci.edu","cs.uci.edu",".informatics.uci.edu",".stat.uci.edu"]

        # exclude list of file-extension urls along with any URLs that contain numeric date-like pattern
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
def get_content_from_response(resp):
    return resp.raw_response.content if hasattr(resp.raw_response, 'content') else None

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
    for key, value in sorted_subdomains:
        output += f"   subdomain name: {key}, pages found: {value}\n"
    try:
        f = open("output.txt", "x")
    except Exception as e:
        print(f'output.txt exist, updating file...')
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
