# class Profile(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="profile",
#         related_query_name="profile",
#     )

#     # LLM default settings
#     model_name = models.CharField(
#         max_length=100,
#         blank=True,
#         null=True,
#     )
#     notes = models.TextField(blank=True, null=True)
#     personality = models.ForeignKey(
#         "AgentPersonality",
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#     )

#     def __str__(self) -> str:
#         return self.user.username


# # create profile when user is created
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


# class InferenceProvider(models.TextChoices):
#     BEDROCK = "bedrock", "Bedrock"
#     GOOGLE_GLA = "google_gla", "Google GLA"
#     MISTRAL_AI = "mistral_ai", "Mistral AI"


# class InferenceCredentials(models.Model):
#     default_provider: InferenceProvider

#     class Meta:
#         abstract = True
#         unique_together = ("user", "provider")

#     profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
#     provider = models.CharField(max_length=20, choices=InferenceProvider.choices)

#     def save(
#         self,
#         *args,
#         **kwargs,
#     ) -> None:
#         self.provider = self.default_provider

#         return super().save(*args, **kwargs)


# class ApiKeyInferenceCredentials(InferenceCredentials):
#     class Meta:
#         abstract = True

#     api_key = models.CharField(max_length=255)


# class BedrockCredentials(ApiKeyInferenceCredentials):
#     default_provider = InferenceProvider.BEDROCK
#     region = models.CharField(max_length=100)


# class GoogleGLACredentials(ApiKeyInferenceCredentials):
#     default_provider = InferenceProvider.GOOGLE_GLA


# class MistralAICredentials(ApiKeyInferenceCredentials):
#     default_provider = InferenceProvider.MISTRAL_AI


# class AgentPersonality(models.Model):
#     owner = models.ForeignKey(
#         Profile,
#         on_delete=models.CASCADE,
#     )
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     prompt_template = models.TextField()

#     def __str__(self) -> str:
#         return self.name


# class LLMThread(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     summary = models.TextField()

#     def messages(self) -> list:
#         all_messages = []
#         for interaction in self.interactions.order_by("created_at"):
#             all_messages.extend(interaction.messages())

#         return all_messages


# class LLMInteraction(models.Model):
#     class Meta:
#         ordering = ["created_at"]

#     thread = models.ForeignKey(
#         LLMThread,
#         on_delete=models.CASCADE,
#         related_name="interactions",
#         related_query_name="interaction",
#     )
#     initiator = models.ForeignKey(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name="llm_interactions",
#         related_query_name="llm_interaction",
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     messages_json = models.BinaryField()

#     def messages(self) -> list:
#         return ModelMessagesTypeAdapter.validate_json(self.messages_json)
