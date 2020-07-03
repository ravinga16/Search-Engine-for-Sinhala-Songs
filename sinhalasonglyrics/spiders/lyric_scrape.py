import scrapy
from sinhalasonglyrics.items import LyricsItem
from datetime import datetime
import re
from mtranslate import translate
import pickle


## variables

translated_dict = {}            # dictionary lookup to avoid translate failures and speedup process


def translate_en_si(string):

    if string in translated_dict:
        return translated_dict[string]
    elif string.lower() == "unknown":
        return ''
    else:
        translated = translate(string, 'si', 'en')
        translated_dict[string] = translated
        return translated


def array_translation(stringList):
    temp = []
    for string in stringList:
        temp.append(translate_en_si(string))    
    
    return temp


class SinhalaLyrics(scrapy.Spider):
    name = 'scraper'
    start_urls = ["https://sinhalasongbook.com/all-sinhala-song-lyrics-and-chords/?_page=" + str(2) + ""]


    def parse(self, response):
        global translated_dict

        try:
            translated_dict = pickle.load(open('../translated_dict.pickle', 'rb'))
        except (OSError, IOError):
            pickle.dump(translated_dict, open('../translated_dict.pickle', 'wb'))

        for href in response.xpath("//main[contains(@id, 'genesis-content')]//div[contains(@class, 'entry-content')]//div[contains(@class, 'pt-cv-wrapper')]//h4[contains(@class, 'pt-cv-title')]/a/@href"):
            url = href.extract()

            yield scrapy.Request(url, callback=self.parse_dir_contents)
    

    def parse_dir_contents(self, response):
        global translated_dict

        item = LyricsItem()


        # song name
        songName = response.xpath("//div[contains(@class, 'site-inner')]//header[contains(@class, 'entry-header')]/h1/text()").extract()[0]
        songName = re.split('\||–|-', songName)
        item['song_name'] = songName[1].strip()

        # genre
        genre = response.xpath("//div[contains(@class, 'entry-content')]//div[contains(@class, 'su-column su-column-size-3-6')]//span[contains(@class, 'entry-tags')]/a/text()").extract()
        if len(genre) == 0:
            item['genre'] = []
        else:
            genre = array_translation(genre)
            item['genre'] = genre

        # artist name
        artistName = response.xpath("//div[contains(@class, 'entry-content')]//div[contains(@class, 'su-column su-column-size-3-6')]//span[contains(@class, 'entry-categories')]/a/text()").extract()
        if len(artistName) == 0:
            item['artist'] = []
        else:
            artistName = array_translation(artistName)
            item['artist'] = artistName
        
        
        
        # lyric writer
        lyricsWriter = response.xpath("//div[contains(@class, 'entry-content')]//div[contains(@class, 'su-column su-column-size-2-6')]//span[contains(@class, 'lyrics')]/a/text()").extract()
        if len(lyricsWriter) == 0:
            item['lyrics_writer'] = []
        else:
            lyricsWriter = array_translation(lyricsWriter)
            item['lyrics_writer'] = lyricsWriter

        

        # shares
        try:
            shares = response.xpath("//div[contains(@class, 'entry-content')]//div[contains(@class, 'nc_tweetContainer swp_share_button total_shares total_sharesalt')]/span[contains(@class, 'swp_count')]/text()").extract()[0]
            shares = int(re.sub('[^0-9,]', "", shares).replace(',', ''))
            item['shares'] = shares
        except:
            item['shares'] = None

        # music director
        musicBy = response.xpath("//div[contains(@class, 'entry-content')]//div[contains(@class, 'su-column su-column-size-2-6')]//span[contains(@class, 'music')]/a/text()").extract()
        if len(musicBy) == 0:
            item['music_by'] = []
        else:
            musicBy = array_translation(musicBy)
            item['music_by'] = musicBy

        # views
        try:
            views = response.xpath("//div[contains(@class, 'entry-content')]/div[contains(@class, 'tptn_counter')]/text()").extract()[0]
            views = int(re.sub('[^0-9,]', "", views).replace(',', ''))
            item['views'] = views
        except:
            item['views'] = None

      

        # lyrics
        songlyrics = response.xpath("//div[contains(@class, 'entry-content')]//pre/text()").extract()
        temp_lyric = ''
        lyrics_line = False

        for line in songlyrics:
            line_content = (re.sub("[\da-zA-Z\-—\[\]\t\@\_\!\#\+\$\%\^\&\*\(\)\<\>\?\|\}\{\~\:\∆\/]", "", line)).split('\n')
            
            for l_line in line_content:
                if l_line == '' or l_line.isspace():
                    if not lyrics_line:
                        lyrics_line = True
                        temp_lyric += '\n'
                else:            
                    lyrics_line = False
                    temp_lyric += l_line.strip()
            
            

        item['lyrics'] = temp_lyric

        pickle.dump(translated_dict, open('../translated_dict.pickle', 'wb'))

        yield item
