import re
import json

from botocore.vendored import requests
import boto3

with open('config.json', 'r') as f:
    config = json.load(f)

S3bucket=config['CONFIG']['S3BUCKET']
number_hashtags = config['VARIABLES']['NB_HASHTAGS']

# Connect to S3
s3 = boto3.resource('s3')

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

def lambda_handler(event, context):
  list_url_photos = []
  list_url_photos = [event['queryStringParameters']['url']]
  #loop all the urls
  list_name_photos = []
  for i in range(len(list_url_photos)):
      url = list_url_photos[i]
      s3_image_filename = re.findall(r'[0-9A-Za-z]+(\.jpg|\.png|\.jpeg|\.JPG|\.JPEG|\.PNG)', url)[0] #extract the name of the image from the url
      list_name_photos.append(s3_image_filename)

      # Given an Internet-accessible URL, download the image and upload it to S3,
      # without needing to persist the image to disk locally
      req_for_image = requests.get(url, stream=True)
      file_object_from_req = req_for_image.raw
      req_data = file_object_from_req.read()

      # Do the actual upload to s3
      s3.Bucket(S3bucket).put_object(Key=s3_image_filename, Body=req_data)

  ### AI Rekogniton ###
  client=boto3.client('rekognition')

  label_account = []

  for i in range(len(list_name_photos)):
      labels_photo = {}
      photo = list_name_photos[i]
      response = client.detect_labels(Image={'S3Object':{'Bucket':S3bucket,'Name':photo}},
          MaxLabels=10, MinConfidence=80)

      for label in response['Labels']:

          labels_photo[label['Name']] = label['Confidence']
          label_account.append(label['Name'])

      all_hashtag = {}

      # search for hashtag on Instagram
      for label, confidence in labels_photo.items():

          all_hashtag[label] = {}

          for hashtag, absRelevance in getHashtag(label).items():
              score_number = confidence * absRelevance
              all_hashtag[label][hashtag] = {'score' : score_number}

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
      instagram_hastags = []
      k = 0
      for hashtag, score in sorted_hashtag:
          if k >= number_hashtags:
            break
          else:
            new_hastag = '#' + hashtag
            instagram_hastags.append(new_hastag)
            k += 1

  # delete all S3 files in the bucket
  s3.Bucket(S3bucket).objects.all().delete()

  return {
        "statusCode": 200,
        "body": json.dumps(instagram_hastags)
    }