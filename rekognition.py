import boto3
import sys
import requests
import re

# pass url imput into variable
url = sys.argv[1]
bucket_to_use='NameOfYourBucket'

# import the image to S3
# Uses the creds in ~/.aws/credentials
s3 = boto3.resource('s3')
bucket_name_to_upload_image_to = bucket_to_use
s3_image_filename = re.findall(r'[^.\/]+\.jpg|\.png', url)[0] #extract the name of the image from the url
internet_image_url = url

# Do this as a quick and easy check to make sure your S3 access is OK
for bucket in s3.buckets.all():
    if bucket.name == bucket_name_to_upload_image_to:
        print('Good to go. Found the bucket to upload the image into.')
        good_to_go = True

if not good_to_go:
    print('Not seeing your s3 bucket, might want to double check permissions in IAM')

# Given an Internet-accessible URL, download the image and upload it to S3,
# without needing to persist the image to disk locally
req_for_image = requests.get(internet_image_url, stream=True)
file_object_from_req = req_for_image.raw
req_data = file_object_from_req.read()

# Do the actual upload to s3
s3.Bucket(bucket_name_to_upload_image_to).put_object(Key=s3_image_filename, Body=req_data)

if __name__ == "__main__":

    bucket=bucket_to_use
    photo=s3_image_filename
    
    client=boto3.client('rekognition')


    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)

    print('Detected labels for ' + photo) 
    print()   
    for label in response['Labels']:
        print ("Label: " + label['Name'])
        print ("Confidence: " + str(label['Confidence']))
        print ("Instances:")
        for instance in label['Instances']:
            print ("  Bounding box")
            print ("    Top: " + str(instance['BoundingBox']['Top']))
            print ("    Left: " + str(instance['BoundingBox']['Left']))
            print ("    Width: " +  str(instance['BoundingBox']['Width']))
            print ("    Height: " +  str(instance['BoundingBox']['Height']))
            print ("  Confidence: " + str(instance['Confidence']))
            print()

        print ("Parents:")
        for parent in label['Parents']:
            print ("   " + parent['Name'])
        print ("----------")
        print ()
