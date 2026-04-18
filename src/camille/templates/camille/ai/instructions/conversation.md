## Conversation

You are in a multi-user conversation with the following users:

```jsonl
{% for user in all_users %}{{ user|safe }}
{% endfor %}
```

Current user is {{ current_user.username }} (id={{ current_user.id }})`