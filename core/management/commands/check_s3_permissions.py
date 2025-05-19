import boto3
from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand
from django.conf import settings
import json

class Command(BaseCommand):
    help = 'Check S3 bucket permissions and CORS configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-acls',
            action='store_true',
            help='Check ACLs on objects in addition to bucket permissions',
        )
        parser.add_argument(
            '--fix-cors',
            action='store_true',
            help='Fix CORS configuration if issues are found',
        )

    def handle(self, *args, **options):
        # Check if S3 is enabled
        if not hasattr(settings, 'USE_S3') or not settings.USE_S3:
            self.stdout.write(self.style.ERROR('S3 storage is not enabled. Aborting check.'))
            return
        
        check_acls = options['check_acls']
        fix_cors = options['fix_cors']
        
        # Initialize boto3 clients
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        sts = boto3.client(
            'sts',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Get current AWS identity
        try:
            identity = sts.get_caller_identity()
            self.stdout.write(self.style.SUCCESS(f"Using AWS Account: {identity['Account']}"))
            self.stdout.write(self.style.SUCCESS(f"User/Role ARN: {identity['Arn']}"))
        except ClientError as e:
            self.stdout.write(self.style.ERROR(f"Error getting caller identity: {str(e)}"))
            self.stdout.write(self.style.WARNING("Check that your AWS credentials are valid."))
            return
        
        # Check bucket existence and permissions
        self.stdout.write(self.style.SUCCESS(f"\n=== Checking S3 Bucket: {settings.AWS_STORAGE_BUCKET_NAME} ==="))
        
        try:
            # Try to get bucket location (requires s3:GetBucketLocation permission)
            location = s3.get_bucket_location(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            self.stdout.write(self.style.SUCCESS(f"Bucket exists and is accessible"))
            self.stdout.write(self.style.SUCCESS(f"Bucket region: {location['LocationConstraint'] or 'us-east-1'}"))
            
            # Additional permission checks - try operations that would be needed
            try:
                # Check if we can list objects (s3:ListBucket)
                s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, MaxKeys=1)
                self.stdout.write(self.style.SUCCESS("✓ Can list objects in bucket"))
            except ClientError as e:
                self.stdout.write(self.style.ERROR(f"✗ Cannot list objects in bucket: {str(e)}"))
            
            try:
                # Check if we can get objects (s3:GetObject)
                # First list at least one object
                response = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, MaxKeys=1)
                if 'Contents' in response and len(response['Contents']) > 0:
                    test_key = response['Contents'][0]['Key']
                    # Try to generate a presigned URL
                    url = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': test_key},
                        ExpiresIn=60
                    )
                    self.stdout.write(self.style.SUCCESS(f"✓ Can generate presigned URLs for objects"))
                    self.stdout.write(f"Sample URL (expires in 60s): {url}")
                else:
                    self.stdout.write(self.style.WARNING("No objects found in bucket to test GetObject permission"))
            except ClientError as e:
                self.stdout.write(self.style.ERROR(f"✗ Error testing GetObject permission: {str(e)}"))
            
            try:
                # Check if we can put objects (s3:PutObject)
                test_key = 'test_permissions.txt'
                s3.put_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=test_key,
                    Body='test content'
                )
                self.stdout.write(self.style.SUCCESS("✓ Can put objects in bucket"))
                
                # Clean up the test object
                s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=test_key)
                self.stdout.write(self.style.SUCCESS("✓ Can delete objects in bucket"))
            except ClientError as e:
                self.stdout.write(self.style.ERROR(f"✗ Cannot put/delete objects in bucket: {str(e)}"))
            
            # Check CORS configuration
            self.stdout.write(self.style.SUCCESS("\n=== Checking CORS Configuration ==="))
            try:
                cors = s3.get_bucket_cors(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
                if 'CORSRules' in cors:
                    self.stdout.write(self.style.SUCCESS("CORS configuration found:"))
                    for rule in cors['CORSRules']:
                        self.stdout.write(json.dumps(rule, indent=2))
                    
                    # Check if CORS configuration is appropriate
                    has_all_methods = False
                    has_all_headers = False
                    
                    for rule in cors['CORSRules']:
                        if 'AllowedMethods' in rule and ('GET' in rule['AllowedMethods'] and 'PUT' in rule['AllowedMethods']):
                            has_all_methods = True
                        if 'AllowedHeaders' in rule and '*' in rule['AllowedHeaders']:
                            has_all_headers = True
                    
                    if has_all_methods and has_all_headers:
                        self.stdout.write(self.style.SUCCESS("✓ CORS configuration appears to be appropriate"))
                    else:
                        self.stdout.write(self.style.WARNING("! CORS configuration may be incomplete"))
                        
                        if fix_cors:
                            self.stdout.write(self.style.SUCCESS("Fixing CORS configuration..."))
                            recommended_cors = {
                                'CORSRules': [
                                    {
                                        'AllowedHeaders': ['*'],
                                        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                                        'AllowedOrigins': ['*'],
                                        'ExposeHeaders': ['ETag', 'Content-Length']
                                    }
                                ]
                            }
                            s3.put_bucket_cors(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                CORSConfiguration=recommended_cors
                            )
                            self.stdout.write(self.style.SUCCESS("CORS configuration updated"))
                else:
                    self.stdout.write(self.style.WARNING("No CORS rules found in the bucket"))
                    
                    if fix_cors:
                        self.stdout.write(self.style.SUCCESS("Adding recommended CORS configuration..."))
                        recommended_cors = {
                            'CORSRules': [
                                {
                                    'AllowedHeaders': ['*'],
                                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                                    'AllowedOrigins': ['*'],
                                    'ExposeHeaders': ['ETag', 'Content-Length']
                                }
                            ]
                        }
                        s3.put_bucket_cors(
                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                            CORSConfiguration=recommended_cors
                        )
                        self.stdout.write(self.style.SUCCESS("CORS configuration added"))
            except ClientError as e:
                if 'NoSuchCORSConfiguration' in str(e):
                    self.stdout.write(self.style.WARNING("No CORS configuration found on the bucket"))
                    
                    if fix_cors:
                        self.stdout.write(self.style.SUCCESS("Adding recommended CORS configuration..."))
                        recommended_cors = {
                            'CORSRules': [
                                {
                                    'AllowedHeaders': ['*'],
                                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                                    'AllowedOrigins': ['*'],
                                    'ExposeHeaders': ['ETag', 'Content-Length']
                                }
                            ]
                        }
                        try:
                            s3.put_bucket_cors(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                CORSConfiguration=recommended_cors
                            )
                            self.stdout.write(self.style.SUCCESS("CORS configuration added"))
                        except ClientError as cors_e:
                            self.stdout.write(self.style.ERROR(f"Error adding CORS configuration: {str(cors_e)}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Error checking CORS configuration: {str(e)}"))
            
            # Check bucket policy
            self.stdout.write(self.style.SUCCESS("\n=== Checking Bucket Policy ==="))
            try:
                policy = s3.get_bucket_policy(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
                if 'Policy' in policy:
                    self.stdout.write(self.style.SUCCESS("Bucket policy found:"))
                    policy_json = json.loads(policy['Policy'])
                    self.stdout.write(json.dumps(policy_json, indent=2))
                else:
                    self.stdout.write(self.style.WARNING("No bucket policy found"))
            except ClientError as e:
                if 'NoSuchBucketPolicy' in str(e):
                    self.stdout.write(self.style.WARNING("No bucket policy found"))
                else:
                    self.stdout.write(self.style.ERROR(f"Error checking bucket policy: {str(e)}"))
            
            # Check ACLs on sample objects if requested
            if check_acls:
                self.stdout.write(self.style.SUCCESS("\n=== Checking ACLs on Sample Objects ==="))
                response = s3.list_objects_v2(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Prefix='media/private/cvs/',
                    MaxKeys=5
                )
                
                if 'Contents' in response and len(response['Contents']) > 0:
                    for obj in response['Contents']:
                        self.stdout.write(f"\nChecking object: {obj['Key']}")
                        try:
                            acl = s3.get_object_acl(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=obj['Key']
                            )
                            if 'Grants' in acl:
                                self.stdout.write(f"Object ACL grants:")
                                for grant in acl['Grants']:
                                    grantee = grant.get('Grantee', {})
                                    grantee_type = grantee.get('Type', 'Unknown')
                                    grantee_id = grantee.get('ID', 'N/A')
                                    grantee_uri = grantee.get('URI', 'N/A')
                                    permission = grant.get('Permission', 'Unknown')
                                    
                                    if grantee_type == 'CanonicalUser':
                                        self.stdout.write(f"  - User {grantee_id}: {permission}")
                                    elif grantee_type == 'Group':
                                        self.stdout.write(f"  - Group {grantee_uri}: {permission}")
                                    else:
                                        self.stdout.write(f"  - {grantee_type}: {permission}")
                            else:
                                self.stdout.write("No ACL grants found for this object")
                        except ClientError as e:
                            self.stdout.write(self.style.ERROR(f"Error checking object ACL: {str(e)}"))
                else:
                    self.stdout.write(self.style.WARNING("No objects found with prefix 'media/private/cvs/'"))
            
            # Provide guidance
            self.stdout.write(self.style.SUCCESS("\n=== Recommendations ==="))
            self.stdout.write("""
If you're experiencing "Access Denied" errors when trying to view CV files:

1. Check that your bucket policy and IAM permissions allow:
   - s3:GetObject
   - s3:PutObject
   - s3:ListBucket

2. Ensure your Django settings have:
   - AWS_QUERYSTRING_AUTH = True for private files
   - custom_domain = False in PrivateMediaStorage class

3. Verify the object paths in S3 match what Django expects:
   - Should be in format: media/private/cvs/filename.pdf

4. For non-authenticated users visiting direct file URLs:
   - Direct S3 URLs won't work for private objects
   - Use a signed URL through the Django view
   
5. Test with the following command from Django shell:
   python manage.py shell
   
   Then run:
   
   from django.contrib.auth.models import User
   from core.models import UserProfile
   import boto3
   from django.conf import settings
   
   # Select a user that has a CV
   user = User.objects.filter(userprofile__cv__isnull=False).first()
   if user:
       profile = user.userprofile
       print(f"File path: {profile.cv.name}")
       
       # Generate a pre-signed URL
       s3 = boto3.client('s3', 
           region_name=settings.AWS_S3_REGION_NAME,
           aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
       
       file_key = f"media/private/{profile.cv.name}"
       url = s3.generate_presigned_url('get_object',
           Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': file_key},
           ExpiresIn=3600)
       
       print(f"Pre-signed URL: {url}")
            """)
            
        except ClientError as e:
            self.stdout.write(self.style.ERROR(f"Error checking bucket: {str(e)}"))
            self.stdout.write(self.style.WARNING("This may indicate that the bucket doesn't exist or you don't have permission to access it."))
            self.stdout.write(self.style.WARNING("Check your AWS_STORAGE_BUCKET_NAME setting and AWS credentials.")) 