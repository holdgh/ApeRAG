import json
from http import HTTPStatus

from config import settings
from kubechat.chat.history.redis import RedisChatMessageHistory
from kubechat.db.models import MessageFeedback, MessageFeedbackStatus
from kubechat.views.utils import fail


async def feedback_message(user, chat_id, message_id, upvote, downvote, revised_answer=None):
    history = RedisChatMessageHistory(chat_id, url=settings.MEMORY_REDIS_URL)
    msg = None
    for message in await history.messages:
        item = json.loads(message.content)
        if item["id"] != message_id:
            continue
        if message.additional_kwargs.get("role", "") != "ai":
            continue
        msg = item
    if msg is None:
        return fail(HTTPStatus.NOT_FOUND, "Message not found")
    data = {
        "question": msg["query"],
        "original_answer": msg.get("response", ""),
    }
    if upvote is not None:
        data["upvote"] = upvote
    if downvote is not None:
        data["downvote"] = downvote

    if revised_answer is not None:
        data["revised_answer"] = revised_answer
    data["status"] = MessageFeedbackStatus.PENDING
    feedback, _ = await MessageFeedback.objects.aupdate_or_create(
        user=user, chat_id=chat_id, message_id=message_id, collection_id=msg["collection_id"],
        defaults=data
    )
    return feedback
