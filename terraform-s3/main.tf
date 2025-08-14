provider "aws" {
  region = "us-east-1"
}

# Create S3 bucket
resource "aws_s3_bucket" "my_bucket" {
  bucket = "melhem-terraform-bucket"
  acl    = "private"
}

# Upload a file to the bucket
resource "aws_s3_bucket_object" "my_file" {
  bucket = aws_s3_bucket.my_bucket.id
  key    = "example.txt"       # The name it will have in S3
  source = "example.txt"       # Local file path
  acl    = "private"
}
