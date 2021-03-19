import json 
import requests
import pandas as pd

API_KEY = 'AIzaSyAoXyoleVzyGJeGiUtFKlEEEzcDd7itaVA'
YOUTUBE_ID = ''

def getSeconds(durStr):
    nums = []
    temp = ''
    out = 0
    for it in durStr:
        #print(it)
        if not it.isdigit():
            if temp == '':
                continue
            else:
                nums.append(int(temp))
                temp = ''
        else:
            temp += it

    out += nums[-1]

    if(len(nums)>1):
        out += nums[-2]*60
    if(len(nums)>2):
        out += nums[-3]*60*60
    if(len(nums)>3):
        out += nums[-4]*24*60*60

    return out

def recognizeChannel(url):
	CH_ID = url.split('/')
	if(CH_ID[-1] in ["featured", "videos", "playlists", "community", "channels", "about"]):
		CH_ID = CH_ID[:-1]

	url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forUsername={CH_ID[-1]}&key={API_KEY}"
	response = requests.get(url)
	data = response.json()
	if(data["pageInfo"]["totalResults"] != 0):
		return data["items"][0]["id"]

	url = f"https://www.googleapis.com/youtube/v3/channels?part=id&id={CH_ID[-1]}&key={API_KEY}"
	response = requests.get(url)
	data = response.json()
	if(data["pageInfo"]["totalResults"] != 0):
		return data["items"][0]["id"]

	url = f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=25&q={CH_ID[-1]}&key={API_KEY}&type=channel"
	response = requests.get(url)
	data = response.json()

	if(data["pageInfo"]["totalResults"] != 0):
		#print(data["items"][0])
		return data["items"][0]["snippet"]["channelId"]

def getVideoInfo(vid):
	info = {}

	url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={vid}&key={API_KEY}"
	response = requests.get(url) # Perform the GET request 
	data = response.json() # Read the json response and convert it to a Python dictionary 

	try:
		info['likes'] = data['items'][0]['statistics']['likeCount']
		info['dislikes'] = data['items'][0]['statistics']['dislikeCount']
		info['views'] = data['items'][0]['statistics']['viewCount']
		info['comments'] = data['items'][0]['statistics']['commentCount']
		info['favs'] = data['items'][0]['statistics']['favoriteCount']
	except IndexError:
		return 0
	except KeyError:
		return 0
	url=f"https://www.googleapis.com/youtube/v3/videos?id={vid}&key={API_KEY}&part=contentDetails"
	response = requests.get(url)
	data = response.json()
	#print(data)
	info['duration'] = getSeconds(data['items'][0]['contentDetails']['duration'])

	url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid}&key={API_KEY}"
	response = requests.get(url) # Perform the GET request 
	data = response.json() # Read the json response and convert it to a Python dictionary 
	string = data['items'][0]['snippet']['publishedAt'].split('T')
	info['published'] = (f"{string[0]} {string[1][:-1]}")

	return info


def getVInfoList(url):
	playlists = []
	videos = []
	nextPageToken = ''
	YOUTUBE_ID = recognizeChannel(url)

	while True:
		if nextPageToken:
			nextPageToken = '&pageToken=' + nextPageToken

		url = f"https://www.googleapis.com/youtube/v3/playlists?part=snippet&channelId={YOUTUBE_ID}&key={API_KEY}&maxResults=50"+nextPageToken
		response = requests.get(url)
		data = response.json()

		pldata = (data["items"])
		for pl in pldata:
			playlists.append([pl["snippet"]["title"], pl["id"]])

		try:
			nextPageToken = data['nextPageToken']
		except KeyError:
			nextPageToken = ''
			break

	i = 1
	j = 1
	for playlist in playlists:
		while True:
			if nextPageToken:
				nextPageToken = '&pageToken=' + nextPageToken

			url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist[1]}&key={API_KEY}&maxResults=50"+nextPageToken
			response = requests.get(url)
			data = response.json()

			playlistLen = data['pageInfo']['totalResults']
			pldata = data["items"]
			for pl in pldata:
				if(pl["snippet"]["title"] == 'Private video'):
					continue
				vInfo = getVideoInfo(pl["snippet"]["resourceId"]["videoId"])
				if(vInfo == 0):
					continue
				print('[' + str(i) + '/' + str(len(playlists)) + ']['+ str(j) +'/'+ str(playlistLen) +'][' + pl["snippet"]["title"] + ']')
				videos.append([playlist[0], pl["snippet"]["title"], vInfo['published'], vInfo['views'], vInfo['likes'], vInfo['dislikes'], vInfo['favs'], vInfo['comments'], vInfo['duration']])
				#print(videos[i])
				j += 1
			
			try:
				nextPageToken = data['nextPageToken']
			except KeyError:
				nextPageToken = ''
				j = 1
				break
		i += 1
	return videos




if __name__ == '__main__':

	chUrl = input('Enter channel URL or title: ')

	vids = getVInfoList(chUrl)

	df = pd.DataFrame(vids)
	df.columns = ['playlist','title', 'date', 'views', 'likes', 'dislikes', 'favs', 'comments', 'duration']
	df.to_csv('out.csv')