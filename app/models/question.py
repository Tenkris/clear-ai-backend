from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, ListAttribute, UTCDateTimeAttribute
from app.utils.config import Config
from datetime import datetime, timezone
import uuid

class QuestionModel(Model):
    class Meta:
        table_name = "questions_dev_clearai"
        region = Config.AWS_REGION_NAME
        
    question_id = UnicodeAttribute(hash_key=True)
    question_understanding = UnicodeAttribute()
    solving_strategy = UnicodeAttribute()
    solution_steps = ListAttribute(of=UnicodeAttribute)
    conversations = ListAttribute(of=UnicodeAttribute)
    image_s3 = UnicodeAttribute()
    created_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    updated_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'question_id': self.question_id,
            'question_understanding': self.question_understanding,
            'solving_strategy': self.solving_strategy,
            'solution_steps': self.solution_steps,
            'conversations': self.conversations,
            'image_s3': self.image_s3,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def generate_id(cls):
        """Generate a unique question ID."""
        return f"q_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
