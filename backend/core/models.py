import uuid
from django.db import models
from django.contrib.auth.models import User

# ==============================================================================
#  1. Document Model
# ==============================================================================
class Document(models.Model):
    """
    Stores metadata for each user-uploaded file.\n
        id,
        user,
        filename,
        filepath,
        fileType,
        size,
        uploadDate,
        status (for async AI processing),
        version
    """

    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    # Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    filename = models.CharField(max_length=255)
    filepath = models.CharField(max_length=512)
    fileType = models.CharField(max_length=100)
    size = models.IntegerField()
    uploadDate = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    version = models.IntegerField(default=1)
    
    def __str__(self) -> str:
        user_info = self.user.username if self.user else "No User Assigned"
        return f"{self.filename} (User: {user_info})"
    
# ==============================================================================
#  2. GeneratedContent Model
# ==============================================================================
class GeneratedContent(models.Model):
    """
    Stores the associated content to each document.\n
        id,
        document,
        contentType,
        contentData,
        createdAt
    """
    
    # Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='generated_content')
    contentType = models.CharField(max_length=50)
    contentData = models.JSONField()
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contentType} for Document ID: {self.document.id}"

# ==============================================================================
#  3. Log Model
# ==============================================================================
class Log(models.Model):
    """
    Stores logs for error debugging and tracking events\n
        id,
        user,
        document,
        level,
        message,
        createdAt
    """
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARN', 'Warning'),
        ('ERROR', 'Error'),
    ]
    
    # Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] {self.createdAt}: {self.message}"