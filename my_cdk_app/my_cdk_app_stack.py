import os 
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_lambda_event_sources as event_sources,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    aws_ec2 as ec2,
    RemovalPolicy
)
from constructs import Construct

class MyCdkAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        this_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Lambda function path: {this_dir}")

        # VPC for enhanced security
        vpc = ec2.Vpc(self, "LambdaVpc",
            cidr="10.50.0.0/16",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
            restrict_default_security_group=False 
        )

        # S3 Bucket
        bucket = s3.Bucket(
            self, "JsonAnalyzerBucket",
            bucket_name='ridwangomezybucket',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        

        # SNS Topic
        topic = sns.Topic(self, "JsonAnalyzerTopic")
        topic.add_subscription(
            subscriptions.EmailSubscription("ridwangomez98@gmail.com")
        )

        # Lambda Function
        lambda_function = lambda_.Function(
            self, "JsonAnalyzerFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="lambda_function.handler",
            code=lambda_.Code.from_asset(this_dir),
            vpc=vpc,
            environment={
                "TOPIC_ARN": topic.topic_arn
            }
        )

        # Grant permissions
        bucket.grant_read(lambda_function)
        bucket.grant_write(lambda_function)
        topic.grant_publish(lambda_function)

        # Deny access to all except your admin user and the Lambda function
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                actions=["s3:*"],
                resources=[f"{bucket.bucket_arn}/*"],
                principals=[iam.AnyPrincipal()],
                conditions={
                    "StringNotEquals": {
                        "aws:PrincipalArn": [
                            "arn:aws:iam::236823122578:user/Theadmin",  # Replace with your actual account ID
                            lambda_function.role.role_arn
                        ]
                    }
                }
            )
        )

        # S3 Event to trigger Lambda
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(lambda_function),
            s3.NotificationKeyFilter(prefix="data/", suffix=".json")
        )

        # VPC Endpoints for private AWS service access
        s3_endpoint = ec2.GatewayVpcEndpoint(
            self, "S3Endpoint",
            vpc=vpc,
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

    

                # SNS VPC Endpoint Security Group
        sns_endpoint_sg = ec2.SecurityGroup(
            self, "SNSEndpointSGRestricted",
            vpc=vpc,
            description="Restrict traffic for SNS VPC endpoint",
            allow_all_outbound=False  # 🚫 Disable all outbound by default
        )

        # ✅ Ingress: Allow Lambda to initiate traffic to endpoint (port 443)
        sns_endpoint_sg.add_ingress_rule(
            peer=lambda_function.connections.security_groups[0],
            connection=ec2.Port.tcp(443),
            description="Allow Lambda to connect to SNS endpoint"
        )

        # ✅ Egress: Allow SNS endpoint to return traffic to Lambda over HTTPS
        sns_endpoint_sg.add_egress_rule(
            peer=ec2.Peer.ipv4("10.50.0.0/16"),  # Your VPC CIDR block
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS response to Lambda in VPC"
        )

        # SNS VPC Endpoint with restricted SG
        sns_endpoint = ec2.InterfaceVpcEndpoint(
            self, "SNSEndpoint",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SNS,
            private_dns_enabled=True,
            security_groups=[sns_endpoint_sg]
        )