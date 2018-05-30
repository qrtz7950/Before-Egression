import datetime
import pytz
import urllib.request
import json

#oled lib

import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess

#ultrasonic lib

#import time
import RPi.GPIO as GPIO

#----------------------------------------------------------------------
# <initialize>

# oled initialize

RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

disp.begin()

disp.clear()
disp.display()

width = disp.width
height = disp.height
image1 = Image.new('1', (width, height))

draw = ImageDraw.Draw(image1)

draw.rectangle((0,0,width,height), outline=0, fill=0)

padding = -2
top = padding
bottom = height-padding

x = 0

font = ImageFont.load_default()

# ultrasonic initialize

GPIO.setmode(GPIO.BCM)
pin_trigger = 18
pin_echo = 23

GPIO.setup(pin_trigger, GPIO.OUT) # trigger signal
GPIO.output(pin_trigger, GPIO.LOW)

GPIO.setup(pin_echo, GPIO.IN) # echo signal

time.sleep(.5)

# Declarate global variable
PTY = 0
SKY = 0
TMN = 100
TMX = 100
#----------------------------------------------------------------------

# time calculate
def get_api_date() :
    
	standard_time = [2, 5, 8, 11, 14, 17, 20, 23] 		#APT renewal time
	time_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%H')
	check_time = int(time_now) - 1
	day_calibrate = 0
	while not check_time in standard_time :
		check_time -= 1
		if check_time < 2 :
			day_calibrate = 1
			check_time = 23

	date_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')
	check_date = int(date_now) - day_calibrate

	return (str(check_date), (str(check_time) + '00'))

# get weather data
# dong = 동네예보
# cho = 초단기
def get_weather_data() :
    
        api_date, api_time= get_api_date()
        key = "Key"				 # insert your API key
        date = api_date
        time = api_time
        time_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%H')
        time_now = int(time_now) - 1
        nx = "60"
        ny = "127"

        api_url_dong = "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastSpaceData?serviceKey=" + key + "&base_date=" + date + "&base_time=" + time + "&nx=" + nx + "&ny=" + ny + "&numOfRows=82&_type=json"
        api_url_cho = "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastGrib?serviceKey=" + key + "&base_date=" + date + "&base_time=" + str(time_now) + "00" + "&nx=" + nx + "&ny=" + ny + "&numOfRows=10&_type=json"
        
        data_dong = urllib.request.urlopen(api_url_dong).read().decode('utf8')
        data_json_dong = json.loads(data_dong)
	
        data_cho = urllib.request.urlopen(api_url_cho).read().decode('utf8')
        data_json_cho = json.loads(data_cho)
	
        parsed_json_dong = data_json_dong['response']['body']['items']['item']
        parsed_json_cho = data_json_cho['response']['body']['items']['item']
        
        target_date = parsed_json_dong[0]['fcstDate']  # get date and time
        target_time = parsed_json_dong[0]['fcstTime']

        date_calibrate = target_date #date of TMX, TMN
        if target_time > 1300:
            date_calibrate = str(int(target_date) + 1)
        
        weather_info_dong = {}
        for one_parsed in parsed_json_dong:
            if one_parsed['fcstDate'] == target_date and one_parsed['fcstTime'] == target_time: #get today's data
                weather_info_dong[one_parsed['category']] = one_parsed['fcstValue']
        
        i = 0
        while i<82 :
            if parsed_json_dong[i]['category'] == 'TMX' :
                global TMX
                TMX = str(int(parsed_json_dong[i]['fcstValue']))
            elif parsed_json_dong[i]['category'] == 'TMN' :
                global TMN
                TMN = str(int(parsed_json_dong[i]['fcstValue']))
            i = i + 1

        weather_info_cho = {}
        for one_parsed in parsed_json_cho:
            weather_info_cho[one_parsed['category']] = one_parsed['obsrValue']
                
        return weather_info_dong, weather_info_cho

# process dong data
def process_dong(dictionary) :
    global PTY
    global SKY
    global image
    
    POP = str(dictionary['POP']) + "%" #precipation persentage
    PTY = str(dictionary['PTY']) #precipation status
    SKY = str(dictionary['SKY']) #sky status
    
    if PTY == "0" :
        PTY = "none "
    elif PTY == "1" :
        PTY = "rain "
    elif PTY == "2" :
        PTY = "sleet"
    elif PTY == "3" :
        PTY = "snow "
    
    if SKY == "1" :
        SKY = "sunny "
    elif SKY == "2" :
        SKY = "little"
    elif SKY == "3" :
        SKY = "many  "
    elif SKY == "4" :
        SKY = "cloudy"
        
    return POP,PTY,SKY
   
# process cho data
def process_cho(dictionary) :
    
    REH = str(dictionary['REH']) + "%" #humidity
    T1H = str(dictionary['T1H']) + "°C" #temperature
    
    return REH,T1H

# print(get_weather_data())  # get weather_info test

# print on display
def display_weather() :
    
    dong = {}
    cho = {}
    dong, cho = get_weather_data()
    POP, PTY, SKY = process_dong(dong)
    REH , T1H = process_cho(cho)
    global TMX
    global TMN
    TMX = TMX + "°C"
    TMN = TMN + "°C"

    # print(POP, PTY, SKY)   # display_weather test
    # print(REH, T1H)
    i = 0
    while i < 2 :
        disp.clear()
        disp.display()
        
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((x, top),       "SKY: " + SKY + "    H:" + TMX,  font=font, fill=255)
        draw.text((x, top+8),     "Status: " + PTY + "  L:" + TMN, font=font, fill=255)
        draw.text((x, top+16),    "Huminity: " + REH,  font=font, fill=255)
        draw.text((x, top+25),    "Tempertature: " + T1H,  font=font, fill=255)

        disp.image(image1)
        disp.display()
        time.sleep(5)
        
        display_image()
        
        i = i + 1
    
    disp.clear()
    disp.display()
    time.sleep(0.1)
    
# ultrasonic
def ultrasonic() :
    
    GPIO.output(pin_trigger, GPIO.HIGH) # shoot the signal for 10 us
    time.sleep(.00001) # 10 us
    GPIO.output(pin_trigger, GPIO.LOW)

    # waiting for the return signal
    while GPIO.input(pin_echo) == GPIO.LOW :
        pass
    start = time.time()

    # receiving signal
    while GPIO.input(pin_echo) == GPIO.HIGH :
       pass
    stop = time.time()

    d = (stop - start) * 170 * 100 # cm, speed of sound 340 m/s in air,  d = 340/2
    print(format(d, ".2f") + " cm")

    time.sleep(.1)
    return d

# measuring init d2(distance)
def d2Init() :
    
    d2_list = []
    display_booting_text(0)
    i = 0
    while i<30 :
        ultrasonic()
        i = i + 1
        
    display_booting_text(1)
    k = 0
    while k<10 :
        k = 15
        d2 = 0
        d3 = 0
        i = 0
        j = 0
        while i < k :
            d2_temp = [ultrasonic()]
            d2_list.extend(d2_temp)
            i = i + 1
         
        i = 0
        while i < k :
            d2 = d2 + d2_list[i]
            
            i = i + 1

        d2 = d2/k
        
        i = 0
        while i < k :
            if d2_list[i] < 1.2 * d2 and d2_list[i] > 0.8 * d2 :
                d3 = d3 + d2_list[i]
            else :
                j = j + 1
                
            i = i + 1
        
        k = k - j
        
        if k!=0 :
            d3 = d3/k
        
        if k<10 :
            print("booting fail")
        
        del d2_list[0:k+j]
    
    return int(d3)

# display sky status's image
def display_image() :
    global image
    global SKY
    global PTY
    disp.clear()
    disp.display()

    if PTY == "none " :
        if SKY == "sunny " :
            image = Image.open('sunny.png').resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
        if SKY == "little" :
            image = Image.open('cloudy_little.png').resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
        if SKY == "many  " or SKY == "cloudy" :
            image = Image.open('cloudy_many.png').resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
    elif PTY == "rain " :
        image = Image.open('rainy.png').resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
    elif PTY == "sleet" :
        image = Image.open('sleet.png').resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
    elif PTY == "snow " :
        image = Image.open('snowy.png').resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
        
    disp.image(image)
    disp.display()
    time.sleep(2)
    
def display_booting_text(x) :
    
    if x == 0 :
        disp.clear()
        disp.display()
        
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((x, top),       "",  font=font, fill=255)
        draw.text((x, top+8),     "       waiting" , font=font, fill=255)
        draw.text((x, top+16),    "       booting",  font=font, fill=255)
        draw.text((x, top+25),    "",  font=font, fill=255)

        disp.image(image1)
        disp.display()
        
    elif x == 1 :
        disp.clear()
        disp.display()
        
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((x, top),       "",  font=font, fill=255)
        draw.text((x, top+8),     "       booting", font=font, fill=255)
        draw.text((x, top+16),    "       start",  font=font, fill=255)
        draw.text((x, top+25),    "",  font=font, fill=255)

        disp.image(image1)
        disp.display()
        
    elif x == 2 :
        disp.clear()
        disp.display()
        
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((x, top),       "",  font=font, fill=255)
        draw.text((x, top+8),     "       booting", font=font, fill=255)
        draw.text((x, top+16),    "       success",  font=font, fill=255)
        draw.text((x, top+25),    "",  font=font, fill=255)

        disp.image(image1)
        disp.display()
        
    time.sleep(0.1)
#----------------------------------------------------------------------
# main
d2 = d2Init()

display_booting_text(2)
time.sleep(2)
disp.clear()
disp.display()

print("initial value = " + str(d2))

while True :
    d = ultrasonic()
    if d < d2 - 50 :
        display_weather()


