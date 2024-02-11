import socket
import urllib.robotparser as robotparser
import xml.etree.ElementTree as ET

# Parse robots.txt and sitemap

class RobotsTxtParser:
    def __init__(self, domain):
        self.robot_parser = robotparser.RobotFileParser()
        self.robot_parser.set_url(f"https://{domain}/robots.txt")
        self.robot_parser.read()
    
    def is_url_allowed(self, url):
        return self.robot_parser.can_fetch("*", url)
    
    #sitemap
    def parse_sitemap(self, sitemap_file_path):
        tree = ET.parse(sitemap_file_path)
        root = tree.getroot()
        urls = [url_child.text for url_child in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        
        return urls