import boto3
import sys
import requests
import re
import json
import shutil
from subprocess import call
import time
import instagram_scraper as insta

S3bucket='bucket'

insta_profiles = ["profile"]
number_last_photos = 1 # put 0 to select all
number_hashtags = 5

#scrape meta data from n last media from insta profiles
def scraper():
 #  call('instagram-scraper ' + insta_profiles + ' -m ' + number_last_photos + ' -u 0 -p 0 -t none --media-metadata', shell=True)
    imgScraper = insta.InstagramScraper(usernames=[insta_profiles[x]],maximum=number_last_photos,media_metadata=True,
                                        latest=True,media_types=['none'])
    imgScraper.scrape()

    print ("scraped " + str(number_last_photos) + " from " + insta_profiles[x])
def main():
    scraper()

for x in range(len(insta_profiles)):
    main()
    #time.sleep(1)

#need to implement loop for all profiles
path_to_json = insta_profiles[0] + '/' + insta_profiles[0] + '.json'
list_url_photos = []

# read json file and create a list with the urls
with open(path_to_json) as json_file:  
    data = json.load(json_file)
    for i in range(len(data)):
        list_url_photos.append(data[i]['display_url'])

# comment the line below to choose image from instagram profile
#list_url_photos = ["https://upload.wikimedia.org/wikipedia/commons/3/32/House_sparrow04.jpg"]

# import the image to S3
# Uses the creds in ~/.aws/credentials
s3 = boto3.resource('s3')

# Do this as a quick and easy check to make sure your S3 access is OK
for bucket in s3.buckets.all():
    if bucket.name == S3bucket:
        print('Good to go. Found the bucket to upload the image into.')
        print()
        good_to_go = True

if not good_to_go:
    print('Not seeing your s3 bucket, might want to double check permissions in IAM')

# loop all the urls
list_name_photos = []

for i in range(len(list_url_photos)):
    url = list_url_photos[i]
    s3_image_filename = re.findall(r'[^.\/]+\.jpg|\.png', url)[0] #extract the name of the image from the url
    list_name_photos.append(s3_image_filename)

    # Given an Internet-accessible URL, download the image and upload it to S3,
    # without needing to persist the image to disk locally
    req_for_image = requests.get(url, stream=True)
    file_object_from_req = req_for_image.raw
    req_data = file_object_from_req.read()

    # Do the actual upload to s3
    s3.Bucket(S3bucket).put_object(Key=s3_image_filename, Body=req_data)

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

#AI Rekogniton
if __name__ == "__main__":
    
    client=boto3.client('rekognition')

    label_account = []

    for i in range(len(list_name_photos)):
        labels_photo = {}
        photo = list_name_photos[i]
        response = client.detect_labels(Image={'S3Object':{'Bucket':S3bucket,'Name':photo}},
            MaxLabels=10, MinConfidence=60)
    
        print ("----------")
        print ()
        print ('Detected labels for ' + photo) 
        print ()

        for label in response['Labels']:

            labels_photo[label['Name']] = label['Confidence']
            label_account.append(label['Name'])

        all_hashtag = {}

        # search for hashtag on Instagram
        for label, confidence in labels_photo.items():
            #print("Hashtags seach for ", label, "confidence of", confidence)
            #print ("----------")
            #print ()

            all_hashtag[label] = {}

            for hashtag, absRelevance in getHashtag(label).items():
                score_number = confidence * absRelevance
                all_hashtag[label][hashtag] = {'score' : score_number}
                #print(hashtag, 'has a score of', absRelevance)
            #print()

        # loop in all hashtag found and keep the highest score
        hashtag_selected = {}
        for label, hashtags in all_hashtag.items():
            for hashtag, details_hashtag in hashtags.items():
                # if the score is higher don't replace
                if hashtag in hashtag_selected:
                    if hashtag_selected[hashtag] < details_hashtag['score'] :
                        hashtag_selected[hashtag] = details_hashtag['score']
                else:
                    hashtag_selected[hashtag] = details_hashtag['score']

        #sort hashtag by value
        sorted_hashtag = sorted(hashtag_selected.items(), key=lambda kv: kv[1], reverse=True)

        #loop the number of hashtag wanted
        k = 0
        for hashtag, score in sorted_hashtag:
            if k >= number_hashtags:
                break
            else:
                print('#' + hashtag)
                k += 1


    print ("----------")
    print ()
    ##need to implement loop for all profiles
    # print summary of label found
    #print ('Summary labels for the acccount ' + insta_profiles[0]) 
    #print ()
    #remove duplicate
    #label_account_order = list(dict.fromkeys(label_account))
    # print the total of the labels found in a alphabetical order
    #print (sorted(label_account_order))

#delete the folder with json
for i in range(len(insta_profiles)):
    shutil.rmtree(insta_profiles[i])
    print(insta_profiles[i] + " folder deleted")
# delete all S3 files in the bucket
s3.Bucket(S3bucket).objects.all().delete()
print("All S3 objects deleted")