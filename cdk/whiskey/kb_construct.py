"""Data bucket, S3 Vectors bucket + index, Bedrock KB and data source (design §3)."""

from aws_cdk import Aws, RemovalPolicy
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3vectors as s3vectors
from constructs import Construct

from cdk.whiskey.constants import EMBEDDING_DIM, EMBEDDING_MODEL
from cdk.whiskey.secure_bucket import secure_bucket


class KnowledgeBase(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self.data_bucket = secure_bucket(self, 'DataBucket')

        vector_bucket_name = f'whiskey-vectors-{Aws.ACCOUNT_ID}'
        self.vector_bucket = s3vectors.CfnVectorBucket(self, 'VectorBucket', vector_bucket_name=vector_bucket_name)
        self.vector_bucket.apply_removal_policy(RemovalPolicy.DESTROY)

        self.index = s3vectors.CfnIndex(
            self,
            'VectorIndex',
            vector_bucket_name=vector_bucket_name,
            index_name='whiskey-index',
            data_type='float32',
            dimension=EMBEDDING_DIM,
            distance_metric='cosine',
            # KB-7: Bedrock's text and metadata blobs must not count against the 2 KB filterable limit.
            metadata_configuration=s3vectors.CfnIndex.MetadataConfigurationProperty(
                non_filterable_metadata_keys=['AMAZON_BEDROCK_TEXT', 'AMAZON_BEDROCK_METADATA']
            ),
        )
        self.index.add_resource_dependency(self.vector_bucket)
        self.index.apply_removal_policy(RemovalPolicy.DESTROY)

        embed_arn = f'arn:aws:bedrock:{Aws.REGION}::foundation-model/{EMBEDDING_MODEL}'
        self.role = iam.Role(
            self,
            'KbRole',
            assumed_by=iam.ServicePrincipal(
                'bedrock.amazonaws.com',
                conditions={
                    'StringEquals': {'aws:SourceAccount': Aws.ACCOUNT_ID},
                    'ArnLike': {'aws:SourceArn': f'arn:aws:bedrock:{Aws.REGION}:{Aws.ACCOUNT_ID}:knowledge-base/*'},
                },
            ),
        )
        self.role.add_to_policy(iam.PolicyStatement(actions=['bedrock:InvokeModel'], resources=[embed_arn]))
        self.role.add_to_policy(
            iam.PolicyStatement(
                actions=['s3:ListBucket'],
                resources=[self.data_bucket.bucket_arn],
                conditions={'StringLike': {'s3:prefix': ['docs/*', 'docs/']}},
            )
        )
        self.role.add_to_policy(iam.PolicyStatement(actions=['s3:GetObject'], resources=[self.data_bucket.arn_for_objects('docs/*')]))
        self.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    's3vectors:PutVectors',
                    's3vectors:GetVectors',
                    's3vectors:DeleteVectors',
                    's3vectors:QueryVectors',
                    's3vectors:ListVectors',
                    's3vectors:GetIndex',
                ],
                resources=[self.index.attr_index_arn],
            )
        )
        self.role.add_to_policy(iam.PolicyStatement(actions=['s3vectors:GetVectorBucket'], resources=[self.vector_bucket.attr_vector_bucket_arn]))

        self.kb = bedrock.CfnKnowledgeBase(
            self,
            'Kb',
            name='whiskey-inventory',
            role_arn=self.role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type='VECTOR',
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=embed_arn,
                    embedding_model_configuration=bedrock.CfnKnowledgeBase.EmbeddingModelConfigurationProperty(
                        bedrock_embedding_model_configuration=bedrock.CfnKnowledgeBase.BedrockEmbeddingModelConfigurationProperty(
                            dimensions=EMBEDDING_DIM, embedding_data_type='FLOAT32'
                        )
                    ),
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type='S3_VECTORS',
                s3_vectors_configuration=bedrock.CfnKnowledgeBase.S3VectorsConfigurationProperty(index_arn=self.index.attr_index_arn),
            ),
        )
        self.kb.node.add_dependency(self.role)

        self.data_source = bedrock.CfnDataSource(
            self,
            'DataSource',
            name='whiskey-docs',
            knowledge_base_id=self.kb.attr_knowledge_base_id,
            data_deletion_policy='DELETE',
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type='S3',
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=self.data_bucket.bucket_arn, inclusion_prefixes=['docs/']
                ),
            ),
            # KB-4: one chunk per whiskey.
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(chunking_strategy='NONE')
            ),
        )

    @property
    def kb_id(self) -> str:
        return self.kb.attr_knowledge_base_id

    @property
    def kb_arn(self) -> str:
        return self.kb.attr_knowledge_base_arn
