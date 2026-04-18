## Instructions

Here are the instructions and personnal preferences of the users in the conversation.

{% for user in all_users %}
### {{ user.username }} (id={{ user.id }})

{% if user.agent_config.instructions %}{{ user.agent_config.instructions }}{% else %}No specific instructions or preferences.{% endif %}
{% endfor %}