# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import uuid
from enum import Enum

from fastapi_users.db import SQLAlchemyBaseOAuthAccountTable
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aperag.utils.utils import utc_now

# Create the declarative base
Base = declarative_base()


# Helper function for random id generation
def random_id():
    """Generate a random ID string"""
    return "".join(random.sample(uuid.uuid4().hex, 16))


# Helper function for creating enum columns that store values as varchar instead of database enum
def EnumColumn(enum_class, **kwargs):
    """Create a String column for enum values to avoid database enum constraints"""
    # Remove enum-specific kwargs that don't apply to String columns
    kwargs.pop("name", None)

    # Determine the maximum length needed for enum values
    max_length = max(len(e.value) for e in enum_class) if enum_class and len(enum_class) > 0 else 50
    # Add some buffer for future enum values
    max_length = max(max_length + 20, 50)

    # Set default length if not specified
    kwargs.setdefault("length", max_length)

    return String(**kwargs)


# Enums for choices
class CollectionStatus(str, Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class CollectionSummaryStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class CollectionType(str, Enum):
    DOCUMENT = "document"
    CHAT = "CHAT"


class CollectionMarketplaceStatusEnum(str, Enum):
    """Collection marketplace sharing status enumeration"""

    DRAFT = "DRAFT"  # Not published, only owner can see
    PUBLISHED = "PUBLISHED"  # Published to marketplace, publicly visible


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"  # 新增：已上传但未确认添加到collection
    EXPIRED = "EXPIRED"  # 新增：已过期的临时上传文档
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DELETED = "DELETED"


class DocumentIndexType(str, Enum):
    """Document index type enumeration"""

    VECTOR = "VECTOR"
    FULLTEXT = "FULLTEXT"
    GRAPH = "GRAPH"
    SUMMARY = "SUMMARY"
    VISION = "VISION"


class DocumentIndexStatus(str, Enum):
    """Document index lifecycle status"""

    PENDING = "PENDING"  # Awaiting processing (create/update)
    CREATING = "CREATING"  # Task claimed, creation/update in progress
    ACTIVE = "ACTIVE"  # Index is up-to-date and ready for use
    DELETING = "DELETING"  # Deletion has been requested
    DELETION_IN_PROGRESS = "DELETION_IN_PROGRESS"  # Task claimed, deletion in progress
    FAILED = "FAILED"  # The last operation failed


class BotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class BotType(str, Enum):
    KNOWLEDGE = "knowledge"
    COMMON = "common"
    AGENT = "agent"


class Role(str, Enum):
    ADMIN = "admin"
    RW = "rw"
    RO = "ro"


class ChatStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class ChatPeerType(str, Enum):
    SYSTEM = "system"
    FEISHU = "feishu"
    WEIXIN = "weixin"
    WEIXIN_OFFICIAL = "weixin_official"
    WEB = "web"
    DINGTALK = "dingtalk"


class MessageFeedbackStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class MessageFeedbackType(str, Enum):
    GOOD = "good"
    BAD = "bad"


class MessageFeedbackTag(str, Enum):
    HARMFUL = "Harmful"
    UNSAFE = "Unsafe"
    FAKE = "Fake"
    UNHELPFUL = "Unhelpful"
    OTHER = "Other"


class ModelServiceProviderStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"


class ApiKeyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class APIType(str, Enum):
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    RERANK = "rerank"


class QuestionType(str, Enum):
    """Question type enumeration"""

    FACTUAL = "FACTUAL"
    INFERENTIAL = "INFERENTIAL"
    USER_DEFINED = "USER_DEFINED"


class EvaluationStatus(str, Enum):
    """Evaluation task lifecycle status"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EvaluationItemStatus(str, Enum):
    """Evaluation item lifecycle status"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Models
class Collection(Base):
    __tablename__ = "collection"

    id = Column(String(24), primary_key=True, default=lambda: "col" + random_id())
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    user = Column(String(256), nullable=False, index=True)  # Add index for frequent queries
    status = Column(EnumColumn(CollectionStatus), nullable=False, index=True)  # Add index for status queries
    type = Column(EnumColumn(CollectionType), nullable=False)
    config = Column(Text, nullable=False)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries


class CollectionSummary(Base):
    __tablename__ = "collection_summary"
    __table_args__ = (UniqueConstraint("collection_id", name="uq_collection_summary"),)

    id = Column(String(24), primary_key=True, default=lambda: "cs" + random_id())
    collection_id = Column(String(24), nullable=False, index=True)

    # Reconciliation fields
    status = Column(
        EnumColumn(CollectionSummaryStatus), nullable=False, default=CollectionSummaryStatus.PENDING, index=True
    )
    version = Column(Integer, nullable=False, default=1)
    observed_version = Column(Integer, nullable=False, default=0)

    # Summary content and metadata
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_last_reconciled = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<CollectionSummary(id={self.id}, collection_id={self.collection_id}, status={self.status}, version={self.version})>"

    def update_version(self):
        """Update the version to trigger reconciliation"""
        self.version += 1
        self.gmt_updated = utc_now()


class CollectionMarketplace(Base):
    """Collection sharing status table"""

    __tablename__ = "collection_marketplace"
    __table_args__ = (
        UniqueConstraint("collection_id", name="uq_collection_marketplace_collection"),
        Index("idx_collection_marketplace_status", "status"),
        Index("idx_collection_marketplace_gmt_deleted", "gmt_deleted"),
        Index("idx_collection_marketplace_collection_id", "collection_id"),
        Index("idx_collection_marketplace_list", "status", "gmt_created"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "market_" + random_id()[:16])
    collection_id = Column(String(24), nullable=False)

    # Sharing status: use VARCHAR storage, not database enum type, validated at application layer
    status = Column(String(20), nullable=False, default=CollectionMarketplaceStatusEnum.DRAFT.value)

    # Timestamp fields
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)  # Updated in code layer
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<CollectionMarketplace(id={self.id}, collection_id={self.collection_id}, status={self.status})>"


class UserCollectionSubscription(Base):
    """User subscription to published collections table"""

    __tablename__ = "user_collection_subscription"
    __table_args__ = (
        # Allow multiple history records, but active subscription (gmt_deleted=NULL) must be unique
        UniqueConstraint(
            "user_id", "collection_marketplace_id", "gmt_deleted", name="idx_user_marketplace_history_unique"
        ),
        Index("idx_user_subscription_marketplace", "collection_marketplace_id"),
        Index("idx_user_subscription_user", "user_id"),
        Index("idx_user_subscription_gmt_deleted", "gmt_deleted"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "sub_" + random_id()[:16])
    user_id = Column(String(24), nullable=False)  # Related to users table, maintained at application layer
    collection_marketplace_id = Column(
        String(24), nullable=False
    )  # Related to collection_marketplace table, maintained at application layer

    # Timestamp fields
    gmt_subscribed = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)  # Soft delete: NULL means active subscription

    def __repr__(self):
        return f"<UserCollectionSubscription(id={self.id}, user_id={self.user_id}, marketplace_id={self.collection_marketplace_id})>"


class Document(Base):
    __tablename__ = "document"
    __table_args__ = (
        UniqueConstraint("collection_id", "name", "gmt_deleted", name="uq_document_collection_name_deleted"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "doc" + random_id())
    name = Column(String(1024), nullable=False)
    user = Column(String(256), nullable=False, index=True)  # Add index for user queries
    collection_id = Column(String(24), nullable=True, index=True)  # Add index for collection queries
    status = Column(EnumColumn(DocumentStatus), nullable=False, index=True)  # Add index for status queries
    size = Column(BigInteger, nullable=False)  # Support larger files (up to 9 exabytes)
    content_hash = Column(
        String(64), nullable=True, index=True
    )  # SHA-256 hash of original file content for duplicate detection
    object_path = Column(Text, nullable=True)
    doc_metadata = Column(Text, nullable=True)  # Store document metadata as JSON string
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries

    def get_document_indexes(self, session):  # 查询当前文档对应的所有索引任务
        """Get document indexes from the merged table"""

        stmt = select(DocumentIndex).where(DocumentIndex.document_id == self.id)
        result = session.execute(stmt)
        return result.scalars().all()

    def get_overall_index_status(self, session) -> "DocumentStatus":
        """Calculate overall status based on document indexes"""
        document_indexes = self.get_document_indexes(session)  # 查询当前文档对应的所有索引任务

        if not document_indexes:  # 如果当前文档没有索引任务，则返回文档状态PENDING
            return DocumentStatus.PENDING

        statuses = [idx.status for idx in document_indexes]  # 收集当前文档的所有索引任务状态列表

        if any(status == DocumentIndexStatus.FAILED for status in statuses):  # 只要有一个索引任务为失败状态，则返回文档状态FAILED
            return DocumentStatus.FAILED
        elif any(
            status in [DocumentIndexStatus.CREATING, DocumentIndexStatus.DELETION_IN_PROGRESS] for status in statuses
        ):  # 只要一个索引任务为处理中状态，则返回文档状态RUNNING
            return DocumentStatus.RUNNING
        elif all(status == DocumentIndexStatus.ACTIVE for status in statuses):  # 仅当所有索引任务为已完成状态，则返回文档状态COMPLETE
            return DocumentStatus.COMPLETE
        else:
            return DocumentStatus.PENDING

    def object_store_base_path(self) -> str:  # 为当前文档信息实例生成对象存储基本路径
        """Generate the base path for object store"""
        user = self.user.replace("|", "-")
        return f"user-{user}/{self.collection_id}/{self.id}"  # 基本路径规则：“user-{用户id}/{知识库id}/{文档信息id}”

    async def get_collection(self, session):
        """Get the associated collection object"""
        return await session.get(Collection, self.collection_id)

    async def set_collection(self, collection):
        """Set the collection_id by Collection object or id"""
        if hasattr(collection, "id"):
            self.collection_id = collection.id
        elif isinstance(collection, str):
            self.collection_id = collection


class Bot(Base):
    __tablename__ = "bot"

    id = Column(String(24), primary_key=True, default=lambda: "bot" + random_id())
    user = Column(String(256), nullable=False, index=True)  # Add index for user queries
    title = Column(String(256), nullable=True)
    type = Column(EnumColumn(BotType), nullable=False, default=BotType.KNOWLEDGE)
    description = Column(Text, nullable=True)
    status = Column(EnumColumn(BotStatus), nullable=False, index=True)  # Add index for status queries
    config = Column(Text, nullable=False)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries


class ConfigModel(Base):
    __tablename__ = "config"

    key = Column(String(256), primary_key=True)
    value = Column(Text, nullable=False)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)


class UserQuota(Base):
    __tablename__ = "user_quota"

    user = Column(String(256), primary_key=True)
    key = Column(String(256), primary_key=True)
    quota_limit = Column(Integer, default=0, nullable=False)  # Renamed from 'value' for clarity
    current_usage = Column(Integer, default=0, nullable=False)  # New field to track current usage
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def is_quota_exceeded(self, additional_usage: int = 1) -> bool:
        """Check if adding additional usage would exceed the quota limit"""
        return (self.current_usage + additional_usage) > self.quota_limit

    def can_consume(self, amount: int = 1) -> bool:
        """Check if the specified amount can be consumed without exceeding quota"""
        return not self.is_quota_exceeded(amount)


class Chat(Base):
    __tablename__ = "chat"
    __table_args__ = (
        UniqueConstraint("bot_id", "peer_type", "peer_id", "gmt_deleted", name="uq_chat_bot_peer_deleted"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "chat" + random_id())
    user = Column(String(256), nullable=False, index=True)  # Add index for user queries
    peer_type = Column(EnumColumn(ChatPeerType), nullable=False, default=ChatPeerType.SYSTEM)
    peer_id = Column(String(256), nullable=True)
    status = Column(EnumColumn(ChatStatus), nullable=False, index=True)  # Add index for status queries
    bot_id = Column(String(24), nullable=False, index=True)  # Add index for bot queries
    title = Column(String(256), nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries

    async def get_bot(self, session):
        """Get the associated bot object"""
        return await session.get(Bot, self.bot_id)

    async def set_bot(self, bot):
        """Set the bot_id by Bot object or id"""
        if hasattr(bot, "id"):
            self.bot_id = bot.id
        elif isinstance(bot, str):
            self.bot_id = bot


class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    __table_args__ = (
        UniqueConstraint("chat_id", "message_id", "gmt_deleted", name="uq_feedback_chat_message_deleted"),
    )

    user = Column(String(256), nullable=False, index=True)  # Add index for user queries
    chat_id = Column(String(24), primary_key=True)
    message_id = Column(String(256), primary_key=True)
    type = Column(EnumColumn(MessageFeedbackType), nullable=True)
    tag = Column(EnumColumn(MessageFeedbackTag), nullable=True)
    message = Column(Text, nullable=True)
    question = Column(Text, nullable=True)
    status = Column(EnumColumn(MessageFeedbackStatus), nullable=True, index=True)  # Add index for status queries
    original_answer = Column(Text, nullable=True)
    revised_answer = Column(Text, nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries

    async def get_chat(self, session):
        """Get the associated chat object"""
        return await session.get(Chat, self.chat_id)

    async def set_chat(self, chat):
        """Set the chat_id by Chat object or id"""
        if hasattr(chat, "id"):
            self.chat_id = chat.id
        elif isinstance(chat, str):
            self.chat_id = chat


class ApiKey(Base):
    __tablename__ = "api_key"

    id = Column(String(24), primary_key=True, default=lambda: "key" + random_id())
    key = Column(String(64), default=lambda: f"sk-{uuid.uuid4().hex}", nullable=False)
    user = Column(String(256), nullable=False, index=True)  # Add index for user queries
    description = Column(String(256), nullable=True)
    status = Column(EnumColumn(ApiKeyStatus), nullable=False, index=True)  # Add index for status queries
    is_system = Column(Boolean, default=False, nullable=False, index=True)  # Mark system-generated API keys
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries

    @staticmethod
    def generate_key() -> str:
        """Generate a unique API key"""
        return f"sk-{uuid.uuid4().hex}"

    async def update_last_used(self, session):
        """Update the last_used_at timestamp"""
        self.last_used_at = utc_now()
        session.add(self)
        await session.commit()


class ModelServiceProvider(Base):
    __tablename__ = "model_service_provider"
    __table_args__ = (UniqueConstraint("name", "gmt_deleted", name="uq_model_service_provider_name_deleted"),)

    id = Column(String(24), primary_key=True, default=lambda: "msp" + random_id())
    name = Column(String(256), nullable=False, index=True)  # Reference to LLMProvider.name
    status = Column(EnumColumn(ModelServiceProviderStatus), nullable=False, index=True)  # Add index for status queries
    api_key = Column(String(256), nullable=False)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries


class LLMProvider(Base):
    """LLM Provider configuration model

    This model stores the provider-level configuration that was previously
    stored in model_configs.json file. Each provider has basic information
    and dialect configurations for different API types.
    """

    __tablename__ = "llm_provider"

    name = Column(String(128), primary_key=True)  # Unique provider name identifier
    user_id = Column(String(256), nullable=False, index=True)  # Owner of the provider config, "public" for global
    label = Column(String(256), nullable=False)  # Human-readable provider display name
    completion_dialect = Column(String(64), nullable=False)  # API dialect for completion/chat APIs
    embedding_dialect = Column(String(64), nullable=False)  # API dialect for embedding APIs
    rerank_dialect = Column(String(64), nullable=False)  # API dialect for rerank APIs
    allow_custom_base_url = Column(Boolean, default=False, nullable=False)  # Whether custom base URLs are allowed
    base_url = Column(String(512), nullable=False)  # Default API base URL for this provider
    extra = Column(Text, nullable=True)  # Additional configuration data in JSON format
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def __str__(self):
        return f"LLMProvider(name={self.name}, label={self.label}, user_id={self.user_id})"


class LLMProviderModel(Base):
    """LLM Provider Model configuration

    This model stores individual model configurations for each provider.
    Each model belongs to a provider and has a specific API type (completion, embedding, rerank).
    """

    __tablename__ = "llm_provider_models"

    provider_name = Column(String(128), primary_key=True)  # Reference to LLMProvider.name
    api = Column(EnumColumn(APIType), nullable=False, primary_key=True)
    model = Column(String(256), primary_key=True)  # Model name/identifier
    custom_llm_provider = Column(String(128), nullable=False)  # Custom LLM provider implementation
    context_window = Column(Integer, nullable=True)  # Context window size (total tokens)
    max_input_tokens = Column(Integer, nullable=True)  # Maximum input tokens
    max_output_tokens = Column(Integer, nullable=True)  # Maximum output tokens
    tags = Column(JSON, default=lambda: [], nullable=True)  # Tags for model categorization
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def __str__(self):
        return f"LLMProviderModel(provider={self.provider_name}, api={self.api}, model={self.model})"

    async def get_provider(self, session):
        """Get the associated provider object"""
        return await session.get(LLMProvider, self.provider_name)

    async def set_provider(self, provider):
        """Set the provider_name by LLMProvider object or name"""
        if hasattr(provider, "name"):
            self.provider_name = provider.name
        elif isinstance(provider, str):
            self.provider_name = provider

    def has_tag(self, tag: str) -> bool:
        """Check if model has a specific tag"""
        return tag in (self.tags or [])

    def add_tag(self, tag: str) -> bool:
        """Add a tag to model. Returns True if tag was added, False if already exists"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            return True
        return False

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from model. Returns True if tag was removed, False if not found"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def get_tags(self) -> list:
        """Get all tags for this model"""
        return self.tags or []


class User(Base):
    __tablename__ = "user"

    id = Column(String(24), primary_key=True, default=lambda: "user" + random_id())
    username = Column(String(256), unique=True, nullable=True)  # Unified with other user fields
    email = Column(String(254), unique=True, nullable=True)
    role = Column(EnumColumn(Role), nullable=False, default=Role.RO)
    hashed_password = Column(String(128), nullable=False)  # fastapi-users expects hashed_password
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)  # fastapi-users requires is_verified
    is_staff = Column(Boolean, default=False, nullable=False)
    chat_collection_id = Column(String(24), nullable=True, index=True)  # Chat collection for user
    date_joined = Column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )  # Unified naming with other time fields
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship("OAuthAccount", lazy="joined", back_populates="user")

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, value):
        self.hashed_password = value


class OAuthAccount(SQLAlchemyBaseOAuthAccountTable[str], Base):
    __tablename__ = "oauth_account"

    id = Column(String(24), primary_key=True, default=lambda: "oauth" + random_id())
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user.id", ondelete="cascade"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")


class Invitation(Base):
    __tablename__ = "invitation"

    id = Column(String(24), primary_key=True, default=lambda: "invite" + random_id())
    email = Column(String(254), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    created_by = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    role = Column(EnumColumn(Role), nullable=False, default=Role.RO)

    def is_valid(self) -> bool:
        """Check if invitation is still valid"""
        now = utc_now()
        return not self.is_used and now < self.expires_at

    async def use(self, session):
        """Mark invitation as used"""
        self.is_used = True
        self.used_at = utc_now()
        session.add(self)
        await session.commit()

        # Auto-expire after use (optional)
        # self.expires_at = utc_now()


class SearchHistory(Base):
    __tablename__ = "searchhistory"

    id = Column(String(24), primary_key=True, default=lambda: "sh" + random_id())
    user = Column(String(256), nullable=False, index=True)  # Add index for user queries
    collection_id = Column(String(24), nullable=True, index=True)  # Add index for collection queries
    query = Column(Text, nullable=False)
    vector_search = Column(JSON, default=lambda: {}, nullable=True)
    fulltext_search = Column(JSON, default=lambda: {}, nullable=True)
    graph_search = Column(JSON, default=lambda: {}, nullable=True)
    summary_search = Column(JSON, default=lambda: {}, nullable=True)
    vision_search = Column(JSON, default=lambda: {}, nullable=True)
    items = Column(JSON, default=lambda: [], nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True, index=True)  # Add index for soft delete queries


class LightRAGDocChunksModel(Base):
    """LightRAG Document Chunks Storage Model"""

    __tablename__ = "lightrag_doc_chunks"

    id = Column(String(255), primary_key=True)
    workspace = Column(String(255), primary_key=True)
    full_doc_id = Column(String(256), nullable=True)
    chunk_order_index = Column(Integer, nullable=True)
    tokens = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    content_vector = Column(Vector(), nullable=True)
    file_path = Column(String(256), nullable=True)
    create_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    update_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class LightRAGVDBEntityModel(Base):
    """LightRAG VDB Entity Storage Model"""

    __tablename__ = "lightrag_vdb_entity"

    id = Column(String(255), primary_key=True)
    workspace = Column(String(255), primary_key=True)
    entity_name = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    content_vector = Column(Vector(), nullable=True)
    create_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    update_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    chunk_ids = Column(ARRAY(String), nullable=True)
    file_path = Column(Text, nullable=True)


class LightRAGVDBRelationModel(Base):
    """LightRAG VDB Relation Storage Model"""

    __tablename__ = "lightrag_vdb_relation"

    id = Column(String(255), primary_key=True)
    workspace = Column(String(255), primary_key=True)
    source_id = Column(String(256), nullable=True)
    target_id = Column(String(256), nullable=True)
    content = Column(Text, nullable=True)
    content_vector = Column(Vector(), nullable=True)
    create_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    update_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    chunk_ids = Column(ARRAY(String), nullable=True)
    file_path = Column(Text, nullable=True)


class DocumentIndex(Base):
    """Document index - single status model"""

    __tablename__ = "document_index"
    __table_args__ = (UniqueConstraint("document_id", "index_type", name="uq_document_index"),)

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(24), nullable=False, index=True)
    index_type = Column(EnumColumn(DocumentIndexType), nullable=False, index=True)

    status = Column(EnumColumn(DocumentIndexStatus), nullable=False, default=DocumentIndexStatus.PENDING, index=True)
    # 索引任务完成后，会有version==observed_version。创建索引任务时，version初始化为1，observed_version初始化为0，表示索引任务已创建但未处理【observed_version小于version】
    version = Column(Integer, nullable=False, default=1)  # Incremented on each spec change 每次更新后的版本号，初始值为1，数据的 “当前真实版本号”
    observed_version = Column(Integer, nullable=False, default=0)  # Last processed spec version 最近处理过的版本号，初始值为0，“已处理过的版本号”（处理完成后，会将 observed_version 同步为当前的 version）

    # Index data and task tracking
    index_data = Column(Text, nullable=True)  # JSON string for index-specific data
    error_message = Column(Text, nullable=True)

    # Timestamps
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_last_reconciled = Column(DateTime(timezone=True), nullable=True)  # Last reconciliation attempt

    def __repr__(self):
        return f"<DocumentIndex(id={self.id}, document_id={self.document_id}, type={self.index_type}, status={self.status}, version={self.version})>"

    def update_version(self):
        """Update the version to trigger reconciliation"""
        self.version += 1
        self.gmt_updated = utc_now()


class AuditResource(str, Enum):
    """Audit resource types"""

    COLLECTION = "collection"
    DOCUMENT = "document"
    BOT = "bot"
    CHAT = "chat"
    MESSAGE = "message"
    API_KEY = "api_key"
    LLM_PROVIDER = "llm_provider"
    LLM_PROVIDER_MODEL = "llm_provider_model"
    MODEL_SERVICE_PROVIDER = "model_service_provider"
    USER = "user"
    CONFIG = "config"
    INVITATION = "invitation"
    AUTH = "auth"
    CHAT_COMPLETION = "chat_completion"
    SEARCH = "search"
    LLM = "llm"
    FLOW = "flow"
    SYSTEM = "system"
    INDEX = "index"


class AuditLog(Base):
    """Audit log model to track all system operations"""

    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, comment="User ID")
    username = Column(String(255), nullable=True, comment="Username")
    resource_type = Column(EnumColumn(AuditResource), nullable=True, comment="Resource type")
    resource_id = Column(String(255), nullable=True, comment="Resource ID (extracted at query time)")
    api_name = Column(String(255), nullable=False, comment="API operation name")
    http_method = Column(String(10), nullable=False, comment="HTTP method (POST, PUT, DELETE)")
    path = Column(String(512), nullable=False, comment="API path")
    status_code = Column(Integer, nullable=True, comment="HTTP status code")
    request_data = Column(Text, nullable=True, comment="Request data (JSON)")
    response_data = Column(Text, nullable=True, comment="Response data (JSON)")
    error_message = Column(Text, nullable=True, comment="Error message if failed")
    ip_address = Column(String(45), nullable=True, comment="Client IP address")
    user_agent = Column(String(500), nullable=True, comment="User agent string")
    request_id = Column(String(255), nullable=False, comment="Request ID for tracking")
    start_time = Column(BigInteger, nullable=False, comment="Request start time (milliseconds since epoch)")
    end_time = Column(BigInteger, nullable=True, comment="Request end time (milliseconds since epoch)")
    gmt_created = Column(DateTime(timezone=True), nullable=False, default=utc_now, comment="Created time")

    # Index for better query performance
    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_resource_type", "resource_type"),
        Index("idx_audit_api_name", "api_name"),
        Index("idx_audit_http_method", "http_method"),
        Index("idx_audit_status_code", "status_code"),
        Index("idx_audit_gmt_created", "gmt_created"),
        Index("idx_audit_resource_id", "resource_id"),
        Index("idx_audit_request_id", "request_id"),
        Index("idx_audit_start_time", "start_time"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, api={self.api_name}, method={self.http_method}, status={self.status_code})>"


# Graph Database Models
class LightRAGGraphNode(Base):
    """LightRAG Graph Node Storage Model - unified with SQLAlchemy"""

    __tablename__ = "lightrag_graph_nodes"
    __table_args__ = (
        UniqueConstraint("workspace", "entity_id", name="uq_lightrag_graph_nodes_workspace_entity"),
        Index("idx_lightrag_nodes_entity_type", "workspace", "entity_type"),
        Index("idx_lightrag_nodes_entity_name", "workspace", "entity_name"),
        # Performance optimization indexes for batch operations
        Index("idx_lightrag_nodes_workspace_createtime", "workspace", "createtime"),
        Index("idx_lightrag_nodes_entity_type_createtime", "workspace", "entity_type", "createtime"),
        # Composite index for common query patterns
        Index("idx_lightrag_nodes_workspace_type_id", "workspace", "entity_type", "entity_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entity_id = Column(String(256), nullable=False)
    entity_name = Column(String(255), nullable=True)
    entity_type = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    source_id = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    workspace = Column(String(255), nullable=False)
    createtime = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updatetime = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __repr__(self):
        return f"<LightRAGGraphNode(workspace={self.workspace}, entity_id={self.entity_id})>"


class LightRAGGraphEdge(Base):
    """LightRAG Graph Edge Storage Model - unified with SQLAlchemy"""

    __tablename__ = "lightrag_graph_edges"
    __table_args__ = (
        UniqueConstraint(
            "workspace", "source_entity_id", "target_entity_id", name="uq_lightrag_graph_edges_workspace_source_target"
        ),
        Index("idx_lightrag_edges_workspace_source", "workspace", "source_entity_id"),
        Index("idx_lightrag_edges_workspace_target", "workspace", "target_entity_id"),
        Index("idx_lightrag_edges_weight", "workspace", "weight"),
        # Performance optimization indexes for batch operations and degree calculations
        Index("idx_lightrag_edges_workspace_source_target", "workspace", "source_entity_id", "target_entity_id"),
        Index("idx_lightrag_edges_workspace_target_source", "workspace", "target_entity_id", "source_entity_id"),
        # Index for efficient degree calculations (covers both source and target in one index)
        Index("idx_lightrag_edges_degree_calc", "workspace", "source_entity_id", "target_entity_id", "weight"),
        # Index for time-based queries
        Index("idx_lightrag_edges_workspace_createtime", "workspace", "createtime"),
        # Covering index for edge metadata queries
        Index("idx_lightrag_edges_metadata", "workspace", "source_entity_id", "target_entity_id", "weight", "keywords"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_entity_id = Column(String(255), nullable=False)
    target_entity_id = Column(String(255), nullable=False)
    weight = Column(Numeric(10, 6), default=0.0, nullable=False)  # DECIMAL(10,6) for precise weight values
    keywords = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    source_id = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    workspace = Column(String(255), nullable=False)
    createtime = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updatetime = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __repr__(self):
        return f"<LightRAGGraphEdge(workspace={self.workspace}, {self.source_entity_id}->{self.target_entity_id})>"


class MergeSuggestionStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class MergeSuggestion(Base):
    """Active merge suggestions for knowledge graph node merging (PENDING only)"""

    __tablename__ = "graph_index_merge_suggestions"
    __table_args__ = (
        # Only allow one active suggestion per entity combination per collection
        UniqueConstraint("collection_id", "entity_ids_hash", name="uq_graph_index_merge_suggestions"),
        Index("idx_graph_index_merge_suggestions_collection", "collection_id"),
        Index("idx_graph_index_merge_suggestions_created", "gmt_created"),
        Index("idx_graph_index_merge_suggestions_batch", "collection_id", "suggestion_batch_id"),
        Index("idx_graph_index_merge_suggestions_confidence", "confidence_score"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "msug" + random_id())
    collection_id = Column(String(24), nullable=False, index=True)

    # Suggestion batch (same batch_id for suggestions generated in the same LLM call)
    suggestion_batch_id = Column(String(24), nullable=False, index=True, default=lambda: "batch" + random_id())

    # Entity combination for merging
    entity_ids = Column(ARRAY(String), nullable=False)  # Entity IDs suggested for merging
    entity_ids_hash = Column(String(64), nullable=False)  # Hash of entity ID combination for uniqueness

    # LLM analysis results
    confidence_score = Column(Numeric(3, 2), nullable=False)  # 0.00-1.00
    merge_reason = Column(Text, nullable=False)  # LLM-generated reason for merging
    suggested_target_entity = Column(JSON, nullable=False)  # Suggested target entity {entity_name, entity_type}

    # Status (always PENDING for active suggestions)
    status = Column(
        EnumColumn(MergeSuggestionStatus), nullable=False, default=MergeSuggestionStatus.PENDING, index=True
    )

    # Timestamps
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    @classmethod
    def generate_entity_ids_hash(cls, entity_ids: list) -> str:
        """Generate hash for entity ID combination"""
        import hashlib

        sorted_ids = sorted(entity_ids)
        return hashlib.md5(":".join(sorted_ids).encode()).hexdigest()

    def __repr__(self):
        return f"<MergeSuggestion(id={self.id}, collection_id={self.collection_id}, entities={len(self.entity_ids)})>"


class MergeSuggestionHistory(Base):
    """History of processed merge suggestions for knowledge graph node merging"""

    __tablename__ = "graph_index_merge_suggestions_history"
    __table_args__ = (
        Index("idx_graph_index_merge_suggestions_history_collection", "collection_id"),
        Index("idx_graph_index_merge_suggestions_history_collection_status", "collection_id", "status"),
        Index("idx_graph_index_merge_suggestions_history_operated_at", "operated_at"),
        Index("idx_graph_index_merge_suggestions_history_original_id", "original_suggestion_id"),
        Index("idx_graph_index_merge_suggestions_history_batch", "suggestion_batch_id"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "hsug" + random_id())
    original_suggestion_id = Column(String(24), nullable=False, index=True)  # ID from active suggestions
    collection_id = Column(String(24), nullable=False, index=True)

    # Suggestion batch (same batch_id for suggestions generated in the same LLM call)
    suggestion_batch_id = Column(String(24), nullable=False, index=True)

    # Entity combination for merging
    entity_ids = Column(ARRAY(String), nullable=False)  # Entity IDs suggested for merging
    entity_ids_hash = Column(String(64), nullable=False)  # Hash of entity ID combination for uniqueness

    # LLM analysis results
    confidence_score = Column(Numeric(3, 2), nullable=False)  # 0.00-1.00
    merge_reason = Column(Text, nullable=False)  # LLM-generated reason for merging
    suggested_target_entity = Column(JSON, nullable=False)  # Suggested target entity {entity_name, entity_type}

    # Status (ACCEPTED or REJECTED only)
    status = Column(EnumColumn(MergeSuggestionStatus), nullable=False, index=True)

    # Timestamps
    gmt_created = Column(DateTime(timezone=True), nullable=False)  # Original creation time
    operated_at = Column(DateTime(timezone=True), nullable=False)  # When the action was taken

    # User operation tracking
    operated_by = Column(String(24), nullable=True)  # User ID who performed the action

    @classmethod
    def generate_entity_ids_hash(cls, entity_ids: list) -> str:
        """Generate hash for entity ID combination"""
        import hashlib

        sorted_ids = sorted(entity_ids)
        return hashlib.md5(":".join(sorted_ids).encode()).hexdigest()

    def __repr__(self):
        return (
            f"<MergeSuggestionHistory(id={self.id}, original_id={self.original_suggestion_id}, status={self.status})>"
        )


class QuestionSet(Base):
    __tablename__ = "question_sets"
    __table_args__ = (
        Index("idx_question_sets_user_id", "user_id"),
        Index("idx_question_sets_collection_id", "collection_id"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "qs_" + random_id()[:16])
    user_id = Column(String(24), nullable=False)
    collection_id = Column(String(24), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<QuestionSet(id={self.id}, name={self.name}, user_id={self.user_id})>"


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (Index("idx_questions_question_set_id", "question_set_id"),)

    id = Column(String(24), primary_key=True, default=lambda: "q_" + random_id()[:16])
    question_set_id = Column(String(24), nullable=False)
    question_type = Column(EnumColumn(QuestionType), nullable=True)
    question_text = Column(Text, nullable=False)
    ground_truth = Column(Text, nullable=False)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Question(id={self.id}, qs_id={self.question_set_id})>"


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        Index("idx_evaluations_user_id", "user_id"),
        Index("idx_evaluations_status", "status"),
        Index("idx_evaluations_collection_id", "collection_id"),
    )

    id = Column(String(24), primary_key=True, default=lambda: "eval_" + random_id()[:16])
    user_id = Column(String(24), nullable=False)
    name = Column(String(255), nullable=False)
    collection_id = Column(String(24), nullable=False)
    question_set_id = Column(String(24), nullable=False)
    agent_llm_config = Column(JSON, nullable=False)
    judge_llm_config = Column(JSON, nullable=False)
    status = Column(EnumColumn(EvaluationStatus), nullable=False, default=EvaluationStatus.PENDING)
    error_message = Column(Text, nullable=True)
    total_questions = Column(Integer, nullable=False, default=0)
    completed_questions = Column(Integer, nullable=False, default=0)
    average_score = Column(Numeric(3, 2), nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Evaluation(id={self.id}, name={self.name}, status={self.status})>"


class EvaluationItem(Base):
    __tablename__ = "evaluation_items"
    __table_args__ = (Index("idx_evaluation_items_evaluation_id", "evaluation_id"),)

    id = Column(String(24), primary_key=True, default=lambda: "item_" + random_id()[:16])
    evaluation_id = Column(String(24), nullable=False)
    question_id = Column(String(24), nullable=True)
    status = Column(EnumColumn(EvaluationItemStatus), nullable=False, default=EvaluationItemStatus.PENDING, index=True)
    question_text = Column(Text, nullable=False)
    ground_truth = Column(Text, nullable=False)
    rag_answer = Column(Text, nullable=True)
    rag_answer_details = Column(JSON, nullable=True)
    llm_judge_score = Column(Integer, nullable=True)
    llm_judge_reasoning = Column(Text, nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<EvaluationItem(id={self.id}, eval_id={self.evaluation_id}, q_id={self.question_id})>"


class Setting(Base):
    __tablename__ = "setting"

    key = Column(String(256), primary_key=True)
    value = Column(Text, nullable=True)
    gmt_created = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_updated = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    gmt_deleted = Column(DateTime(timezone=True), nullable=True)
