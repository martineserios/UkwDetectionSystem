variable "client" {
  description = "Client name"
  type        = string
  default = "aiftp"
}

variable "project" {
  description = "Project name"
  type        = string
  default = "wildfire"
}

variable "region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Availability zone for the subnet"
  type        = string
  default     = "us-east-1a"
}

variable "env" {
  description = "Project environment"
  type        = string
  default = "dev"
}

# variable "sagemaker_model_data_url" {
#   description = "S3 URL for the SageMaker model data"
#   type        = string
# }

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}


variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "inference_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "ml.c6i.xlarge"
}

variable "sagemaker_model_image_ecr_uri" {
  description = "URI of the ECR repository"
  type        = string
  default     = "654654140928.dkr.ecr.us-east-1.amazonaws.com/yolov5-wildifire-model:latest"

}

variable "inference_model_s3_uri" {
  description = "Model file S3 URI"
  type        = string
  default     = "s3://ukw-wildfire-projects/wildfire-detector/model/latest/inference_model.tar.gz"
}

variable "twilio_layer_arn" {
  description = "twilio lambda layer arn"
  type        = string
  default     = "arn:aws:lambda:us-east-1:654654140928:layer:twilio:3"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0c7217cdde317cfec" # Amazon Linux 2 AMI ID
}