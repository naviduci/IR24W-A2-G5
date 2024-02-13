import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from collections import Counter
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
nltk.download('stopwords')

# global variables
tokenize_list = [] # contain all token found on every tokenize pages
max_url_token = 0 # the highest number of tokens found on a url
max_url = "" # the url which has the highest number of tokens
unique_set = set() # contain every URL checked excluding fragments
subdomains = dict() # contain the subdomain as a key and the amount of pages in that subdomain as the value
data_processed = 0 # the currect data processed
data_threshold = 2000000  # Set the data threshold (e.g., 2 MB)
frontier_empty = False # output file Output.txt containing our report.
visited_domains_robots = {}

#extra credit 1 start
def fetch_robots_txt(domain):
    """Fetch and cache the robots.txt file for a domain."""
    if domain in visited_domains_robots:
        return visited_domains_robots[domain]
    
    url = f"{domain}/robots.txt"
    try:
        response = requests.get(url)
        visited_domains_robots[domain] = response.text
    except requests.RequestException:
        visited_domains_robots[domain] = ""
    return visited_domains_robots[domain]

def parse_robots_txt(robots_txt, url_path):
    """Parse the robots.txt content to check if path is allowed."""
    disallow_paths = []
    for line in robots_txt.splitlines():
        if line.startswith("Disallow:"):
            disallowed_path = line.split(":", 1)[1].strip()
            disallow_paths.append(disallowed_path)
    return all(not url_path.startswith(path) for path in disallow_paths)

def can_fetch(url):
    """Determine if the crawler can fetch a URL based on robots.txt rules."""
    parsed_url = urlparse(url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_txt = fetch_robots_txt(domain)
    return parse_robots_txt(robots_txt, parsed_url.path)

#extra credit 1 end

#extra credit 2 functions (start), not implemented in scrapper yet

def get_fingerprint(content, n=3, functions=hash):

    soup = BeautifulSoup(content, 'html.parser')
    all_text = soup.get_text(separator=' ', strip=True)
    words = re.findall(r'\w+', all_text.lower())  #lower them

    # ngram saperate
    n_grams = zip(*[words[i:] for i in range(n)])
    n_grams = [' '.join(v) for v in n_grams]

    # this counter counts each words and make a dict {words: count#}
    counts = Counter(n_grams)

    hash_n_grams = {functions(k): v for k, v in counts.items()}

    return set(hash_n_grams)

#extra credit 2 functions (end)

def scraper(url, resp):
    global data_processed
    global data_threshold
    global frontier_empty
    # check content within a page of code 200
    if resp.status != 200 or not resp.raw_response.content:
        return []

    links = extract_next_links(url, resp)
    
    # keep track of the data being processed, update at data processed threshold
    data_processed = len(get_content_from_response(resp)) if get_content_from_response(resp) else 0
    if data_processed >= data_threshold:
        getOutput()
        data_processed = 0

    # this is added into the worker.py
    # if not links:
        # frontier_empty = True
    # Update holder.txt through getOutput() if frontier is empty
    # if frontier_empty:
        # getOutput()
        # frontier_empty = False
    
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
    text_content = soup.get_text()
    urlTokens = tokenize(text_content)
    
    if (urlTokens == []):
        return []
    update_max_tokens(urlTokens, url)
    
    return extract_links_from_tags(soup.find_all('a'))

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global visit_count
    
    try:
        url_without_fragment = urldefrag(url).url
        parsed = urlparse(url_without_fragment)
        validDomains=[".ics.uci.edu","cs.uci.edu",".informatics.uci.edu",
                      ".stat.uci.edu"]
        if parsed.hostname == None or parsed.netloc == None:
            return False
        if parsed.scheme not in set(["http", "https"]) or (url.find("?") != -1)\
                or (url.find("&") != -1):
            return False
        
        # Exclude URLs that match the following criteria:
        # 1. Include a valid domain from the `validDomains` list.
        # 2. Do not include certain file extensions or paths indicating non-content URLs.
        # 3. Do not include months or mentioned of calendar in the URLs 
        # 3. Do not match certain date or event-related patterns **REMOVED FOR TESTING**.
        """and not re.match(r'\/(19|20)[0-9]{2}/|\/(19|20)[0-9]{2}$|\/(19|20)'
                             r'[0-9]{2}-[0-9]{1,2}|\/[0-9]{1,2}-(19|20)[0-9]{2}|'
                             r'[0-9]{1,2}-[0-9]{1,2}-(19|20)[0-9]{2}',
                             parsed.path.lower())
            
                              """
        if any(domain in parsed.hostname for domain in validDomains) \
                and not re.search(r"(css|js|bmp|gif|jpe?g|ico"
                                  r"|png|tiff?|mid|mp2|mp3|mp4"
                                  r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                                  r"|ps|eps|tex|txt|ppt|pptx|doc|docx|xls|xlsx|names"
                                  r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                                  r"|epub|dll|cnf|tgz|sha1|php|z|odc"
                                  r"|thmx|mso|arff|rtf|jar|csv|docs|page"
                                  r"|rm|smil|wmv|swf|wma|zip|rar|gz)", parsed.path.lower())\
                and not re.match(r'\/(19|20)[0-9]{2}/|\/(19|20)[0-9]{2}$|\/(19|20)'
                             r'[0-9]{2}-[0-9]{1,2}|\/[0-9]{1,2}-(19|20)[0-9]{2}|'
                             r'[0-9]{1,2}-[0-9]{1,2}-(19|20)[0-9]{2}',
                             parsed.path.lower()):

            if url_without_fragment in visit_count and visit_count[url_without_fragment] >= 3:
                return False  # Do not crawl if already visited more than 3 times

            if url_without_fragment in unique_set:
                visit_count[url_without_fragment] += 1
                return False
            else:
                unique_set.add(url_without_fragment)
                visit_count[url_without_fragment] = 1
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
    global max_url_token
    global max_url
    if len(tokens) > max_url_token:
        max_url_token = len(tokens)
        max_url = url

def extract_links_from_tags(tags):
    # takes the list of tokens created and adds them to the DBDictionary
    #updateDBD(urlTokens)
    url_list = [tag.get('href').split('#')[0] for tag in tags if tag.get('href')]
    return url_list

def updateDBD(Tokens):
    # Take list of tokens updates the DBDictionary to include these tokens
    global tokenize_list
    tokenize_list.extend(Tokens)

def print_top_50(wordList):
    #prints the frequencies of the list of words that it is passed
    freqList = Counter(wordList)
    finalList = [word for word, _ in freqList.most_common(50)]
    return finalList

def update_subdomains(unique_set):
    # Takes the set containing all unique urls and builds a dictionary
    # with subdomains as keys and the number of occurrences as values
    global subdomains
    subdomains.clear()
    for url in unique_set:
        parsed = urlparse(url)
        if parsed.netloc.lower().endswith('.uci.edu'):
            subdomains[parsed.hostname] = subdomains.get(parsed.hostname, 0) + 1
           
def getOutput():
    # returns a string with the answer to all four problems 
    # TODO: create a textfile
    global unique_set
    global max_url
    global max_url_token
    holder = ""
    
    # Problem 1: Number of unique pages found
    holder += f"1. Number of unique pages found: {len(unique_set)}\n\n"

    # Problem 2: Longest page in terms of number of words
    holder += f"2. Longest page: {max_url} with {max_url_token} words total\n\n"

    # Problem 3: 50 most common words
    holder += "3. 50 most common words in order of most frequent to least frequent are:\n   "
    commonWords = print_top_50(tokenize_list)
    holder += "\n  ".join(commonWords) + "\n"

    # Problem 4: Subdomains found
    update_subdomains(unique_set)
    sorted_subdomains = sorted(subdomains.items(), key=lambda x: x[0])
    holder += "\n4. Subdomains found:\n"
    for key, value in sorted_subdomains:
        holder += f"   Subdomain name: {key}, Pages found: {value}\n"

    # Write holder to a text file
    with open("result.txt", "w") as file:
        file.write(holder)

    print("Result has been written to result.txt file.")
 
def tokenize(resp):
    # Tokenizes a text file looking for an sequence of alphanumerics while
    # ignoring stop words
    # exclusionWords exclude from the list of tokens. These include months and days
    urlTokens = []
    exclusionWords = {'january', 'jan', 'feb', 'february', 'march', 'mar',
                      'april', 'apr', 'may', 'june', 'jun', 'jul', 'july', 'aug'
                      'august', 'september', 'sept', 'aug', 'august', 'october',
                      'oct', 'november', 'nov', 'dec', 'december', 'monday',
                      'mon', 'tues', 'tuesday', 'wednesday', 'wed', 'thursday',
                      'thurs', 'friday', 'fri', 'sat', 'saturday', 'sun',
                      'sunday'}

    # tokenizes with the pattern r'\b[a-zA-Z]{3,}\b' which finds tokens of 2 or more characters.
    # We excluded numbers to reduce extracting low value information
    myTokenizer = RegexpTokenizer(r'\b[a-zA-Z]{3,}\b') # instead of '[a-z]{2,}'
    tempTokens = myTokenizer.tokenize(resp)
    sw = stopwords.words('english')

    # this loop checks if tokens are stop words or words we want to exclude,
    # if not then it adds it to the token list
    for tokens in tempTokens:
        checkToken = tokens.lower()
        if checkToken not in sw and checkToken not in exclusionWords:
            urlTokens.append(checkToken)

    # updataDBD adds all tokens found on this page to our master list
    # containing all tokens found on all pages
    updateDBD(urlTokens)
    
    # Check if the number of tokens is less than the minimum required
    min_tokens = 141
    if len(resp) < min_tokens:
        return []  # Return en empty list if the page doesn't have enough tokens

    return urlTokens