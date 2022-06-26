#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import getsizeof


class AWSEvent:

    # https://docs.aws.amazon.com/whitepapers/latest/security-overview-aws-lambda/lambda-event-sources.html

    UNIDENTIFIED = 'unidentified'
    API_GATEWAY_AWS_PROXY = 'api_gateway_aws_proxy'
    API_GATEWAY_HTTP = 'api_gateway_http'
    S3 = 'S3'
    SNS = 'sns'
    DYNAMO_DB = 'dynamo_db'
    CLOUDFRONT = 'cloudfront'
    SCHEDULED_EVENT = 'scheduled_event'
    CLOUD_WATCH_LOGS = 'cloud_watch_logs'
    API_GATEWAY_AUTHORIZER = 'api_gateway_authorizer'
    AWS_CONFIG = 'aws_config'
    CLOUD_FORMATION = 'cloud_formation'
    CODE_COMMIT = 'code_commit'
    SES = 'ses'
    KINESIS = 'kinesis'
    KINESIS_FIREHORSE = 'kinesis_firehose'
    COGNITO_SYNC_TRIGGER = 'cognito_sync_trigger'
    MOBILE_BACKEND = 'is_mobile_backend'

    def __init__(self, event: dict = {}) -> None:
        self.event = event
        self.event_type = self._get_event_type()
        self.size = getsizeof(event)

    def _get_event_type(self):
        if not self.event:
            return self.UNIDENTIFIED

        if 'pathParameters' in self.event and 'proxy' in self.event['pathParameters']:
            return self.API_GATEWAY_AWS_PROXY
        if 'requestContext' in self.event and 'resourceId' in self.event['requestContext']:
            return self.API_GATEWAY_HTTP
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'eventSource' in self.event['Records'][0] and self.event['Records'][0]['eventSource'] == 'aws:s3':
            return self.S3
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'EventSource' in self.event['Records'][0] and self.event['Records'][0]['EventSource'] == 'aws:sns':
            return self.SNS
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'eventSource' in self.event['Records'][0] and self.event['Records'][0]['eventSource'] == 'aws:dynamodb':
            return self.DYNAMO_DB
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'cf' in self.event['Records'][0]:
            return self.CLOUDFRONT
        elif 'source' in self.event and self.event['source'] == 'aws.events':
            return self.SCHEDULED_EVENT
        elif 'awslogs' in self.event and 'data' in self.event['awslogs']:
            return self.CLOUD_WATCH_LOGS
        elif 'authorizationToken' in self.event and self.event['authorizationToken'] == "incoming-client-token":
            return self.API_GATEWAY_AUTHORIZER
        elif 'configRuleId' in self.event and 'configRuleName' in self.event and 'configRuleArn' in self.event:
            return self.AWS_CONFIG
        elif 'StackId' in self.event and 'RequestType' in self.event and 'ResourceType' in self.event:
            return self.CLOUD_FORMATION
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'eventSource' in self.event['Records'][0] and self.event['Records'][0]['eventSource'] == 'aws:codecommit':
            return self.CODE_COMMIT
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'eventSource' in self.event['Records'][0] and self.event['Records'][0]['eventSource'] == 'aws:ses':
            return self.SES
        elif 'Records' in self.event and len(self.event['Records']) > 0 and 'eventSource' in self.event['Records'][0] and self.event['Records'][0]['eventSource'] == 'aws:kinesis':
            return self.KINESIS
        elif 'records' in self.event and len(self.event['Records']) > 0 and 'approximateArrivalTimestamp' in self.event['records'][0]:
            return self.KINESIS_FIREHORSE
        elif 'records' in self.event and len(self.event['Records']) > 0 and 'deliveryStreamArn' in self.event and self.event['deliveryStreamArn'] is str and self.event['deliveryStreamArn'].startswith('arn:aws:kinesis:'):
            return self.KINESIS_FIREHORSE
        elif 'eventType' in self.event and self.event['eventType'] == 'SyncTrigger' and 'identityId' in self.event and 'identityPoolId' in self.event:
            return self.COGNITO_SYNC_TRIGGER
        elif 'operation' in self.event and 'message' in self.event:
            return self.MOBILE_BACKEND

        return self.UNIDENTIFIED


class AWSContext:

    def __init__(self, context) -> None:
        self._context = context

        self.aws_request_id = getattr(context, "aws_request_id", None)
        self.log_group_name = getattr(context, "log_group_name", None)
        self.log_stream_name = getattr(context, "log_stream_name", None)
        self.function_name = getattr(context, "function_name", None)
        self.memory_limit_in_mb = getattr(context, "memory_limit_in_mb", None)
        self.function_version = getattr(context, "function_version", None)
        self.invoked_function_arn = getattr(
            context, "invoked_function_arn", None)
        self.client_context = getattr(context, "client_context", None)

        self.size = getsizeof(context)

    @property
    def context(self) -> dict:
        return {
            "aws_request_id": self.aws_request_id,
            "log_group_name": self.log_group_name,
            "log_stream_name": self.log_stream_name,
            "function_name": self.function_name,
            "memory_limit_in_mb": self.memory_limit_in_mb,
            "function_version": self.function_version,
            "invoked_function_arn": self.invoked_function_arn,
            "client_context": self.client_context,
        }


def parse_function_payload(event, context):
    # TODO: make cloud case dest.
    return (
        AWSEvent(event),
        AWSContext(context)
    )
