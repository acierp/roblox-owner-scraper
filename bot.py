import httpx
import threading
import ctypes
import time
import datetime
import json
import dateutil.parser as dp
good = 0

itemdetails = httpx.get("https://www.rolimons.com/itemapi/itemdetails", timeout=30)

with open('config.json', 'r+', encoding='utf-8') as cfgfile:
    try:
        config = json.load(cfgfile)
    except:
        print(f'{datetime.datetime.now().time()}: Your config file is in invalid format. Please troubleshoot it using jsonformatter.curiousconcept.com')

itemstoscrape = config['items to scrape']
staticscraped = config['items to scrape']

cookies = {
	".ROBLOSECURITY": config['scraping cookie']
}
def isActive(user):
	try:
		userlastonline = httpx.get(f'https://api.roblox.com/users/{user}/onlinestatus/', timeout=30)
		lastonline = userlastonline.json()['LastOnline']
		parsed_time = dp.parse(lastonline)
		time_in_seconds = parsed_time.timestamp()
		final_time = time.time()-time_in_seconds

		if final_time/int(config['maximum seconds offline']) <= 1:
			return True, final_time
		else:
			return False, final_time
	except Exception as e:
		#print(f'Ignoring exception in isActive {e}')
		return isActive(user)

def canTrade(user):
	try:
		check = httpx.get(f'https://www.roblox.com/users/profile/profileheader-json?userid={user}', timeout=30, cookies=cookies)
		if check.json()['CanTrade'] == True:
			return True, check.json()['ProfileUserName']
		else:
			return False, 'no'
	except Exception as e:
		#print(f'Ignoring exception in canTrade {e}')
		return canTrade(user)

def getName(item):
        global itemdetails
        return itemdetails.json()['items'][str(item)][0]

def getOwners(item, cursor=None):
	global good
	try:
		if cursor == None:
			owners = httpx.get(f'https://inventory.roblox.com/v2/assets/{item}/owners?sortOrder=Desc&limit=100', timeout=30, cookies=cookies)
		else:
			owners = httpx.get(f'https://inventory.roblox.com/v2/assets/{item}/owners?sortOrder=Desc&limit=100&cursor={cursor}', timeout=30, cookies=cookies)
		if owners.status_code == 200:
			for user in owners.json()['data']:
				if user['owner']:
					userid = user['owner']['id']
					activebool, final = isActive(userid)
					if activebool:
						cantrade, username = canTrade(userid)
						if cantrade == True:
							good += 1
							print(f'Successfully scraped tradable user {username} ({userid}) from {getName(item)} owners. {final / 3600} hours inactive.')
							with open("out.txt", "a") as file:
								file.write(f'{userid}\n')
								file.close()
			if owners.json()['nextPageCursor']:
				return getOwners(item, owners.json()['nextPageCursor'])
			else:
				return
		elif owners.status_code == 429:
			time.sleep(5)
			return getOwners(item, cursor)
		else:
			print(owners.text)
	except Exception as e:
		#print(f'Ignoring exception in getOwners {e}')
		return getOwners(item, cursor)


def thread(task):
	if task == 'scrape':
		while itemstoscrape:
			currentitem = itemstoscrape.pop()
			getOwners(currentitem)

threads = ['ticker']
for _ in range(config['threads']):
	threads.append('scrape')

for threadc in threads:
	threading.Thread(target=thread, args=[threadc]).start()


