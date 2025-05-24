from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, ListAttribute, UTCDateTimeAttribute , NumberAttribute
from app.utils.config import Config
from datetime import datetime, timezone

class UserModel(Model):
    class Meta:
        table_name = "users_dev_clearai"
        region = Config.AWS_REGION_NAME
        
    email = UnicodeAttribute(hash_key=True)
    password = UnicodeAttribute()
    role = UnicodeAttribute()
    age = NumberAttribute(null=True)
    created_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.email,
            'email': self.email,
            'role': self.role,
            'age': self.age,
            'created_at': self.created_at.isoformat()
        }
    
