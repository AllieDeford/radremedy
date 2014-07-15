#!/usr/bin/env python
"""
Consume Howard Brown resource sites, export named tuples.

"""
from scraper import Scraper
from toolz import concat
from parse_helpers import a_cleanse, split, is_a_pseudo_header, get_soup, starts_with_end_tag
from bs4 import BeautifulSoup
import re


class HowardBrownScraper(Scraper):

    # a template for a page on Howard Brown waiting for a number
    # from a category
    BASE = "http://www.howardbrown.org/hb_services.asp?id=%d"
    DEFAULT_CATEGORIES = (2722, 2706, 2723, 2725, 2715, 2475)

    def __init__(self, category_ids=DEFAULT_CATEGORIES):
        super(HowardBrownScraper, self).__init__(source='Howard Brown')
        self.pages_to_scrape = map(lambda c: HowardBrownScraper.BASE % c, category_ids)
        self.black = re.compile('#00000')

    @staticmethod
    def parse_category(category):
        category = (category and category.text) or ''

        if len(category.split()) > 10:
            category = ''

        return category

    def get_category_from_link(self, link):
        return HowardBrownScraper.parse_category(link.find_previous('font', color=self.black))

    def process_record(self, link, text_following, url):
        category = self.get_category_from_link(link)

        if link.text and '://' in link['href']:
            # BeautifulSoup will not parse if starts with end tag
            txt_following = starts_with_end_tag.sub('', text_following)
            soup_following = BeautifulSoup(txt_following)
            # TODO: add 'category': category
            return {'name': a_cleanse(link.text),
                    'url': link['href'],
                    'description': a_cleanse("\n".join(soup_following.stripped_strings)),
                    'source': self.source,
                    'category': category}

        else:
            # TODO: Why aren't we scraping these? Do we want to?
            print("Not scraping: %s" % link)
            return {}

    def broken_by_bold(self, url):
        soup = get_soup(url).find('td', id='content')

        return map(lambda (link, txt): self.process_record(link, txt, url),
                   split(soup, is_a_pseudo_header))

    def scrape(self, targets=None):
        """
        This method walks every href in the targets list
        and gets it's data from the Howard brown website.

        The targets should be links to categories in the format
        http://www.howardbrown.org/hb_services.asp?id=<number>
        where number is a unsigned integer to the id of the
        category you want to scrape.

        The targets are turned into a set of unique values.

        The records returned are formatted as follow:
        ('category', 'link_text', 'link_target', 'description', 'source')

        So the final data looks like this:
        [('category', 'link_text', 'link_target', 'description', 'source'),
         ('category', 'link_text', 'link_target', 'description', 'source'),
         ...
         ('category', 'link_text', 'link_target', 'description', 'source')]

        :param targets: Links to pages you want to scrape. Defaults to the categories
        specified during instantiation.
        :return: A list of records.
        """
        return list(concat(map(self.broken_by_bold, set(targets or self.pages_to_scrape))))