region        = "us-east-2"
access_key    = "AKIARAU2UJCVNU2TQPVU"
secret_key    = "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"
instance_type = "t2.small"
ami           = "ami-024e6efaf93d85776"
vpc_cidr      = "10.0.0.0/16"
public_subnet_cidrs = [
  { cidr = "10.0.1.0/24", az = "us-east-2a" },
  { cidr = "10.0.2.0/24", az = "us-east-2b" }
]
