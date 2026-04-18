## Persistant memory

Your notes about the users in the conversation. For security reason, you can only update the notes of the current user.

Use this to save important observations that should persist across conversations.

{% for user in all_users %}
### {{ user.username }} (id={{ user.id }})

{% if user.agent_config.notes %}{{ user.agent_config.notes }}{% else %}No notes{% endif %}
{% endfor %}