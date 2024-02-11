import re
from urllib.parse import urlparse, urljoin, urldefrag
from collections import Counter
from bs4 import BeautifulSoup

visited = set()
max_depth = 5  # for now
url_depth = {}


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


def scraper(url, resp):
    global visited, url_depth

    if url not in url_depth:
        url_depth[url] = 0

    depth_now = url_depth[url]

    if url in visited:
        print("visited")
        return []
    elif depth_now > max_depth:
        print("max depth, depth now:", depth_now)
        return []

    visited.add(url)

    if resp.status != 200 or not resp.raw_response:
        print("not 200 scraper!")
        return []

    links = extract_next_links(url, resp)
    valids = []

    for v in links:
        if is_valid(v) and v not in visited:
            if v not in url_depth:
                url_depth[v] = depth_now + 1
            valids.append(v)
    print("returning", valids)
    return valids


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
    urls = []

    if resp.status == 200 and resp.raw_response:
        try:
            page_con = resp.raw_response.content
            parsed_page = BeautifulSoup(page_con, "html.parser")
            for v in parsed_page.find_all('a'):
                href = v.get('href')

                if href:
                    full_url = urljoin(resp.url, href)
                    url_no_frag, frag = urldefrag(full_url)
                    urls.append(full_url)
        except Exception as errors:
            print(f"Something wrong (prob need to be checked)!: {errors}")
    else:
        print("some problem occured!", resp.status)
    return urls


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            print("not https :", parsed.scheme)
            return False

        url_domain = parsed.netloc

        if not any(v for v in domains if url_domain.endswith(v)):
            print("not domain : ", url_domain)
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", url)
        raise


