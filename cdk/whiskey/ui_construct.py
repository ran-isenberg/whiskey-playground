"""Private UI bucket behind CloudFront with OAC (design §7.1, §8)."""

from pathlib import Path

from aws_cdk import aws_cloudfront as cf
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct

from cdk.whiskey.constants import UI_DIST_DIR
from cdk.whiskey.secure_bucket import secure_bucket


class UiHosting(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)
        self.bucket = secure_bucket(self, 'UiBucket')
        self.distribution = cf.Distribution(
            self,
            'Distribution',
            default_root_object='index.html',
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.bucket),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
            ),
        )

    @property
    def url(self) -> str:
        return f'https://{self.distribution.distribution_domain_name}'

    def deploy(self, api_url: str) -> None:
        """Upload ui/dist plus a runtime config.json (no build-time dependency on the API URL)."""
        sources = [s3deploy.Source.json_data('config.json', {'apiUrl': api_url})]
        if Path(UI_DIST_DIR).is_dir():
            sources.insert(0, s3deploy.Source.asset(UI_DIST_DIR))
        s3deploy.BucketDeployment(
            self,
            'Deploy',
            destination_bucket=self.bucket,
            sources=sources,
            distribution=self.distribution,
            distribution_paths=['/*'],
            memory_limit=512,
        )
