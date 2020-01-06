import scrapy
from datetime import date, timedelta, datetime


class AttractionSpider(scrapy.Spider):
    name = "attraction"

    start_urls = ["https://www.tripadvisor.com/Attraction_Review-g35418-d5006734-Reviews-Seven_Stars_Alpaca_Ranch-Coeur_d_Alene_Idaho.html"]

    def parse(self, response):

        slug = response.url.split('/')[-1]
        slug_template_list = slug.split('-')
        slug_template_list.insert(-2, "or{}")
        slug_template = "-".join(slug_template_list)
        last_page = int(response.css('div.pageNumbers a.pageNum::text')[-1].get())

        for page_number in range(last_page):
            yield response.follow(slug_template.format(page_number * 5), callback=self.parse_secondaries)

    @staticmethod
    def parse_date_string(date_string):
        if date_string == "Today":
            date_obj = date.today()
            date_string = date_obj.strftime("%b %-d %Y")
        elif date_string == "Yesterday":
            date_obj = date.today() - timedelta(days=1)
            date_string = date_obj.strftime("%b %-d %Y")
        elif len(date_string.split(" ")[-1]) <= 2:
            date_obj = datetime.strptime(date_string, "%b %d")
            today = datetime.today()
            date_obj = date_obj.replace(year=today.year)
            if date_obj > today:
                date_obj = date_obj - timedelta(years=1)
            date_string = date_obj.strftime("%b %-d %Y")
        return date_string

    def parse_secondaries(self, response):


        # entry['review_preview'] = review_body.q.text
        # entry['owner_response'] = owner_response.text if owner_response else None
        # return entry
        review_cards = response.css('div[class*="location-review-card-Card__section"]')
        for review in review_cards:

            title = review.css('a[class^="location-review-review-list-parts-ReviewTitle__reviewTitle"]')
            title_text = title.css('span::text').get()
            title_link = title.attrib['href']

            header = review.css('div[class*="social-member-event-MemberEventOnObjectBlock__member_event_block"]')
            reviewer_name = header.css('a.ui_header_link::text').get()
            reviewer_handle = header.css('a.ui_header_link').attrib['href'].split('/')[-1]

            '''
            Reviews may say "Today", "Yesterday", "Month Day", or "Month Year"
            Reviews do have their original dates posted on their actual page, but getting that
            would require an additional request per review, e.g. ~5x the number of reqs already.

            For now, converting to "Month Day Year" where available and "Month Year" otherwise.
            '''
            review_date_string = header.css('span::text').get().split('review ')[-1]
            review_date_string = self.parse_date_string(review_date_string)

            hometown = header.css('span[class*="social-member-common-MemberHometown__hometown"]::text').get()

            reviewer_stats = header.css('span[class*="social-member-MemberHeaderStats__bold"]::text')
            if len(reviewer_stats) == 2:
                reviewer_contributions = reviewer_stats[0].get()
                reviewer_helpfuls = reviewer_stats[1].get()
            else:
                reviewer_contributions = reviewer_stats[0].get()
                reviewer_helpfuls = 0

            review_has_photo = review.css('div[class^="location-review-review-list-parts-SectionThumbnails__flex_grid"]') \
                         .get() is not None

            body = review.css('div[class*="location-review-review-list-parts-SingleReview__mainCol"]')
            score = float(body.css('span.ui_bubble_rating').attrib['class'].split(" ")[-1].split("_")[-1]) / 10
            experience_date = body.css('span[class*="location-review-review-list-parts-EventDate__event_date"]::text')
            experience_date = experience_date.get().split(": ")[-1]

            review_preview = body.css('q').css("span::text").get()
            owner_response = review.css('span[class*="location-review-review-list-parts-OwnerResponse__reviewText"]').css('span::text').get()

            yield {"title_text" : title_text, "review_link" : title_link,
                   "reviewer_name" : reviewer_name, "reviewer_handle" : reviewer_handle,
                   "date_string" : review_date_string, "hometown" : hometown,
                   "reviewer_contributions" : reviewer_contributions,
                   "reviewer_helpfuls" : reviewer_helpfuls, "score" : score,
                   "experience_date" : experience_date, "review_has_photo" : review_has_photo,
                   "review_preview" : review_preview, "owner_response" : owner_response}

