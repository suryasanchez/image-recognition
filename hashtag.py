import requests

def getHashtag(keyword):
	# https://d212rkvo8t62el.cloudfront.net/tag/
	r = requests.get('https://query.displaypurposes.com/tag/' + keyword)

	hashtag_json = r.json()

	list_hashtag = {}
	# loop 10 best hashtage for the keyword
	for i in range(len(hashtag_json["results"])):
		if i < 10:
			hashtag = hashtag_json["results"][i]["tag"]
			score = hashtag_json["results"][i]["absRelevance"]
			list_hashtag[hashtag] = score
			
		else: break

	return list_hashtag

keywords = ["cat", "tree"]

for keyword in range(len(keywords)):
	print("Hashtags seach for " + keywords[keyword])
	for hashtag, absRelevance in getHashtag(keywords[keyword]).items():
		print(hashtag, 'has a score of', absRelevance)
	print()