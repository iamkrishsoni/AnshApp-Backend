import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# Read AWS credentials and region from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY')  # Fix variable names
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')  # Fix variable names
AWS_REGION = os.getenv('AWS_REGION')  # Ensure this is correctly named in .env

# Initialize the SNS client with the loaded credentials
sns_client = boto3.client(
    'sns',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION  # Use the loaded region name
)

def send_sms(phone_number, otp):
    try:
        phone_number = str(phone_number).strip()
        
        # Ensure +91 prefix
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"
        
        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=f'Your Verification OTP for AnshAp is {otp}'
        )

        print(f"✅ OTP Sent Successfully: {response}")
        return response
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
        return None

def send_otp_email(email, otp):
    try:
        subject = "AnshAp OTP Verification"
        content = f"Your OTP for AnshAp verification is: {otp}. Please do not share this code with anyone."

        # Create or retrieve the topic for OTP emails
        response = sns_client.create_topic(Name="email-otp")
        topic_arn = response["TopicArn"]

        # Subscribe the email to the topic (Only needed for the first time, requires confirmation)
        sns_client.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)

        # Publish the OTP message
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=content
        )

        return response
    except Exception as e:
        print(f"❌ Failed to send OTP email: {e}")
        return None

def send_email(email, subject, content):
    """
    Send an email with the specified content.

    :param email: Recipient email address.
    :param subject: Subject of the email.
    :param content: Content/body of the email.
    """
    try:
        # Create a unique topic for email notifications (can reuse if already created)
        response = sns_client.create_topic(Name='email-notifications')
        topic_arn = response['TopicArn']

        # Subscribe the email to the topic
        sns_client.subscribe(TopicArn=topic_arn, Protocol='email', Endpoint=email)

        # Publish the message
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=content
        )
        return response
    except Exception as e:
        print(f"Failed to send email: {e}")
        return None

def send_push_notification(device_token, content):
    """
    Send a push notification to the specified device token.

    :param device_token: The device token (from Firebase/APNS, etc.).
    :param content: Content/body of the notification.
    """
    try:
        # Replace with your platform application ARN
        platform_application_arn = 'arn:aws:sns:us-east-1:123456789012:app/GCM/YourAppName'  # Update this

        # Create a platform endpoint for the device token
        response = sns_client.create_platform_endpoint(
            PlatformApplicationArn=platform_application_arn,
            Token=device_token
        )
        endpoint_arn = response['EndpointArn']

        # Publish the notification
        response = sns_client.publish(
            TargetArn=endpoint_arn,
            Message=content
        )
        return response
    except Exception as e:
        print(f"Failed to send push notification: {e}")
        return None
