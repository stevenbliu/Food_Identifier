import boto3
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import time
import datetime
from .models import Photo

@csrf_exempt  # If you want to skip CSRF validation for the API endpoint
def generate_presigned_url(request):
    if request.method == 'POST':
        try: 
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            filename = data.get('filename')
            file_size = data.get('file_size')
            md5Checksum = data.get('md5Checksum')
            print(md5Checksum)
            if not filename or not file_size:
                return JsonResponse({'error': 'Missing filename or file_size in the request body'}, status=400)

            # Initialize the S3 client
            s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
            print(md5Checksum)

            # Generate a pre-signed URL
            response = s3_client.generate_presigned_url('put_object',
                                                        Params={
                                                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': filename,
                                                            'ContentType': 'image/png',  # Adjust as necessary
                                                            'ContentLength': file_size,
                                                            # 'Content-MD5': md5Checksum
                                                        },
                                                        ExpiresIn=3600)  # URL expires in 1 hour
            
            # Save data to the database
            image_metadata = Photo.objects.create(
                filename = filename,  # Filename as saved in S3
                file_size = 10,  # File size in bytes
                # s3_url = response.data.url,  # The S3 URL to access the photo
                # upload_time = datetime.datetime.now().time(),  # Time when the photo metadata is saved
                checksum = 111  # Optional field to store checksum (e.g., MD5) 

            )

            return JsonResponse({'url': response})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)
    

def store_image_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_key = data.get('imageKey')
            title = data.get('title')
            description = data.get('description')

            if not image_key or not title:
                return JsonResponse({'error': 'Missing image key or title'}, status=400)

            # Save data to the database
            image_metadata = Photo.objects.create(
                image_key=image_key,
                title=title,
                description=description
            )

            return JsonResponse({'success': True, 'id': image_metadata.id})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)
    

from django.http import JsonResponse
from .sns_service import send_sns_notification

def upload_notification(request):
    print(12321)
    try:
        # Trigger SNS notification (e.g., on file upload)
        send_sns_notification('File uploaded successfully.')
        return JsonResponse({'message': 'Notification sent successfully'})
    except Exception as e:
        return JsonResponse({'message': 'Failed to send notification', 'error': str(e)}, status=500)
    
from .sns_service import subscribe_to_sns

def subscribe_view(request):
    topic_arn = "arn:aws:sns:us-east-1:509399626395:photoUploadAlert"  # Replace with your SNS topic ARN
    url_forward = 'https://055f-76-126-145-131.ngrok-free.app'
    endpoint = f"{url_forward}/photo-handler/sns_endpoint/"  # Replace with your endpoint URL

    response = subscribe_to_sns(topic_arn, endpoint)
    print(response)
    if response:
        return JsonResponse({"message": "Successfully subscribed!"})
    else:
        return JsonResponse({"message": "Subscription failed!"})

from django.http import HttpResponse
import json

def sns_endpoint(request):
    print(request.method)
    if request.method == 'POST':
        body = json.loads(request.body)
        # Validate the SNS message here (check signature, etc.)
        
        # Handle your SNS message (e.g., trigger logic based on the notification)
        print(f"Received SNS message: {body}")

        # Return a success response
        return HttpResponse(status=200)
    return HttpResponse(status=400)
