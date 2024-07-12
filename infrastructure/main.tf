provider "aws" {
  region = var.region
}

locals {
  prefix = "${var.client}-${var.project}"
  prefix_env = "${var.client}-${var.project}-${var.env}"
}

resource "aws_iam_user" "user" {
  name = "${local.prefix_env}"
}

resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_attach" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_user_policy_attachment" "user_attach" {
  user       = aws_iam_user.user.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_user_policy_attachment" "user_attach_sagemaker" {
  user       = aws_iam_user.user.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role" "role" {
  name = "${local.prefix_env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

# Networking Resources
resource "aws_vpc" "vpc" {
  cidr_block = var.vpc_cidr
  tags = {
    Name = "${local.prefix_env}-vpc"
  }
}

resource "aws_subnet" "subnet" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true
  tags = local.tags
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = local.tags
}

resource "aws_route_table" "rt" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = local.tags
}

resource "aws_route_table_association" "rta" {
  subnet_id      = aws_subnet.subnet.id
  route_table_id = aws_route_table.rt.id
}

resource "aws_security_group" "sg" {
  name = "${local.prefix_env}-sg"
  vpc_id = aws_vpc.vpc.id
  depends_on = [ aws_vpc.vpc ]

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

# EC2 Instance
resource "aws_instance" "ec2" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.subnet.id
  security_groups        = [aws_security_group.sg.id]
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              yum update -ya
              amazon-linux-extras install docker -y
              service docker start
              usermod -a -G docker ec2-user
              chkconfig docker on

              # Install git
              yum install -y git

              # Clone the repository
              git clone https://github.com/your-repo/your-project.git /home/ec2-user/your-project

              # Build Docker image
              cd /home/ec2-user/your-project
              docker build -t your-image-name .

              # Run Docker container
              docker run -d -p 80:80 your-image-name
              EOF

  tags = local.tags

}

# S3 Buckets
resource "aws_s3_bucket" "s3_bucket_sampling" {
  bucket = "${local.prefix_env}-sampling"
  tags = local.tags
}

resource "aws_s3_bucket" "s3_bucket_inference_positive" {
  bucket = "${local.prefix_env}-inference-positive"
  tags = local.tags
}

resource "aws_s3_bucket" "s3_bucket_main" {
  bucket = "${local.prefix_env}-main"
  tags = local.tags
}

resource "local_file" "lambda_python_code" {
  content  = file("../system_files/inference/lambda_function/lambda_function.py")
  filename = "../system_files/inference/lambda_function/package/lambda_function.py"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "../system_files/inference/lambda_function/lambda_function.zip"
  source_dir = "../system_files/inference/lambda_function/package"
  depends_on=[local_file.lambda_python_code]
}

# Upload an object
resource "aws_s3_object" "s3_bucket_main" {
  bucket = aws_s3_bucket.s3_bucket_main.id
  key    = "lambda_function.zip"
  acl    = "private"  # or can be "public-read"
  # source = "${data.archive_file.lambda_zip.output_path}"
  source = data.archive_file.lambda_zip.output_path
  server_side_encryption = "AES256"
}

# DynamoDB Table
resource "aws_dynamodb_table" "table" {
  name           = "${local.prefix_env}-inference-positive"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "image_id"

  # https://stackoverflow.com/questions/55012816/why-is-the-l-dynamodb-attribute-type-not-included-in-terraforms-aws-dynamodb-at
  attribute {
    name = "image_id"
    type = "S"
  }

  tags = local.tags
}

# SageMaker Model
resource "aws_sagemaker_model" "model" {
  name                   = "${local.prefix_env}"
  execution_role_arn     = aws_iam_role.role.arn  
  depends_on = [ aws_iam_role.role ]
  primary_container {
    image          = var.sagemaker_model_image_ecr_uri
    model_data_url = var.inference_model_s3_uri 
  }
  tags = local.tags
}

# SageMaker Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "endpoint_config" {
  name = "${local.prefix_env}"

  production_variants {
    variant_name          = "AllTraffic"
    model_name            = aws_sagemaker_model.model.name
    initial_instance_count = 1
    instance_type         = var.inference_instance_type
  }

  tags = local.tags
}

# SageMaker Endpoint
resource "aws_sagemaker_endpoint" "endpoint" {
  name = "${local.prefix_env}"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.endpoint_config.name
  tags = local.tags
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "${local.prefix_env}_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "${local.prefix_env}-lambda-s3-policy"
  description = "Policy to allow Lambda functions to access S3, DynamoDB, and SageMaker"

  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "sagemaker:*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = [
          "arn:aws:s3:::${local.prefix_env}-main",
          "arn:aws:s3:::${local.prefix_env}-main/*",
          "arn:aws:s3:::${local.prefix_env}-sampling",
          "arn:aws:s3:::${local.prefix_env}-sampling/*",
          "arn:aws:s3:::${local.prefix_env}-inference-positive",
          "arn:aws:s3:::${local.prefix_env}-inference-positive/*",
          "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.current.account_id}:table/${aws_dynamodb_table.table.name}",
          "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:*",
          "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${aws_lambda_function.lambda_inference.function_name}",
          "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${aws_lambda_function.lambda_inference.function_name}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_exec_role_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

# Lambda Function
resource "aws_lambda_function" "lambda_inference" {
  function_name   = "${local.prefix_env}-inference"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_exec_role.arn
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  layers = [ var.twilio_layer_arn ]

  tags = local.tags
}


data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_inference.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.s3_bucket_sampling.arn
}


# Adding S3 bucket as trigger to my lambda and giving the permissions
resource "aws_s3_bucket_notification" "aws-lambda-trigger" {
  bucket = aws_s3_bucket.s3_bucket_sampling.id
  # eventbridge = true
  # depends_on = [ aws_s3_bucket.s3_bucket_sampling, aws_lambda_function.lambda_inference  ]

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_inference.arn
    events              = [
      "s3:ObjectCreated:*"
      ]
  }

  depends_on = [aws_lambda_permission.allow_bucket]

}

data "aws_caller_identity" "current" {}