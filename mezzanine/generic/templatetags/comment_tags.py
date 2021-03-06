
from collections import defaultdict

from django.core.urlresolvers import reverse

from mezzanine import template
from mezzanine.generic.forms import ThreadedCommentForm
from mezzanine.generic.models import ThreadedComment


register = template.Library()


@register.inclusion_tag("generic/includes/comments.html", takes_context=True)
def comments_for(context, obj):
    """
    Provides a generic context variable name for the object that
    comments are being rendered for.
    """
    form = ThreadedCommentForm(context["request"], obj)
    try:
        context["posted_comment_form"]
    except KeyError:
        context["posted_comment_form"] = form
    context["unposted_comment_form"] = form
    context["comment_url"] = reverse("comment")
    context["object_for_comments"] = obj
    return context


@register.inclusion_tag("generic/includes/comment.html", takes_context=True)
def comment_thread(context, parent):
    """
    Return a list of child comments for the given parent, storing all
    comments in a dict in the context when first called, using parents
    as keys for retrieval on subsequent recursive calls from the
    comments template.
    """
    if "all_comments" not in context:
        comments = defaultdict(list)
        if "request" in context and context["request"].user.is_staff:
            comments_queryset = parent.comments.all()
        else:
            comments_queryset = parent.comments.visible()
        for comment in comments_queryset.select_related("user"):
            comments[comment.replied_to_id].append(comment)
        context["all_comments"] = comments
        parent = None
    else:
        parent = parent.id
    try:
        replied_to = int(context["request"].POST["replied_to"])
    except KeyError:
        replied_to = 0
    context.update({
        "comments_for_thread": context["all_comments"].get(parent, []),
        "no_comments": parent is None and not comments,
        "replied_to": replied_to,
    })
    return context


@register.simple_tag
def gravatar_url(email_hash, size=32):
    """
    Return the full URL for a Gravatar given an email hash.
    """
    return "http://www.gravatar.com/avatar/%s?s=%s" % (email_hash, size)


@register.inclusion_tag("admin/includes/recent_comments.html",
    takes_context=True)
def recent_comments(context):
    """
    Dashboard widget for displaying recent comments.
    """
    latest = context["settings"].COMMENTS_NUM_LATEST
    comments = ThreadedComment.objects.all().select_related(depth=1)
    context["comments"] = comments.order_by("-id")[:latest]
    return context
