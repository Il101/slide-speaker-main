#!/usr/bin/env python3
"""
Initialize MinIO bucket for Slide Speaker
Creates the required bucket and sets up basic policies
"""

import boto3
import time
import sys
from botocore.exceptions import ClientError, NoCredentialsError

def wait_for_minio(max_retries=30, delay=2):
    """Wait for MinIO to be ready"""
    print("Waiting for MinIO to be ready...")
    
    for attempt in range(max_retries):
        try:
            client = boto3.client(
                's3',
                endpoint_url='http://localhost:9000',
                aws_access_key_id='minioadmin',
                aws_secret_access_key='minioadmin',
                region_name='us-east-1'
            )
            
            # Try to list buckets
            client.list_buckets()
            print("✅ MinIO is ready!")
            return client
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_retries}: {e}")
                time.sleep(delay)
            else:
                print(f"❌ MinIO not ready after {max_retries} attempts")
                return None

def create_bucket(client, bucket_name):
    """Create bucket if it doesn't exist"""
    try:
        # Check if bucket exists
        try:
            client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                pass
            else:
                raise
        
        # Create bucket
        client.create_bucket(Bucket=bucket_name)
        print(f"✅ Created bucket '{bucket_name}'")
        
        # Set bucket policy for public read access (optional)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        try:
            client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
            print(f"✅ Set public read policy for bucket '{bucket_name}'")
        except Exception as e:
            print(f"⚠️  Could not set bucket policy: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return False

def test_bucket(client, bucket_name):
    """Test bucket functionality"""
    try:
        # Test upload
        test_key = "test/test.txt"
        test_content = "Hello, Slide Speaker!"
        
        client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"✅ Test upload successful: {test_key}")
        
        # Test download
        response = client.get_object(Bucket=bucket_name, Key=test_key)
        content = response['Body'].read().decode('utf-8')
        assert content == test_content
        print(f"✅ Test download successful: {content}")
        
        # Test presigned URL
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print(f"✅ Generated presigned URL: {url[:50]}...")
        
        # Clean up test file
        client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing bucket: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing MinIO for Slide Speaker...")
    
    # Wait for MinIO
    client = wait_for_minio()
    if not client:
        print("❌ Failed to connect to MinIO")
        sys.exit(1)
    
    # Create bucket
    bucket_name = "slide-speaker"
    if not create_bucket(client, bucket_name):
        print("❌ Failed to create bucket")
        sys.exit(1)
    
    # Test bucket
    if not test_bucket(client, bucket_name):
        print("❌ Bucket test failed")
        sys.exit(1)
    
    print("\n🎉 MinIO initialization completed successfully!")
    print(f"📦 Bucket: {bucket_name}")
    print("🌐 MinIO Console: http://localhost:9001")
    print("🔑 Credentials: minioadmin / minioadmin")
    print("\n✅ Ready for Slide Speaker export!")

if __name__ == "__main__":
    import json
    main()